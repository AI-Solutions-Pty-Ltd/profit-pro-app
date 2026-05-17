"""Backfill the new trade_code FK on labour/plant/prelim specs.

For every Labour/Plant/Preliminary specification (Project/Contractor/System)
that has a free-text ``trade_name`` but no ``trade_code`` link, find an
existing TradeCode in the same scope whose name matches (case-insensitive,
either ``trade_name`` or ``prefix+trade_name``). If none exists, create one
so no data is lost. Reverse is a no-op (the legacy ``trade_name`` column is
kept, so this migration is non-destructive and safe to unapply).
"""

from django.db import migrations

# (spec model, trade-code model, scope field on the spec or None for global)
PLAN = [
    ("SystemLabourSpecification", "SystemTradeCode", None),
    ("SystemPlantSpecification", "SystemTradeCode", None),
    ("SystemPreliminarySpecification", "SystemTradeCode", None),
    ("ContractorLabourSpecification", "ContractorTradeCode", "company"),
    ("ContractorPlantSpecification", "ContractorTradeCode", "company"),
    ("ContractorPreliminarySpecification", "ContractorTradeCode", "company"),
    ("ProjectLabourSpecification", "ProjectTradeCode", "project"),
    ("ProjectPlantSpecification", "ProjectTradeCode", "project"),
    ("ProjectPreliminarySpecification", "ProjectTradeCode", "project"),
]


def _unique_prefix(existing_prefixes, name):
    """Derive a prefix that is unique within the scope (<=20 chars)."""
    base = "".join(ch for ch in name if ch.isalnum())[:18].upper() or "TRADE"
    candidate = base
    n = 1
    while candidate in existing_prefixes:
        suffix = str(n)
        candidate = base[: 20 - len(suffix)] + suffix
        n += 1
    existing_prefixes.add(candidate)
    return candidate


def forwards(apps, schema_editor):
    for spec_name, tc_name, scope_field in PLAN:
        Spec = apps.get_model("estimator", spec_name)
        TradeCode = apps.get_model("estimator", tc_name)

        qs = Spec.objects.filter(trade_code__isnull=True).exclude(trade_name="")
        # Cache trade codes per scope: scope_key -> (lookup dict, prefixes set)
        cache = {}

        for spec in qs.iterator():
            name = (spec.trade_name or "").strip()
            if not name:
                continue
            scope_id = getattr(spec, f"{scope_field}_id") if scope_field else None

            if scope_id not in cache:
                tc_qs = TradeCode.objects.all()
                if scope_field:
                    tc_qs = tc_qs.filter(**{scope_field + "_id": scope_id})
                lookup = {}
                prefixes = set()
                for tc in tc_qs:
                    prefixes.add(tc.prefix)
                    lookup.setdefault((tc.trade_name or "").strip().lower(), tc)
                    lookup.setdefault(
                        f"{tc.prefix}{tc.trade_name}".strip().lower(), tc
                    )
                cache[scope_id] = (lookup, prefixes)

            lookup, prefixes = cache[scope_id]
            tc = lookup.get(name.lower())
            if tc is None:
                create_kwargs = {
                    "prefix": _unique_prefix(prefixes, name),
                    "trade_name": name[:100],
                }
                if scope_field:
                    create_kwargs[f"{scope_field}_id"] = scope_id
                tc = TradeCode.objects.create(**create_kwargs)
                lookup[name.lower()] = tc
                lookup[f"{tc.prefix}{tc.trade_name}".strip().lower()] = tc

            spec.trade_code = tc
            spec.save(update_fields=["trade_code"])


def backwards(apps, schema_editor):
    # Non-destructive: legacy trade_name is retained, so nothing to undo.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("estimator", "0024_contractorlabourspecification_trade_code_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
