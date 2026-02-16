from datetime import date
from decimal import Decimal

from django.db import migrations


def seed_default_vat_rates(apps, schema_editor):
    """Create default historical VAT rates."""
    Vat = apps.get_model("Ledger", "Vat")

    vat_periods = [
        {
            "name": "No VAT",
            "rate": Decimal("0.00"),
            "start_date": None,
            "end_date": None,
        },
        {
            "name": "VAT Exempt",
            "rate": Decimal("0.00"),
            "start_date": None,
            "end_date": None,
        },
        {
            "name": "VAT 10% (1991-09-30 to 1993-04-06)",
            "rate": Decimal("10.00"),
            "start_date": date(1991, 9, 30),
            "end_date": date(1993, 4, 6),
        },
        {
            "name": "VAT 14% (1993-04-07 to 2018-03-31)",
            "rate": Decimal("14.00"),
            "start_date": date(1993, 4, 7),
            "end_date": date(2018, 3, 31),
        },
        {
            "name": "VAT 15% (2018-04-01 to Current)",
            "rate": Decimal("15.00"),
            "start_date": date(2018, 4, 1),
            "end_date": None,
        },
    ]

    for vat_period in vat_periods:
        Vat.objects.update_or_create(
            name=vat_period["name"],
            rate=vat_period["rate"],
            start_date=vat_period["start_date"],
            end_date=vat_period["end_date"],
        )


def remove_default_vat_rates(apps, schema_editor):
    """Reverse seeded VAT rates."""
    Vat = apps.get_model("Ledger", "Vat")

    Vat.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("Ledger", "0002_alter_vat_end_date_alter_vat_start_date"),
    ]

    operations = [
        migrations.RunPython(seed_default_vat_rates, remove_default_vat_rates),
    ]
