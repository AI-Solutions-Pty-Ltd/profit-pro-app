from django.db import migrations, models

# Map spec name → preliminary_type for legacy data. Keys are case-insensitive.
NAME_TO_TYPE = {
    "fixed-contractual requirements": "fixed_contractual",
    "fixed contractual requirements": "fixed_contractual",
    "fixed-facilities required": "fixed_facilities",
    "fixed facilities": "fixed_facilities",
    "time-contractual requirements": "time_contractual",
    "time contractual requirements": "time_contractual",
    "time-facilities for contractor": "time_facilities",
    "time-facilities": "time_facilities",
    "time-small tools & accessories": "time_small_tools",
    "time-small tool allowances": "time_small_tools",
    "time-plant and equipment": "time_plant_equipment",
    "time-company and head office overheads": "time_company_overheads",
    "time-company & head office overheads": "time_company_overheads",
    "time-site personnel": "time_site_personnel",
}


def backfill_preliminary_type(apps, schema_editor):
    SystemPreliminarySpecification = apps.get_model(
        "estimator", "SystemPreliminarySpecification"
    )
    ProjectPreliminarySpecification = apps.get_model(
        "estimator", "ProjectPreliminarySpecification"
    )

    for model in (SystemPreliminarySpecification, ProjectPreliminarySpecification):
        for spec in model.objects.all():
            key = (spec.name or "").strip().lower()
            t = NAME_TO_TYPE.get(key)
            if t:
                spec.preliminary_type = t
                spec.save(update_fields=["preliminary_type"])


class Migration(migrations.Migration):
    dependencies = [
        ("estimator", "0012_remove_projectplantspecification_plant_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="systempreliminaryspecification",
            name="preliminary_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("fixed_contractual", "Fixed Contractual Requirements"),
                    ("fixed_facilities", "Fixed Facilities"),
                    ("time_contractual", "Time-Contractual Requirements"),
                    ("time_facilities", "Time-Facilities"),
                    ("time_small_tools", "Time-Small Tool Allowances"),
                    ("time_plant_equipment", "Time-Plant and Equipment"),
                    ("time_company_overheads", "Time-Company & Head Office Overheads"),
                    ("time_site_personnel", "Time-Site Personnel"),
                ],
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="projectpreliminaryspecification",
            name="preliminary_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("fixed_contractual", "Fixed Contractual Requirements"),
                    ("fixed_facilities", "Fixed Facilities"),
                    ("time_contractual", "Time-Contractual Requirements"),
                    ("time_facilities", "Time-Facilities"),
                    ("time_small_tools", "Time-Small Tool Allowances"),
                    ("time_plant_equipment", "Time-Plant and Equipment"),
                    ("time_company_overheads", "Time-Company & Head Office Overheads"),
                    ("time_site_personnel", "Time-Site Personnel"),
                ],
                max_length=30,
            ),
        ),
        migrations.RunPython(backfill_preliminary_type, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="systempreliminaryspecification",
            name="amount",
        ),
        migrations.RemoveField(
            model_name="projectpreliminaryspecification",
            name="amount",
        ),
    ]
