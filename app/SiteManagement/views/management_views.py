"""Views for Site Management."""

from django.urls import reverse_lazy
from django.views.generic import TemplateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role


class SiteManagementView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, TemplateView):
    """Site management logs and tracking view."""

    template_name = "site_management/site_management.html"
    model = Project
    project_slug = "pk"
    roles = [Role.ADMIN, Role.USER]

    def get_project(self) -> Project:
        """Get the project instance."""
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy("project:project-dashboard", kwargs={"pk": project.pk})
                ),
            ),
            BreadcrumbItem(title="Site Management", url=None),
        ]
