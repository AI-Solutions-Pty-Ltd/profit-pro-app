"""Alter BOQItem FK constraints to reference Project* models
instead of System* models."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("estimator", "0007_populate_project_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="boqitem",
            name="trade_code",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="boq_items",
                to="estimator.projecttradecode",
            ),
        ),
        migrations.AlterField(
            model_name="boqitem",
            name="specification",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="boq_items",
                to="estimator.projectspecification",
            ),
        ),
        migrations.AlterField(
            model_name="boqitem",
            name="labour_specification",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="boq_items",
                to="estimator.projectlabourspecification",
            ),
        ),
        migrations.AlterField(
            model_name="boqitem",
            name="material",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="boq_items",
                to="estimator.projectmaterial",
                help_text="Direct material for items that don't use a specification",
            ),
        ),
    ]
