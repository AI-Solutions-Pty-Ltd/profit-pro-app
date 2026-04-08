"""CRUD views for Bi-Weekly Quality Reports (with child tables)."""

from django.contrib import messages
from django.db import transaction
from django.forms import DateInput, inlineformset_factory
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import (
    BiWeeklyQualityReport,
    QualityActivityInspection,
    QualityMaterialDelivery,
    QualitySiteAudit,
    QualityWorkmanship,
)


class BiWeeklyQualityReportMixin(
    SubscriptionRequiredMixin, UserHasProjectRoleGenericMixin, BreadcrumbMixin
):
    model = BiWeeklyQualityReport
    required_tiers = [Subscription.SITE_MANAGEMENT]
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return BiWeeklyQualityReport.objects.filter(project=self.get_project())

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
            BreadcrumbItem(title="Bi-Weekly Quality", url=None),
        ]


class BiWeeklyQualityReportListView(BiWeeklyQualityReportMixin, ListView):
    template_name = "site_management/biweekly_quality/list.html"
    context_object_name = "reports"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


ActivityInspectionFormSet = inlineformset_factory(
    BiWeeklyQualityReport,
    QualityActivityInspection,
    fields=["activity_or_work_package", "approval_status", "remarks"],
    extra=1,
    can_delete=True,
)
MaterialDeliveryFormSet = inlineformset_factory(
    BiWeeklyQualityReport,
    QualityMaterialDelivery,
    fields=["date", "material", "quantity"],
    extra=1,
    can_delete=True,
)
WorkmanshipFormSet = inlineformset_factory(
    BiWeeklyQualityReport,
    QualityWorkmanship,
    fields=["activity", "is_compliant", "snag_defect", "snag_date"],
    extra=1,
    can_delete=True,
)
SiteAuditFormSet = inlineformset_factory(
    BiWeeklyQualityReport,
    QualitySiteAudit,
    fields=["date", "inspector", "audit_findings"],
    extra=1,
    can_delete=True,
)


class _BiWeeklyQualityReportBaseFormView(BiWeeklyQualityReportMixin):
    template_name = "site_management/biweekly_quality/form.html"
    fields = ["period_start", "period_end", "notes"]
    widgets = {
        "period_start": DateInput(attrs={"type": "date"}),
        "period_end": DateInput(attrs={"type": "date"}),
    }

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name, widget in self.widgets.items():
            form.fields[field_name].widget = widget
        return form

    def _get_formsets(self):
        return {
            "activity_formset": ActivityInspectionFormSet(
                self.request.POST or None, instance=self.object
            ),
            "materials_formset": MaterialDeliveryFormSet(
                self.request.POST or None, instance=self.object
            ),
            "workmanship_formset": WorkmanshipFormSet(
                self.request.POST or None, instance=self.object
            ),
            "audits_formset": SiteAuditFormSet(
                self.request.POST or None, instance=self.object
            ),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context.update(self._get_formsets())
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formsets = [
            context["activity_formset"],
            context["materials_formset"],
            context["workmanship_formset"],
            context["audits_formset"],
        ]
        if not all(fs.is_valid() for fs in formsets):
            return self.form_invalid(form)

        with transaction.atomic():
            response = super().form_valid(form)
            for fs in formsets:
                fs.instance = self.object
                fs.save()
        return response

    def get_success_url(self):
        return reverse_lazy(
            "site_management:biweekly-quality-list",
            kwargs={"project_pk": self.get_project().pk},
        )


class BiWeeklyQualityReportCreateView(_BiWeeklyQualityReportBaseFormView, CreateView):
    def form_valid(self, form):
        form.instance.project = self.get_project()
        form.instance.submitted_by = self.request.user  # type: ignore
        messages.success(self.request, "Bi-weekly quality report created.")
        return super().form_valid(form)


class BiWeeklyQualityReportUpdateView(_BiWeeklyQualityReportBaseFormView, UpdateView):
    def form_valid(self, form):
        messages.success(self.request, "Bi-weekly quality report updated.")
        return super().form_valid(form)


class BiWeeklyQualityReportDeleteView(BiWeeklyQualityReportMixin, DeleteView):
    template_name = "site_management/biweekly_quality/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Bi-weekly quality report deleted.")
        return reverse_lazy(
            "site_management:biweekly-quality-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

