"""Management command to seed default drawing types for existing projects."""

from django.core.management.base import BaseCommand

from app.Project.projects.projects_models import DrawingType, Project

_DEFAULT_DRAWING_TYPES = ["Tender", "Information", "Construction", "Shop"]


class Command(BaseCommand):
    """Seed default drawing types for all existing projects."""

    help = "Seed default drawing types for all projects that do not have them"

    def handle(self, *args, **options):
        """Execute the command."""
        projects = Project.objects.filter(deleted=False)
        created_count = 0
        for project in projects:
            for type_name in _DEFAULT_DRAWING_TYPES:
                _, created = DrawingType.objects.get_or_create(
                    project=project,
                    name=type_name,
                    defaults={"description": f"{type_name} drawing type"},
                )
                if created:
                    created_count += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_count} drawing type(s) for {projects.count()} project(s)."
            )
        )
