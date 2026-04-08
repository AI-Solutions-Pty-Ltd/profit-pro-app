"""CRUD views for Bi-Weekly Safety Reports."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import BiWeeklySafetyReport


class BiWeeklySafetyReportMixin(
    SubscriptionRequiredMixin, UserHasProjectRoleGenericMixin, BreadcrumbMixin
):
    model = BiWeeklySafetyReport
    required_tiers = [Subscription.SITE_MANAGEMENT]
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return BiWeeklySafetyReport.objects.filter(project=self.get_project())

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
            BreadcrumbItem(title="Bi-Weekly Safety", url=None),
        ]


class BiWeeklySafetyReportListView(BiWeeklySafetyReportMixin, ListView):
    template_name = "site_management/biweekly_safety/list.html"
    context_object_name = "reports"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class BiWeeklySafetyReportCreateView(BiWeeklySafetyReportMixin, CreateView):
    template_name = "site_management/biweekly_safety/form.html"
    fields = ["period_start", "period_end", "key_concerns", "notes"]
    widgets = {
        "period_start": DateInput(attrs={"type": "date"}),
        "period_end": DateInput(attrs={"type": "date"}),
    }

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name, widget in self.widgets.items():
            form.fields[field_name].widget = widget
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        form.instance.submitted_by = self.request.user  # type: ignore
        messages.success(self.request, "Bi-weekly safety report created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:biweekly-safety-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class BiWeeklySafetyReportUpdateView(BiWeeklySafetyReportMixin, UpdateView):
    template_name = "site_management/biweekly_safety/form.html"
    fields = ["period_start", "period_end", "key_concerns", "notes"]
    widgets = {
        "period_start": DateInput(attrs={"type": "date"}),
        "period_end": DateInput(attrs={"type": "date"}),
    }

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name, widget in self.widgets.items():
            form.fields[field_name].widget = widget
        return form

    def form_valid(self, form):
        messages.success(self.request, "Bi-weekly safety report updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:biweekly-safety-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class BiWeeklySafetyReportDeleteView(BiWeeklySafetyReportMixin, DeleteView):
    template_name = "site_management/biweekly_safety/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Bi-weekly safety report deleted.")
        return reverse_lazy(
            "site_management:biweekly-safety-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

