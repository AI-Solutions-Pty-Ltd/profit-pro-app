import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("estimator", "0010_systemplantcost_systempreliminarycost_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="boqitem",
            name="plant_specification",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="boq_items",
                to="estimator.projectplantspecification",
            ),
        ),
        migrations.AddField(
            model_name="boqitem",
            name="preliminary_specification",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="boq_items",
                to="estimator.projectpreliminaryspecification",
            ),
        ),
    ]
