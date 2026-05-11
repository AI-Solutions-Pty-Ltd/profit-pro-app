from django.db import migrations


def backfill_pack_from_market_rate(apps, schema_editor):
    """Existing rows have market_rate filled. Set pack_qty=1, pack_cost=market_rate
    so the effective unit rate (pack_cost / pack_qty) is unchanged.
    """
    for model_name in ("SystemMaterial", "ContractorMaterial", "ProjectMaterial"):
        Model = apps.get_model("estimator", model_name)
        for m in Model.objects.all():
            m.pack_qty = 1
            m.pack_cost = m.market_rate
            m.save(update_fields=["pack_qty", "pack_cost"])


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("estimator", "0019_contractormaterial_pack_cost_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_pack_from_market_rate, reverse_noop),
    ]
