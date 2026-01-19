"""Views for Milestone management (Time Forecast)."""

from typing import Any

from django.contrib import messages
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, UpdateView

from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import MilestoneForm
from app.Project.models import Milestone, Project


class MilestoneMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    """Mixin for Milestone views."""

    permissions = ["contractor"]
    model = Milestone
    form_class = MilestoneForm
    project: Project

    def get_project(self) -> Project:
        """Get the project for this view."""
        if hasattr(self, "project") and self.project:
            return self.project

        project_pk = self.kwargs.get("project_pk")
        try:
            self.project = Project.objects.get(pk=project_pk, users=self.request.user)
            return self.project
        except Project.DoesNotExist as err:
            raise Http404(
                "Project not found or you don't have permission to access it."
            ) from err

    def get_success_url(self) -> str:
        return reverse(
            "project:time-forecast", kwargs={"project_pk": self.get_project().pk}
        )

    def get_breadcrumbs(self) -> list[dict[str, str | None]]:
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
        ]


class MilestoneCreateView(MilestoneMixin, CreateView):
    """Create a new milestone for a project."""

    template_name = "forecasts/milestone_form.html"

    def get_breadcrumbs(self) -> list[dict[str, str | None]]:
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.append({"title": "Add Milestone", "url": None})
        return breadcrumbs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context.update(
            {
                "project": project,
                "action": "Add",
            }
        )
        return context

    def form_valid(self, form: MilestoneForm) -> HttpResponse:
        form.instance.project = self.get_project()
        messages.success(self.request, "Milestone created successfully.")
        return super().form_valid(form)


class MilestoneUpdateView(MilestoneMixin, UpdateView):
    """Update an existing milestone."""

    template_name = "forecasts/milestone_form.html"

    def get_object(self) -> Milestone:
        project = self.get_project()
        milestone_pk = self.kwargs.get("pk")
        try:
            return Milestone.objects.get(pk=milestone_pk, project=project)
        except Milestone.DoesNotExist as err:
            raise Http404("Milestone not found.") from err

    def get_breadcrumbs(self) -> list[dict[str, str | None]]:
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.append({"title": f"Edit: {self.get_object().name}", "url": None})
        return breadcrumbs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context.update(
            {
                "project": project,
                "action": "Edit",
            }
        )
        return context

    def form_valid(self, form: MilestoneForm) -> HttpResponse:
        messages.success(self.request, "Milestone updated successfully.")
        return super().form_valid(form)


class MilestoneDeleteView(MilestoneMixin, DeleteView):
    """Delete a milestone."""

    template_name = "forecasts/milestone_confirm_delete.html"

    def get_object(self) -> Milestone:
        project = self.get_project()
        milestone_pk = self.kwargs.get("pk")
        try:
            return Milestone.objects.get(pk=milestone_pk, project=project)
        except Milestone.DoesNotExist as err:
            raise Http404("Milestone not found.") from err

    def get_breadcrumbs(self) -> list[dict[str, str | None]]:
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs.append({"title": f"Delete: {self.get_object().name}", "url": None})
        return breadcrumbs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def form_valid(self, form: Any) -> HttpResponse:
        messages.success(self.request, "Milestone deleted successfully.")
        return super().form_valid(form)


class MilestoneCompleteView(MilestoneMixin, UpdateView):
    """Mark a milestone as complete."""

    http_method_names = ["post"]

    def get_object(self) -> Milestone:
        project = self.get_project()
        milestone_pk = self.kwargs.get("pk")
        try:
            return Milestone.objects.get(pk=milestone_pk, project=project)
        except Milestone.DoesNotExist as err:
            raise Http404("Milestone not found.") from err

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        from django.utils import timezone

        milestone = self.get_object()
        milestone.is_completed = True
        milestone.actual_date = timezone.now().date()
        milestone.save()
        messages.success(request, f"Milestone '{milestone.name}' marked as complete.")
        return redirect(self.get_success_url())
