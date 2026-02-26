"""CRUD views for Early Warning."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.Account.models import Account
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models.early_warning import EarlyWarning


class EarlyWarningMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Early Warning views."""

    model = EarlyWarning
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return EarlyWarning.objects.filter(project=self.get_project()).select_related(
            "submitted_by", "to_user"
        )


class EarlyWarningListView(EarlyWarningMixin, ListView):
    """List all early warnings for a project."""

    template_name = "site_management/early_warning/list.html"
    context_object_name = "early_warnings"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["open_count"] = self.get_queryset().filter(status="OPEN").count()
        context["closed_count"] = self.get_queryset().filter(status="CLOSED").count()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
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
            BreadcrumbItem(title="Early Warnings", url=None),
        ]


class EarlyWarningDetailView(EarlyWarningMixin, DetailView):
    """View details of an early warning."""

    template_name = "site_management/early_warning/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
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
            BreadcrumbItem(
                title="Early Warnings",
                url=str(
                    reverse_lazy(
                        "site_management:early-warning-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=self.get_object().reference_number, url=None),
        ]


class EarlyWarningCreateView(EarlyWarningMixin, CreateView):
    """Create a new early warning."""

    template_name = "site_management/early_warning/form.html"
    fields = [
        "to_user",
        "subject",
        "message",
        "impact_time",
        "impact_cost",
        "impact_quality",
        "respond_by_date",
        "attachment",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["respond_by_date"].widget = DateInput(attrs={"type": "date"})
        form.fields["to_user"].queryset = Account.objects.filter(
            project_roles__project=self.get_project()
        ).distinct()
        form.fields["to_user"].label = "To"
        form.fields["subject"].widget.attrs["placeholder"] = (
            "Brief subject of the early warning"
        )
        form.fields["message"].widget.attrs["placeholder"] = (
            "Detailed description of the potential issue or risk"
        )
        return form

    def form_valid(self, form):
        project = self.get_project()
        form.instance.project = project
        form.instance.submitted_by = self.request.user

        # Auto-set the submitter's role
        role = (
            project.project_roles.filter(user=self.request.user)
            .values_list("role", flat=True)
            .first()
        )
        form.instance.submitted_by_role = role or ""
        messages.success(self.request, "Early warning submitted successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:early-warning-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
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
            BreadcrumbItem(
                title="Early Warnings",
                url=str(
                    reverse_lazy(
                        "site_management:early-warning-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Create Early Warning", url=None),
        ]


class EarlyWarningUpdateView(EarlyWarningMixin, UpdateView):
    """Update an early warning (submitter edits / respondent responds)."""

    template_name = "site_management/early_warning/form.html"
    fields = [
        "to_user",
        "subject",
        "message",
        "impact_time",
        "impact_cost",
        "impact_quality",
        "respond_by_date",
        "attachment",
        "response",
        "response_attachment",
        "status",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["respond_by_date"].widget = DateInput(attrs={"type": "date"})
        form.fields["to_user"].queryset = Account.objects.filter(
            project_roles__project=self.get_project()
        ).distinct()
        form.fields["to_user"].label = "To"
        form.fields["subject"].widget.attrs["placeholder"] = (
            "Brief subject of the early warning"
        )
        form.fields["message"].widget.attrs["placeholder"] = (
            "Detailed description of the potential issue or risk"
        )
        form.fields["response"].widget.attrs["placeholder"] = (
            "Response to this early warning"
        )
        return form

    def form_valid(self, form):
        obj = form.save(commit=False)
        # Auto-set response date if a response was just added
        if obj.response and not obj.response_date:
            obj.response_date = timezone.now().date()
        # Auto-set date_closed if status changed to CLOSED
        if obj.status == "CLOSED" and not obj.date_closed:
            obj.date_closed = timezone.now().date()
        elif obj.status == "OPEN":
            obj.date_closed = None
        obj.save()
        messages.success(self.request, "Early warning updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:early-warning-detail",
            kwargs={"project_pk": self.get_project().pk, "pk": self.object.pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
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
            BreadcrumbItem(
                title="Early Warnings",
                url=str(
                    reverse_lazy(
                        "site_management:early-warning-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=self.get_object().reference_number, url=None),
        ]


class EarlyWarningDeleteView(EarlyWarningMixin, DeleteView):
    """Delete an early warning."""

    template_name = "site_management/early_warning/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Early warning deleted successfully.")
        return reverse_lazy(
            "site_management:early-warning-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
