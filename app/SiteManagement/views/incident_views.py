"""CRUD views for Incidents."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import Incident


class IncidentMixin(
    SubscriptionRequiredMixin, UserHasProjectRoleGenericMixin, BreadcrumbMixin
):
    """Mixin for Incident views."""

    model = Incident
    required_tiers = [Subscription.SITE_MANAGEMENT]
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return Incident.objects.filter(project=self.get_project())

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
            BreadcrumbItem(title="Incidents", url=None),
        ]


class IncidentListView(IncidentMixin, ListView):
    """List all Incidents."""

    template_name = "site_management/incident/list.html"
    context_object_name = "incidents"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class IncidentCreateView(IncidentMixin, CreateView):
    """Create a new Incident."""

    template_name = "site_management/incident/form.html"
    fields = [
        "incident_type",
        "date",
        "description",
        "location",
        "root_cause",
        "corrective_action",
        "corrective_action_date",
        "reported_by",
        "status",
    ]
    widgets = {
        "date": DateInput(attrs={"type": "date"}),
        "corrective_action_date": DateInput(attrs={"type": "date"}),
    }

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = self.widgets["date"]
        form.fields["corrective_action_date"].widget = self.widgets[
            "corrective_action_date"
        ]
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Incident created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:incident-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class IncidentUpdateView(IncidentMixin, UpdateView):
    """Update an Incident."""

    template_name = "site_management/incident/form.html"
    fields = [
        "incident_type",
        "date",
        "description",
        "location",
        "root_cause",
        "corrective_action",
        "corrective_action_date",
        "reported_by",
        "status",
    ]
    widgets = {
        "date": DateInput(attrs={"type": "date"}),
        "corrective_action_date": DateInput(attrs={"type": "date"}),
    }

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = self.widgets["date"]
        form.fields["corrective_action_date"].widget = self.widgets[
            "corrective_action_date"
        ]
        return form

    def form_valid(self, form):
        messages.success(self.request, "Incident updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:incident-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class IncidentDeleteView(IncidentMixin, DeleteView):
    """Delete an Incident."""

    template_name = "site_management/incident/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Incident deleted successfully!")
        return reverse_lazy(
            "site_management:incident-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
