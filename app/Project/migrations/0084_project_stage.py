import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Project", "0083_dailyplantusage_plant_type_productionplan_is_leaf_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectStage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, help_text="When this record was created"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, help_text="When this record was last modified"
                    ),
                ),
                (
                    "deleted",
                    models.BooleanField(default=False, help_text="Soft delete flag"),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Project stage name (e.g., Planning, Design, Construction)",
                        max_length=100,
                        unique=True,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, help_text="Optional description of the stage"
                    ),
                ),
            ],
            options={
                "verbose_name": "Project Stage",
                "verbose_name_plural": "Project Stages",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="project",
            name="project_stage",
            field=models.ForeignKey(
                blank=True,
                help_text="Project stage",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects",
                to="Project.projectstage",
            ),
        ),
    ]
