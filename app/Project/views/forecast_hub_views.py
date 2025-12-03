"""Views for the unified Forecasts hub with tabs."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Sum
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView

from app.BillOfQuantities.models.forecast_models import Forecast
from app.core.Utilities.dates import get_end_of_month
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Milestone, PlannedValue, Project


class ForecastHubMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    """Mixin for Forecast Hub views."""

    permissions = ["contractor"]
    project: Project

    def get_project(self) -> Project:
        """Get the project for this view."""
        if hasattr(self, "project") and self.project:
            return self.project

        project_pk = self.kwargs.get("project_pk")
        try:
            self.project = Project.objects.get(pk=project_pk, account=self.request.user)
            return self.project
        except Project.DoesNotExist as err:
            raise Http404(
                "Project not found or you don't have permission to access it."
            ) from err

    def get_breadcrumbs(self) -> list[dict[str, str | None]]:
        project = self.get_project()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-list")},
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {"title": "Forecasts", "url": None},
        ]


class ForecastHubView(ForecastHubMixin, TemplateView):
    """Main Forecasts hub view with tabs for different forecast types."""

    template_name = "forecasts/forecast_hub.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        active_tab = self.kwargs.get("tab", "cost")

        context.update(
            {
                "project": project,
                "active_tab": active_tab,
                "has_boq": project.line_items.exists(),
                "has_dates": bool(project.start_date and project.end_date),
            }
        )
        return context


class TimeForecastView(ForecastHubMixin, TemplateView):
    """Time Forecast tab - displays project milestones."""

    template_name = "forecasts/time_forecast.html"

    def get_breadcrumbs(self) -> list[dict[str, str | None]]:
        project = self.get_project()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-list")},
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
            {"title": "Time Forecast", "url": None},
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        milestones = Milestone.objects.filter(project=project).order_by(
            "sequence", "planned_date"
        )

        # Calculate summary stats
        total_milestones = milestones.count()
        completed = milestones.filter(is_completed=True).count()
        delayed = sum(1 for m in milestones if m.is_delayed)
        on_schedule = total_milestones - delayed - completed

        context.update(
            {
                "project": project,
                "active_tab": "time",
                "milestones": milestones,
                "total_milestones": total_milestones,
                "completed_milestones": completed,
                "delayed_milestones": delayed,
                "on_schedule_milestones": on_schedule,
            }
        )
        return context


class CashflowForecastView(ForecastHubMixin, TemplateView):
    """Cashflow Forecast tab - waterfall graph display."""

    template_name = "forecasts/cashflow_forecast.html"

    def get_breadcrumbs(self) -> list[dict[str, str | None]]:
        project = self.get_project()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-list")},
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
            {"title": "Cashflow Forecast", "url": None},
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()

        # Get planned values for cashflow chart
        planned_values = PlannedValue.objects.filter(project=project).order_by("period")

        # Prepare chart data
        chart_labels = []
        planned_data = []
        forecast_data = []
        cumulative_planned = []
        cumulative_forecast = []
        running_planned = Decimal("0")
        running_forecast = Decimal("0")

        for pv in planned_values:
            chart_labels.append(pv.period.strftime("%b %Y"))
            planned_data.append(float(pv.value or 0))
            forecast_data.append(float(pv.forecast_value or 0))

            running_planned += pv.value or Decimal("0")
            running_forecast += pv.forecast_value or Decimal("0")
            cumulative_planned.append(float(running_planned))
            cumulative_forecast.append(float(running_forecast))

        contract_value = float(project.get_total_contract_value)

        context.update(
            {
                "project": project,
                "active_tab": "cashflow",
                "has_dates": bool(project.start_date and project.end_date),
                "chart_labels": chart_labels,
                "planned_data": planned_data,
                "forecast_data": forecast_data,
                "cumulative_planned": cumulative_planned,
                "cumulative_forecast": cumulative_forecast,
                "contract_value": contract_value,
                "has_chart_data": bool(planned_values.exists()),
            }
        )
        return context


class EarnedValueView(ForecastHubMixin, TemplateView):
    """Earned Value Predictions tab - EVM metrics display."""

    template_name = "forecasts/earned_value.html"

    def get_breadcrumbs(self) -> list[dict[str, str | None]]:
        project = self.get_project()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-list")},
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
            {"title": "Earned Value Predictions", "url": None},
        ]

    def get_context_data(self: "EarnedValueView", **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()

        # Handle date selection from GET parameter or default to end of current month
        selected_date_str = self.request.GET.get("selected_date")
        if selected_date_str:
            try:
                selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
                # Don't allow future dates
                if selected_date > datetime.now().date():
                    selected_date = datetime.now().date()
            except ValueError:
                selected_date = datetime.now().date()
        else:
            selected_date = datetime.now().date()

        current_month = get_end_of_month(
            datetime.combine(selected_date, datetime.min.time())
        )

        # Get EVM data from project methods
        original_budget = project.get_original_contract_value
        revised_budget = project.get_total_contract_value

        # Get cumulative actual cost (total certified to date)

        # Get latest forecast total
        latest_forecast: Forecast | None = project.forecasts.filter(
            status=Forecast.Status.APPROVED, period__lte=current_month.date()
        ).first()
        forecast_cost = (
            latest_forecast.total_forecast if latest_forecast else Decimal("0")
        )

        # Get payment certificates used for actual cost calculation
        from app.BillOfQuantities.models.payment_certificate_models import (
            PaymentCertificate,
        )

        used_certificates = PaymentCertificate.objects.filter(
            project=project,
            status=PaymentCertificate.Status.APPROVED,
            approved_on__lte=current_month.date(),
        ).order_by("-approved_on")

        actual_cost = project.actual_cost(date=current_month)

        # Get planned value (cumulative)
        planned_values = project.planned_values.filter(period__lte=current_month.date())

        planned_value = sum_queryset(planned_values, "value")

        # Calculate actual % completion
        actual_percent = Decimal(0)
        if revised_budget > 0:
            actual_percent = round((actual_cost / revised_budget) * 100, 2)

        # Calculate Earned Value
        earned_value = Decimal(
            (original_budget * actual_percent / 100) if actual_percent > 0 else 0
        )

        # Calculate variances
        cost_variance = earned_value - actual_cost
        schedule_variance = earned_value - planned_value

        # Calculate performance indices
        cpi = project.cost_performance_index(date=current_month)
        spi = project.schedule_performance_index(date=current_month)

        # Calculate estimates
        eac = (
            round(original_budget / cpi, 2) if cpi and cpi > Decimal(0) else None
        )  # Estimate at Completion
        etc = round(eac - actual_cost, 2) if eac else None  # Estimate to Complete

        # TCPI - To Complete Performance Index
        tcpi = None
        if eac and eac != actual_cost:
            tcpi = round((original_budget - earned_value) / (eac - actual_cost), 2)

        # CPI interpretation
        cpi_interpretation = ""
        if cpi:
            if cpi < 1:
                cpi_interpretation = "Project has overrun the budget"
            elif cpi == 1:
                cpi_interpretation = "Project is on budget"
            else:
                cpi_interpretation = "Project is under budget"

        # SPI interpretation
        spi_interpretation = ""
        if spi:
            if spi < 1:
                spi_interpretation = "Project is behind schedule"
            elif spi == 1:
                spi_interpretation = "Project is on schedule"
            else:
                spi_interpretation = "Project is ahead of schedule"

        context.update(
            {
                "project": project,
                "active_tab": "earned_value",
                # Budget values
                "original_budget": original_budget,
                "revised_budget": revised_budget,
                "actual_cost": actual_cost,
                "forecast_cost": forecast_cost,
                "planned_value": planned_value,
                "actual_percent": actual_percent,
                "earned_value": earned_value,
                # Variances
                "cost_variance": cost_variance,
                "schedule_variance": schedule_variance,
                # Performance indices
                "cpi": cpi,
                "spi": spi,
                "cpi_interpretation": cpi_interpretation,
                "spi_interpretation": spi_interpretation,
                # Estimates
                "eac": eac,
                "etc": etc,
                "tcpi": tcpi,
                "current_month": current_month,
                "selected_date": selected_date.strftime("%Y-%m-%d"),
                # Source data used in calculations
                "latest_forecast": latest_forecast,
                "used_certificates": used_certificates,
            }
        )
        return context
