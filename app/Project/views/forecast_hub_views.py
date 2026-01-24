"""Views for the unified Forecasts hub with tabs."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView

from app.BillOfQuantities.models.forecast_models import Forecast
from app.core.Utilities.dates import get_end_of_month
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Milestone, PlannedValue, Project
from app.Project.models.project_roles import Role


class ForecastHubMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Forecast Hub views."""

    roles = [Role.FORECAST_HUB, Role.ADMIN, Role.USER]
    project: Project

    @property
    def project_slug(self):
        return "project_pk"

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

    def get_breadcrumbs(self) -> list[dict[str, str | None]]:
        project = self.get_project()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
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
        cumulative_work_completed = []
        running_planned = Decimal("0")
        running_forecast = Decimal("0")
        running_work_completed = Decimal("0")

        total_work_completed = Decimal("0")
        table_data = []
        for pv in planned_values:
            chart_labels.append(pv.period.strftime("%b %Y"))
            planned_data.append(float(pv.value or 0))
            forecast_data.append(float(pv.forecast_value or 0))

            running_planned += pv.value or Decimal("0")
            running_forecast += pv.forecast_value or Decimal("0")
            running_work_completed += pv.work_completed_percent or Decimal("0")
            total_work_completed += pv.work_completed_percent or Decimal("0")
            cumulative_planned.append(float(running_planned))
            cumulative_forecast.append(float(running_forecast))
            cumulative_work_completed.append(float(running_work_completed))

            # Calculate variance and percentages for table
            variance = running_planned - running_forecast
            variance_pct = (
                float((variance / running_planned) * 100) if running_planned > 0 else 0
            )
            table_data.append(
                {
                    "month": pv.period.strftime("%b %Y"),
                    "cumulative_planned": float(running_planned),
                    "cumulative_forecast": float(running_forecast),
                    "variance": float(variance),
                    "variance_pct": round(variance_pct, 1),
                    "work_completed_pct": round(float(running_work_completed), 1),
                }
            )

        contract_value = float(project.total_contract_value)

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
                "cumulative_work_completed": cumulative_work_completed,
                "contract_value": contract_value,
                "total_work_completed": total_work_completed,
                "work_completed_remaining": Decimal("100") - total_work_completed,
                "has_chart_data": bool(planned_values.exists()),
                "cashflow_table_data": table_data,
            }
        )
        return context


class EarnedValueView(ForecastHubMixin, TemplateView):
    """Earned Value Predictions tab - EVM metrics display."""

    template_name = "forecasts/earned_value.html"

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
                # # Don't allow future dates
                # if selected_date > datetime.now().date():
                #     selected_date = datetime.now().date()
            except ValueError:
                selected_date = datetime.now().date()
        else:
            selected_date = datetime.now().date()

        current_month = get_end_of_month(
            datetime.combine(selected_date, datetime.min.time())
        )

        # Get EVM data from project methods
        original_budget = project.original_contract_value
        revised_budget = project.total_contract_value

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

        # Get planned value (cumulative)
        planned_values = project.planned_values.filter(period__lte=current_month.date())

        planned_value = sum_queryset(planned_values, "value")

        # Calculate actual % completion
        actual_cost = project.get_actual_cost(date=current_month)
        actual_percent = project.get_actual_cost_percentage(current_month)

        # Calculate Earned Value
        earned_value = project.get_earned_value(current_month)

        # Calculate variances
        cost_variance = project.get_cost_variance(current_month)
        schedule_variance = project.get_schedule_variance(current_month)

        # Calculate performance indices
        cpi = project.get_cost_performance_index(date=current_month)
        spi = project.get_schedule_performance_index(date=current_month)

        # Calculate estimates
        eac = project.get_estimate_at_completion(current_month)
        etc = project.get_estimate_to_complete(current_month)

        # TCPI - To Complete Performance Index
        tcpi = project.get_to_complete_project_index(current_month)

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
