"""Migration to convert Project.account ForeignKey to Project.users ManyToManyField.

This migration preserves existing data by copying the account FK value to the new M2M field.
"""

from django.conf import settings
from django.db import migrations, models


def migrate_account_to_users(apps, schema_editor):
    """Copy existing account FK to new M2M users field."""
    Project = apps.get_model("Project", "Project")
    for project in Project.objects.all():
        if project.account_id:
            project.users.add(project.account_id)


def reverse_users_to_account(apps, schema_editor):
    """Reverse: set account from first user in M2M."""
    Project = apps.get_model("Project", "Project")
    for project in Project.objects.all():
        first_user = project.users.first()
        if first_user:
            project.account_id = first_user.id
            project.save()


class Migration(migrations.Migration):
    dependencies = [
        ("Project", "0022_add_risk_category_and_impact_model"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Add new M2M field (keeping old account field temporarily)
        migrations.AddField(
            model_name="project",
            name="users",
            field=models.ManyToManyField(
                help_text="Users who have access to this project",
                related_name="member_projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # 2. Run data migration to copy account -> users
        migrations.RunPython(migrate_account_to_users, reverse_users_to_account),
        # 3. Remove old account FK field
        migrations.RemoveField(
            model_name="project",
            name="account",
        ),
        # 4. Rename related_name from member_projects to projects
        migrations.AlterField(
            model_name="project",
            name="users",
            field=models.ManyToManyField(
                help_text="Users who have access to this project",
                related_name="projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
