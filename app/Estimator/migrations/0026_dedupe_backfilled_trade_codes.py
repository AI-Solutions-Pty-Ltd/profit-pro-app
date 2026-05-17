"""Merge duplicate trade codes created by the 0025 backfill.

0025 created a new trade code when a spec's legacy free-text trade value did
not match an existing code. Specs often stored the *abbreviation* (e.g.
"CFR") while the real trade code's prefix was "CFR-", so duplicates appeared
(real "Concrete, Formwork & Reinforcement" + junk "CFR"). This collapses
codes that share a normalised prefix back onto the real one and removes the
junk duplicates. Reverse is a no-op.
"""

from django.db import migrations


def _norm(s):
    return "".join(ch for ch in (s or "") if ch.isalnum()).upper()


# trade-code model, scope field, [spec models that FK to it]
PLAN = [
    (
        "ProjectTradeCode",
        "project_id",
        [
            "ProjectLabourSpecification",
            "ProjectPlantSpecification",
            "ProjectPreliminarySpecification",
        ],
    ),
    (
        "ContractorTradeCode",
        "company_id",
        [
            "ContractorLabourSpecification",
            "ContractorPlantSpecification",
            "ContractorPreliminarySpecification",
        ],
    ),
    (
        "SystemTradeCode",
        None,
        [
            "SystemLabourSpecification",
            "SystemPlantSpecification",
            "SystemPreliminarySpecification",
        ],
    ),
]


def forwards(apps, schema_editor):
    for tc_name, scope_field, spec_names in PLAN:
        TradeCode = apps.get_model("estimator", tc_name)
        spec_models = [apps.get_model("estimator", n) for n in spec_names]

        # group codes by (scope, normalised prefix)
        groups = {}
        for tc in TradeCode.objects.all():
            scope_val = getattr(tc, scope_field) if scope_field else None
            groups.setdefault((scope_val, _norm(tc.prefix)), []).append(tc)

        for (_scope, _pfx), codes in groups.items():
            if len(codes) < 2 or not _pfx:
                continue
            # canonical = a "descriptive" code (name differs from prefix),
            # preferring the lowest pk; else just the lowest pk.
            descriptive = [
                c for c in codes if _norm(c.prefix) != _norm(c.trade_name)
            ]
            canonical = min(descriptive or codes, key=lambda c: c.pk)

            for dup in codes:
                if dup.pk == canonical.pk:
                    continue
                for SpecModel in spec_models:
                    SpecModel.objects.filter(trade_code=dup).update(
                        trade_code=canonical,
                        trade_name=canonical.trade_name,
                    )
                # Junk backfill codes (prefix == name) were only ever
                # referenced by the three spec models — safe to remove.
                if _norm(dup.prefix) == _norm(dup.trade_name):
                    still_used = any(
                        SpecModel.objects.filter(trade_code=dup).exists()
                        for SpecModel in spec_models
                    )
                    if not still_used:
                        dup.delete()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("estimator", "0025_backfill_spec_trade_code"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
