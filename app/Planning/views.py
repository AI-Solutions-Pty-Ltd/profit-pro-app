"""Views for Planning & Procurement app."""

from typing import Any

from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Milestone, Project, Role
from app.Project.projects.category_forms import (
    CategoryForm,
    DisciplineForm,
    GroupForm,
    SubCategoryForm,
)

# =============================================================================
# Shared Mixin
# =============================================================================


class PlanningMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Base mixin for all Planning views."""

    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        """Get the project from the URL kwargs."""
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Default breadcrumbs for Planning views."""
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects",
                url=str(reverse_lazy("project:project-list")),
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management",
                        kwargs={"pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Planning & Procurement", url=None),
        ]


class ScopePlanningView(PlanningMixin, TemplateView):
    """Time Forecast tab - displays project milestones."""

    template_name = "planning/scope_planning.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {
                "title": "Setup",
                "url": reverse("project:project-setup", kwargs={"pk": project.pk}),
            },
            {"title": "Time Forecast", "url": None},
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        milestones = Milestone.objects.filter(project=project).order_by(
            "sequence", "planned_date"
        )

        # Build hierarchy using ORM
        # Get all categories for the project
        categories = project.categories.all().prefetch_related(
            "milestones",
            "subcategories__milestones",
            "subcategories__groups",
            "subcategories__groups__milestones",
        )

        # Handle uncategorized milestones
        uncategorized_milestones = milestones.filter(
            project_category__isnull=True, project_discipline__isnull=True
        )
        if uncategorized_milestones.exists():
            uncategorized_milestones = {
                "type": "uncategorized",
                "name": "Uncategorized",
                "object": None,
                "start_date": None,
                "end_date": None,
                "milestones": list(uncategorized_milestones),
            }

        context.update(
            {
                "project": project,
                "active_tab": "time",
                "categories": categories,
                "uncategorized_milestones": uncategorized_milestones,
                "category_form": CategoryForm(),
                "subcategory_form": SubCategoryForm(project=project),
                "group_form": GroupForm(project=project),
                "discipline_form": DisciplineForm(),
            }
        )
        return context


class BudgetPlanningView(ScopePlanningView):
    template_name = "planning/budget_forecast.html"
