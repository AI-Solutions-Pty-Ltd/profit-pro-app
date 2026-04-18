import os
import sys

import django

from app.Project.models.unit_models import UnitOfMeasure

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.local")
django.setup()


def seed_units():
    units = [
        # Length
        {"name": "Meter", "short_name": "m", "category": UnitOfMeasure.Category.LENGTH},
        {
            "name": "Kilometer",
            "short_name": "km",
            "category": UnitOfMeasure.Category.LENGTH,
        },
        {
            "name": "Millimeter",
            "short_name": "mm",
            "category": UnitOfMeasure.Category.LENGTH,
        },
        # Area
        {
            "name": "Square Meter",
            "short_name": "m2",
            "category": UnitOfMeasure.Category.AREA,
        },
        {
            "name": "Hectare",
            "short_name": "ha",
            "category": UnitOfMeasure.Category.AREA,
        },
        # Volume
        {
            "name": "Cubic Meter",
            "short_name": "m3",
            "category": UnitOfMeasure.Category.VOLUME,
        },
        {"name": "Liter", "short_name": "L", "category": UnitOfMeasure.Category.VOLUME},
        # Weight
        {
            "name": "Kilogram",
            "short_name": "kg",
            "category": UnitOfMeasure.Category.WEIGHT,
        },
        {"name": "Tonne", "short_name": "t", "category": UnitOfMeasure.Category.WEIGHT},
        {"name": "Gram", "short_name": "g", "category": UnitOfMeasure.Category.WEIGHT},
        # Time
        {"name": "Hour", "short_name": "hr", "category": UnitOfMeasure.Category.TIME},
        {"name": "Day", "short_name": "day", "category": UnitOfMeasure.Category.TIME},
        {"name": "Week", "short_name": "wk", "category": UnitOfMeasure.Category.TIME},
        {"name": "Month", "short_name": "mo", "category": UnitOfMeasure.Category.TIME},
        # Count
        {"name": "Each", "short_name": "ea", "category": UnitOfMeasure.Category.COUNT},
        {
            "name": "Number",
            "short_name": "no",
            "category": UnitOfMeasure.Category.COUNT,
        },
        {"name": "Set", "short_name": "set", "category": UnitOfMeasure.Category.COUNT},
    ]

    created_count = 0
    for unit_data in units:
        unit, created = UnitOfMeasure.objects.get_or_create(
            short_name=unit_data["short_name"],
            defaults={"name": unit_data["name"], "category": unit_data["category"]},
        )
        if created:
            created_count += 1
            print(f"Created unit: {unit.name} ({unit.short_name})")
        else:
            print(f"Unit already exists: {unit.name} ({unit.short_name})")

    print(f"\nSeeding complete. Created {created_count} units.")


if __name__ == "__main__":
    seed_units()
