"""Views for Risk Management."""

from decimal import Decimal

from django.contrib import messages
from django.db.models import QuerySet, Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.forms import RiskForm
from app.Project.models import Risk, Role


class RiskMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for risk views."""

    roles = [Role.USER]
    project_slug = "project_pk"

    def get_queryset(self) -> QuerySet[Risk]:
        """Filter risks by project."""
        project = self.get_project()
        return Risk.objects.filter(project=project).order_by("-created_at")


class RiskListView(RiskMixin, ListView):
    """List all risks for a project."""

    model = Risk
    template_name = "risk/risk_list.html"
    context_object_name = "risks"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(title="Risk Management", url=None),
        ]

    def get_queryset(self) -> QuerySet[Risk]:
        """Filter risks, optionally by active status."""
        qs = super().get_queryset()
        show_resolved = self.request.GET.get("show_resolved", "false") == "true"
        filter_current = self.request.GET.get("filter_current", "false") == "true"

        if not show_resolved:
            qs = qs.filter(is_active=True)

        if filter_current:
            today = timezone.now().date()
            qs = qs.filter(
                time_impact_start__lte=today,
                time_impact_end__gte=today,
            )

        return qs

    def get_context_data(self, **kwargs):
        """Add project and summary stats to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project
        context["show_resolved"] = (
            self.request.GET.get("show_resolved", "false") == "true"
        )
        context["filter_current"] = (
            self.request.GET.get("filter_current", "false") == "true"
        )

        # Calculate summary statistics
        active_risks = Risk.objects.filter(project=project, is_active=True)
        context["total_risks"] = active_risks.count()

        # Total estimated cost impact
        total_estimated_cost = Decimal("0.00")
        total_estimated_days = Decimal("0.00")
        for risk in active_risks:
            total_estimated_cost += risk.estimated_cost_impact
            if risk.estimated_time_impact_days:
                total_estimated_days += risk.estimated_time_impact_days

        context["total_estimated_cost_impact"] = total_estimated_cost
        context["total_estimated_time_impact"] = total_estimated_days

        # Raw totals
        context["total_cost_impact"] = active_risks.aggregate(total=Sum("cost_impact"))[
            "total"
        ] or Decimal("0.00")

        return context


class RiskCreateView(RiskMixin, CreateView):
    """Create a new risk."""

    model = Risk
    form_class = RiskForm
    template_name = "risk/risk_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Risk Management",
                url=reverse(
                    "project:risk-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Add Risk", url=None),
        ]

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def form_valid(self, form):
        """Set project and created_by before saving."""
        form.instance.project = self.get_project()
        form.instance.created_by = self.request.user
        messages.success(
            self.request,
            f"Risk '{form.instance.risk_name}' has been created successfully.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to the risk list."""
        return reverse_lazy(
            "project:risk-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class RiskUpdateView(RiskMixin, UpdateView):
    """Update an existing risk."""

    model = Risk
    form_class = RiskForm
    template_name = "risk/risk_form.html"

    def get_object(self, queryset=None) -> Risk:
        """Get risk and verify project ownership."""
        return get_object_or_404(
            Risk,
            pk=self.kwargs["pk"],
            project=self.get_project(),
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        risk = self.get_object()
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Risk Management",
                url=reverse(
                    "project:risk-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title=f"Edit: {risk.risk_name}", url=None),
        ]

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def form_valid(self, form):
        """Handle resolution status."""
        risk = form.instance
        # Check if risk is being resolved
        if not risk.is_active and not risk.resolved_date:
            risk.resolved_date = timezone.now().date()
            risk.resolved_by = self.request.user

        messages.success(
            self.request,
            f"Risk '{risk.risk_name}' has been updated successfully.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to the risk list."""
        return reverse_lazy(
            "project:risk-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class RiskDeleteView(RiskMixin, DeleteView):
    """Delete a risk."""

    model = Risk
    template_name = "risk/risk_confirm_delete.html"

    def get_object(self, queryset=None) -> Risk:
        """Get risk and verify project ownership."""
        return get_object_or_404(
            Risk,
            pk=self.kwargs["pk"],
            project=self.get_project(),
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        risk = self.get_object()
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Risk Management",
                url=reverse(
                    "project:risk-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title=f"Delete: {risk.risk_name}", url=None),
        ]

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def form_valid(self, form):
        """Soft delete the risk."""
        risk = self.get_object()
        risk.soft_delete()
        messages.success(
            self.request, f"Risk '{risk.risk_name}' has been deleted successfully."
        )
        return self.get_success_url()

    def get_success_url(self):
        """Redirect to the risk list."""
        from django.shortcuts import redirect

        return redirect(
            str(
                reverse_lazy(
                    "project:risk-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                )
            )
        )
