"""Views for Milestone management (Time Forecast)."""

from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.forms import MilestoneForm
from app.Project.models import Milestone, Role


class MilestoneDetailView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, DetailView):
    """View a single milestone."""

    model = Milestone
    template_name = "forecasts/milestone_detail.html"
    context_object_name = "milestone"
    roles = [Role.USER]
    project_slug = "project_pk"

    def get_queryset(self):
        """Filter milestones by project."""
        return Milestone.objects.filter(project=self.get_project())

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        milestone = self.get_object()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {
                "title": "Forecasts",
                "url": reverse(
                    "project:forecast-hub", kwargs={"project_pk": project.pk}
                ),
            },
            {
                "title": "Time Forecast",
                "url": reverse(
                    "project:time-forecast", kwargs={"project_pk": project.pk}
                ),
            },
            {"title": milestone.name, "url": None},
        ]


class MilestoneCreateView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, CreateView):
    """Create a new milestone for a project."""

    model = Milestone
    form_class = MilestoneForm
    template_name = "forecasts/milestone_form.html"
    roles = [Role.USER]
    project_slug = "project_pk"

    def form_valid(self, form: MilestoneForm) -> HttpResponse:
        form.instance.project = self.get_project()
        messages.success(self.request, "Milestone created successfully.")
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project:time-forecast", kwargs={"project_pk": self.get_project().pk}
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "project": self.get_project(),
                "action": "Add",
            }
        )
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {
                "title": "Forecasts",
                "url": reverse(
                    "project:forecast-hub", kwargs={"project_pk": project.pk}
                ),
            },
            {
                "title": "Time Forecast",
                "url": reverse(
                    "project:time-forecast", kwargs={"project_pk": project.pk}
                ),
            },
            {"title": "Add Milestone", "url": None},
        ]


class MilestoneUpdateView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, UpdateView):
    """Update an existing milestone."""

    model = Milestone
    form_class = MilestoneForm
    template_name = "forecasts/milestone_form.html"
    roles = [Role.USER]
    project_slug = "project_pk"

    def get_queryset(self):
        """Filter milestones by project."""
        return Milestone.objects.filter(project=self.get_project())

    def form_valid(self, form: MilestoneForm) -> HttpResponse:
        messages.success(self.request, "Milestone updated successfully.")
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project:time-forecast", kwargs={"project_pk": self.get_project().pk}
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "project": self.get_project(),
                "action": "Edit",
            }
        )
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        milestone = self.get_object()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {
                "title": "Forecasts",
                "url": reverse(
                    "project:forecast-hub", kwargs={"project_pk": project.pk}
                ),
            },
            {
                "title": "Time Forecast",
                "url": reverse(
                    "project:time-forecast", kwargs={"project_pk": project.pk}
                ),
            },
            {"title": f"Edit: {milestone.name}", "url": None},
        ]


class MilestoneDeleteView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, DeleteView):
    """Delete a milestone."""

    model = Milestone
    template_name = "forecasts/milestone_confirm_delete.html"
    context_object_name = "milestone"
    roles = [Role.USER]
    project_slug = "project_pk"

    def get_queryset(self):
        """Filter milestones by project."""
        return Milestone.objects.filter(project=self.get_project())

    def form_valid(self, form: Any) -> HttpResponse:
        messages.success(self.request, "Milestone deleted successfully.")
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project:time-forecast", kwargs={"project_pk": self.get_project().pk}
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        milestone = self.get_object()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {
                "title": "Forecasts",
                "url": reverse(
                    "project:forecast-hub", kwargs={"project_pk": project.pk}
                ),
            },
            {
                "title": "Time Forecast",
                "url": reverse(
                    "project:time-forecast", kwargs={"project_pk": project.pk}
                ),
            },
            {"title": f"Delete: {milestone.name}", "url": None},
        ]


class MilestoneCompleteView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, UpdateView
):
    """Mark a milestone as complete."""

    model = Milestone
    http_method_names = ["post"]
    roles = [Role.USER]
    project_slug = "project_pk"

    def get_queryset(self):
        """Filter milestones by project."""
        return Milestone.objects.filter(project=self.get_project())

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        from django.utils import timezone

        milestone = self.get_object()
        milestone.is_completed = True
        milestone.actual_date = timezone.now().date()
        milestone.save()
        messages.success(request, f"Milestone '{milestone.name}' marked as complete.")
        return redirect(
            reverse(
                "project:time-forecast", kwargs={"project_pk": self.get_project().pk}
            )
        )
