"""CRUD views for Safety Observation."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import SafetyObservation


class SafetyObservationMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Safety Observation views."""

    model = SafetyObservation
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return SafetyObservation.objects.filter(project=self.get_project())

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
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
            BreadcrumbItem(
                title="Site Management",
                url=str(
                    reverse_lazy(
                        "site_management:site-management",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Safety Observations", url=None),
        ]


class SafetyObservationListView(SafetyObservationMixin, ListView):
    """List all safety observations."""

    template_name = "site_management/safety_observation/list.html"
    context_object_name = "safety_observations"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SafetyObservationCreateView(SafetyObservationMixin, CreateView):
    """Create a new safety observation."""

    template_name = "site_management/safety_observation/form.html"
    fields = [
        "date",
        "observation",
        "location",
        "raised_by",
        "category",
        "corrective_action",
        "closed_out",
        "remarks",
    ]
    widgets = {"date": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = self.widgets["date"]
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Safety observation created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:safety-observation-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SafetyObservationUpdateView(SafetyObservationMixin, UpdateView):
    """Update a safety observation."""

    template_name = "site_management/safety_observation/form.html"
    fields = [
        "date",
        "observation",
        "location",
        "raised_by",
        "category",
        "corrective_action",
        "closed_out",
        "remarks",
    ]
    widgets = {"date": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = self.widgets["date"]
        return form

    def form_valid(self, form):
        messages.success(self.request, "Safety observation updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:safety-observation-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SafetyObservationDeleteView(SafetyObservationMixin, DeleteView):
    """Delete a safety observation."""

    template_name = "site_management/safety_observation/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Safety observation deleted successfully!")
        return reverse_lazy(
            "site_management:safety-observation-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
