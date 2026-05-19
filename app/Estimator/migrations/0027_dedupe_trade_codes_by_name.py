"""Second-pass trade-code dedupe — merge by trade *name*.

0026 only merged codes that shared a normalised prefix. But the 0025
backfill created junk codes whose prefix is the uppercased trade name
(e.g. prefix "MASONRY", name "Masonry -") because the spec's legacy
free-text trade was the descriptive name, not the abbreviation. Those do
not collide with the real code (prefix "MAN-", name "Masonry") on prefix,
so they survived as visible duplicates in the dropdowns.

This merges every "junk" code (prefix == name, ignoring punctuation) into
the matching real code by comparing normalised trade *names* (treating
"&" and "and" as equivalent, ignoring trailing punctuation). Junk with no
real match is left untouched (it is a genuine extra trade, not a dup).
Reverse is a no-op.
"""

from django.db import migrations


def _alnum(s):
    return "".join(ch for ch in (s or "") if ch.isalnum()).upper()


def _nname(s):
    """Normalised trade name: '&' -> 'and', alphanumerics only, upper."""
    return _alnum((s or "").replace("&", " and ").lower())


PLAN = [
    (
        "ProjectTradeCode",
        "project_id",
        [
            "ProjectLabourSpecification",
            "ProjectPlantSpecification",
            "ProjectPreliminarySpecification",
            "ProjectSpecification",
        ],
    ),
    (
        "ContractorTradeCode",
        "company_id",
        [
            "ContractorLabourSpecification",
            "ContractorPlantSpecification",
            "ContractorPreliminarySpecification",
            "ContractorSpecification",
        ],
    ),
    (
        "SystemTradeCode",
        None,
        [
            "SystemLabourSpecification",
            "SystemPlantSpecification",
            "SystemPreliminarySpecification",
            "SystemSpecification",
        ],
    ),
]


def forwards(apps, schema_editor):
    for tc_name, scope_field, spec_names in PLAN:
        TradeCode = apps.get_model("estimator", tc_name)
        spec_models = [apps.get_model("estimator", n) for n in spec_names]

        by_scope = {}
        for tc in TradeCode.objects.all():
            sv = getattr(tc, scope_field) if scope_field else None
            by_scope.setdefault(sv, []).append(tc)

        for _scope, codes in by_scope.items():
            reals = [c for c in codes if _alnum(c.prefix) != _alnum(c.trade_name)]
            junks = [c for c in codes if _alnum(c.prefix) == _alnum(c.trade_name)]
            if not reals or not junks:
                continue

            # name -> real code
            real_by_name = {}
            for r in reals:
                for key in (_nname(r.trade_name), _nname(r.prefix)):
                    if key:
                        real_by_name.setdefault(key, r)

            for j in junks:
                target = real_by_name.get(_nname(j.trade_name)) or real_by_name.get(
                    _nname(j.prefix)
                )
                if target is None or target.pk == j.pk:
                    continue
                for SpecModel in spec_models:
                    field_names = {f.name for f in SpecModel._meta.get_fields()}
                    upd = {"trade_code": target}
                    # Material specs have no legacy trade_name column.
                    if "trade_name" in field_names:
                        upd["trade_name"] = target.trade_name
                    SpecModel.objects.filter(trade_code=j).update(**upd)
                still_used = any(
                    SpecModel.objects.filter(trade_code=j).exists()
                    for SpecModel in spec_models
                )
                if not still_used:
                    j.delete()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("estimator", "0026_dedupe_backfilled_trade_codes"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
