"""Views for Planning & Procurement app."""

from typing import Any

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, TemplateView
from rest_framework.views import APIView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Planning.forms import (
    CategoryFileForm,
    DisciplineFileForm,
    GroupFileForm,
    SubCategoryFileForm,
)
from app.Planning.models import (
    CategoryFile,
    DisciplineFile,
    GroupFile,
    SubCategoryFile,
)
from app.Project.models import (
    Category,
    Discipline,
    Group,
    Milestone,
    Project,
    Role,
    SubCategory,
)
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
            {"title": "Scope Planning", "url": None},
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
            "files",
            "subcategories__milestones",
            "subcategories__files",
            "subcategories__groups",
            "subcategories__groups__milestones",
            "subcategories__groups__files",
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
    
    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {"title": "Cost Planning", "url": None},
        ]


# =============================================================================
# Scope Planning File Upload Views
# =============================================================================


class ScopeFileUploadMixin(PlanningMixin, CreateView):
    """Base mixin for scope file upload views."""

    template_name = "planning/scope/upload_form.html"

    def get_success_url(self):
        return reverse_lazy(
            "planning:scope-planning",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class CategoryFileUploadView(ScopeFileUploadMixin):
    """Upload a file to a Category (L1)."""

    model = CategoryFile
    form_class = CategoryFileForm

    def form_valid(self, form):
        form.instance.category = get_object_or_404(
            Category, pk=self.kwargs["pk"], project=self.get_project()
        )
        messages.success(self.request, "File uploaded successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item"] = get_object_or_404(
            Category, pk=self.kwargs["pk"], project=self.get_project()
        )
        context["level"] = "L1 - Category"
        return context


class SubCategoryFileUploadView(ScopeFileUploadMixin):
    """Upload a file to a SubCategory (L2)."""

    model = SubCategoryFile
    form_class = SubCategoryFileForm

    def form_valid(self, form):
        form.instance.sub_category = get_object_or_404(
            SubCategory, pk=self.kwargs["pk"], project=self.get_project()
        )
        messages.success(self.request, "File uploaded successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item"] = get_object_or_404(
            SubCategory, pk=self.kwargs["pk"], project=self.get_project()
        )
        context["level"] = "L2 - SubCategory"
        return context


class GroupFileUploadView(ScopeFileUploadMixin):
    """Upload a file to a Group (L3)."""

    model = GroupFile
    form_class = GroupFileForm

    def form_valid(self, form):
        form.instance.group = get_object_or_404(
            Group, pk=self.kwargs["pk"], project=self.get_project()
        )
        messages.success(self.request, "File uploaded successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item"] = get_object_or_404(
            Group, pk=self.kwargs["pk"], project=self.get_project()
        )
        context["level"] = "L3 - Group"
        return context


class DisciplineFileUploadView(ScopeFileUploadMixin):
    """Upload a file to a Discipline (L4)."""

    model = DisciplineFile
    form_class = DisciplineFileForm

    def form_valid(self, form):
        form.instance.discipline = get_object_or_404(
            Discipline, pk=self.kwargs["pk"], project=self.get_project()
        )
        messages.success(self.request, "File uploaded successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item"] = get_object_or_404(
            Discipline, pk=self.kwargs["pk"], project=self.get_project()
        )
        context["level"] = "L4 - Discipline"
        return context


# =============================================================================
# Scope Planning File Delete Views
# =============================================================================


class ScopeFileDeleteMixin(PlanningMixin, APIView):
    """Base mixin for scope file delete views."""

    pass


class CategoryFileDeleteView(ScopeFileDeleteMixin):
    """Delete a Category file."""

    def delete(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(
            CategoryFile, pk=pk, category__project=self.get_project()
        )
        obj.delete()
        messages.success(request, "File deleted successfully.")
        return JsonResponse({"success": True})


class SubCategoryFileDeleteView(ScopeFileDeleteMixin):
    """Delete a SubCategory file."""

    def delete(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(
            SubCategoryFile, pk=pk, sub_category__project=self.get_project()
        )
        obj.delete()
        messages.success(request, "File deleted successfully.")
        return JsonResponse({"success": True})


class GroupFileDeleteView(ScopeFileDeleteMixin):
    """Delete a Group file."""

    def delete(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(GroupFile, pk=pk, group__project=self.get_project())
        obj.delete()
        messages.success(request, "File deleted successfully.")
        return JsonResponse({"success": True})


class DisciplineFileDeleteView(ScopeFileDeleteMixin):
    """Delete a Discipline file."""

    def delete(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(
            DisciplineFile, pk=pk, discipline__project=self.get_project()
        )
        obj.delete()
        messages.success(request, "File deleted successfully.")
        return JsonResponse({"success": True})
