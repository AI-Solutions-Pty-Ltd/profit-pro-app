"""Management command to seed default disciplines for existing projects."""

from django.core.management.base import BaseCommand

from app.Project.projects.projects_models import Discipline, Project

_DEFAULT_DISCIPLINES = [
    "Project management",
    "Quantity Surveying",
    "Structural",
    "Electrical",
    "Mechanical",
    "Civil",
    "Piping",
    "Control & Instrumentation",
    "Geotech",
    "Town Planning",
    "Health and Safety",
    "Land Surveying",
    "Architectural",
]


class Command(BaseCommand):
    """Seed default disciplines for all existing projects."""

    help = "Seed default disciplines for all projects that do not have them"

    def handle(self, *args, **options):
        """Execute the command."""
        projects = Project.objects.filter(deleted=False)
        created_count = 0
        for project in projects:
            for name in _DEFAULT_DISCIPLINES:
                _, created = Discipline.objects.get_or_create(
                    project=project,
                    name=name,
                    defaults={"description": f"{name} discipline"},
                )
                if created:
                    created_count += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_count} discipline(s) for {projects.count()} project(s)."
            )
        )
