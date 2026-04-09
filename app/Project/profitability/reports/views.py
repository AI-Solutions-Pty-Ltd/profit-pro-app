from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import F, Sum
from django.http import JsonResponse
from django.views.generic import TemplateView

from app.BillOfQuantities.models import (
    ActualTransaction,
    BaselineCashflow,
    CashflowForecast,
    PaymentCertificate,
)
from app.Project.models import (
    JournalEntry,
    LabourCostTracker,
    MaterialCostTracker,
    OverheadCostTracker,
    PlannedValue,
    PlantCostTracker,
    SubcontractorCostTracker,
)
from app.Project.profitability.views import ProfitabilityMixin


class FinancialBaseView(ProfitabilityMixin, TemplateView):
    """
    Base view containing shared logic for financial performance reporting.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.project
        request = self.request

        # Date range for report (Project Start to End of Previous Month)
        today = date.today()
        
        # Defaults
        default_end_date = today.replace(day=1) - timedelta(days=1)
        default_start_date = (
            project.start_date if project.start_date else date(today.year, 1, 1)
        )

        # Handle Query Parameters (from filters)
        start_date_param = request.GET.get("start_date")
        end_date_param = request.GET.get("end_date")

        try:
            start_date = date.fromisoformat(start_date_param) if start_date_param else default_start_date
        except (ValueError, TypeError):
            start_date = default_start_date

        try:
            end_date = date.fromisoformat(end_date_param) if end_date_param else default_end_date
        except (ValueError, TypeError):
            end_date = default_end_date

        # Get financial metrics --- ACTUAL LOGIC ---
        context["start_date"] = start_date
        context["end_date"] = end_date
        context["financial_table"] = self.get_financial_table_data(start_date, end_date)
        context["baseline_assumptions"] = self.get_baseline_assumptions()
        context["variance_analysis"] = self.get_variance_analysis(
            context["financial_table"]
        )

        return context

    def get_baseline_assumptions(self):
        """Hardcoded baseline assumptions."""
        return {
            "cost_of_sales_percent": 60.0,
            "operating_expenses_percent": 12.0,
            "net_profit_percent": 28.0,
        }

    def get_financial_table_data(self, start_date, end_date):
        """Calculate values for the financial performance table."""
        project = self.project

        # --- REVENUE ---
        actual_revenue_to_date = project.total_certified_to_date

        this_month_start = date.today().replace(day=1)
        actual_revenue_this_month = ActualTransaction.objects.filter(
            line_item__project=project,
            payment_certificate__status=PaymentCertificate.Status.APPROVED,
            payment_certificate__approved_on__gte=this_month_start,
        ).aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")

        planned_revenue_to_date = BaselineCashflow.objects.filter(
            project=project,
            status=BaselineCashflow.Status.APPROVED,
            period__lte=end_date,
        ).aggregate(total=Sum("planned_value"))["total"] or Decimal("0.00")

        forecast_revenue = CashflowForecast.objects.filter(
            project=project,
            status=CashflowForecast.Status.APPROVED,
        ).aggregate(total=Sum("forecast_value"))["total"] or Decimal("0.00")

        # --- COST OF SALES (COGS) ---
        material_actual = (
            MaterialCostTracker.objects.filter(
                project=project, date__lte=end_date
            ).aggregate(total=Sum(F("quantity") * F("rate")))["total"]
            or 0
        )
        labour_actual = (
            LabourCostTracker.objects.filter(
                project=project, date__lte=end_date
            ).aggregate(total=Sum(F("amount_of_days") * F("salary")))["total"]
            or 0
        )
        subcon_actual = (
            SubcontractorCostTracker.objects.filter(
                project=project, date__lte=end_date
            ).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"]
            or 0
        )
        plant_actual = (
            PlantCostTracker.objects.filter(
                project=project, date__lte=end_date
            ).aggregate(total=Sum(F("usage_hours") * F("hourly_rate")))["total"]
            or 0
        )

        actual_cogs_to_date = (
            Decimal(material_actual)
            + Decimal(labour_actual)
            + Decimal(subcon_actual)
            + Decimal(plant_actual)
        )

        material_month = (
            MaterialCostTracker.objects.filter(
                project=project, date__gte=this_month_start
            ).aggregate(total=Sum(F("quantity") * F("rate")))["total"]
            or 0
        )
        labour_month = (
            LabourCostTracker.objects.filter(
                project=project, date__gte=this_month_start
            ).aggregate(total=Sum(F("amount_of_days") * F("salary")))["total"]
            or 0
        )
        subcon_month = (
            SubcontractorCostTracker.objects.filter(
                project=project, date__gte=this_month_start
            ).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"]
            or 0
        )
        plant_month = (
            PlantCostTracker.objects.filter(
                project=project, date__gte=this_month_start
            ).aggregate(total=Sum(F("usage_hours") * F("hourly_rate")))["total"]
            or 0
        )

        actual_cogs_this_month = (
            Decimal(material_month)
            + Decimal(labour_month)
            + Decimal(subcon_month)
            + Decimal(plant_month)
        )

        planned_cogs_to_date = planned_revenue_to_date * Decimal("0.60")

        # --- OPERATING EXPENSES (OPEX) ---
        overhead_tracker_actual = (
            OverheadCostTracker.objects.filter(
                project=project, date__lte=end_date
            ).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"]
            or 0
        )
        journal_overhead_actual = (
            JournalEntry.objects.filter(
                project=project,
                category=JournalEntry.Category.OVERHEAD,
                date__lte=end_date,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        actual_opex_to_date = Decimal(overhead_tracker_actual) + Decimal(
            journal_overhead_actual
        )

        overhead_tracker_month = (
            OverheadCostTracker.objects.filter(
                project=project, date__gte=this_month_start
            ).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"]
            or 0
        )
        journal_overhead_month = (
            JournalEntry.objects.filter(
                project=project,
                category=JournalEntry.Category.OVERHEAD,
                date__gte=this_month_start,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        actual_opex_this_month = Decimal(overhead_tracker_month) + Decimal(
            journal_overhead_month
        )

        planned_opex_to_date = planned_revenue_to_date * Decimal("0.12")

        # --- CALCULATIONS ---
        actual_gp_to_date = actual_revenue_to_date - actual_cogs_to_date
        planned_gp_to_date = planned_revenue_to_date - planned_cogs_to_date
        actual_gp_this_month = actual_revenue_this_month - actual_cogs_this_month

        actual_np_to_date = actual_gp_to_date - actual_opex_to_date
        planned_np_to_date = planned_gp_to_date - planned_opex_to_date
        actual_np_this_month = actual_gp_this_month - actual_opex_this_month

        gp_margin_actual = (
            (actual_gp_to_date / actual_revenue_to_date * 100)
            if actual_revenue_to_date > 0
            else 0
        )
        gp_margin_planned = (
            (planned_gp_to_date / planned_revenue_to_date * 100)
            if planned_revenue_to_date > 0
            else 0
        )

        np_margin_actual = (
            (actual_np_to_date / actual_revenue_to_date * 100)
            if actual_revenue_to_date > 0
            else 0
        )
        np_margin_planned = (
            (planned_np_to_date / planned_revenue_to_date * 100)
            if planned_revenue_to_date > 0
            else 0
        )

        return {
            "revenue": {
                "actual_to_date": actual_revenue_to_date,
                "planned_to_date": planned_revenue_to_date,
                "actual_this_month": actual_revenue_this_month,
                "forecast": forecast_revenue,
            },
            "cost_of_sales": {
                "actual_to_date": actual_cogs_to_date,
                "planned_to_date": planned_cogs_to_date,
                "actual_this_month": actual_cogs_this_month,
                "forecast": forecast_revenue * Decimal("0.60"),
            },
            "gross_profit": {
                "actual_to_date": actual_gp_to_date,
                "planned_to_date": planned_gp_to_date,
                "actual_this_month": actual_gp_this_month,
                "forecast": forecast_revenue * Decimal("0.40"),
            },
            "operating_expenses": {
                "actual_to_date": actual_opex_to_date,
                "planned_to_date": planned_opex_to_date,
                "actual_this_month": actual_opex_this_month,
                "forecast": forecast_revenue * Decimal("0.12"),
            },
            "net_profit": {
                "actual_to_date": actual_np_to_date,
                "planned_to_date": planned_np_to_date,
                "actual_this_month": actual_np_this_month,
                "forecast": forecast_revenue * Decimal("0.28"),
            },
            "gp_margin": {
                "actual_to_date": gp_margin_actual,
                "planned_to_date": gp_margin_planned,
                "actual_this_month": (
                    actual_gp_this_month / actual_revenue_this_month * 100
                )
                if actual_revenue_this_month > 0
                else 0,
                "forecast": 40.0,
            },
            "np_margin": {
                "actual_to_date": np_margin_actual,
                "planned_to_date": np_margin_planned,
                "actual_this_month": (
                    actual_np_this_month / actual_revenue_this_month * 100
                )
                if actual_revenue_this_month > 0
                else 0,
                "forecast": 28.0,
            },
        }

    def get_variance_analysis(self, table_data):
        """Prepare variance data for display."""
        metrics = [
            "revenue",
            "cost_of_sales",
            "gross_profit",
            "operating_expenses",
            "net_profit",
        ]
        variance_results = []

        for metric in metrics:
            actual = table_data[metric]["actual_to_date"]
            planned = table_data[metric]["planned_to_date"]
            variance = actual - planned
            variance_pct = (variance / planned * 100) if planned != 0 else 0

            status = "On Track"
            if metric in ["cost_of_sales", "operating_expenses"]:
                if variance_pct > 10:
                    status = "Critical"
                elif variance_pct > 5:
                    status = "At Risk"
            else:
                if variance_pct < -10:
                    status = "Critical"
                elif variance_pct < -5:
                    status = "At Risk"

            variance_results.append(
                {
                    "label": metric.replace("_", " ").title(),
                    "actual": actual,
                    "planned": planned,
                    "variance": variance,
                    "variance_pct": variance_pct,
                    "variance_pct_abs": abs(variance_pct),
                    "status": status,
                }
            )

        return variance_results


class FinancialPerformanceView(FinancialBaseView):
    """
    View for the Financial Performance Reports dashboard.
    """

    template_name = "profitability/reports/financial_performance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Source indicators/footnotes
        context["source_indicators"] = [
            {"label": "Revenue", "description": "Certified to date - Cumulative"},
            {
                "label": "COGS",
                "description": "Material + Labour + Subcontractor + Plant trackers",
            },
            {"label": "OpEx", "description": "Overhead tracker + Journal Entries"},
            {
                "label": "Planned",
                "description": "Calculated from baseline assumptions (60% COGS, 12% OpEx)",
            },
            {"label": "Forecast", "description": "From Expenditure Forecast"},
        ]
        context["tab"] = "performance_report"
        return context


class FinancialBreakdownView(FinancialBaseView):
    """
    View for the Detailed Financial Breakdown (Table).
    """

    template_name = "profitability/reports/financial_breakdown.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tab"] = "performance_report"
        return context


class FinancialPerformanceDataView(ProfitabilityMixin, TemplateView):
    """
    JSON View that provides data for the charts in the Financial Performance Report.
    """

    def get(self, request, *args, **kwargs):
        project = self.project

        # 1. Period Setup
        today = date.today()
        
        # Default: End of previous month
        default_end_date = today.replace(day=1) - timedelta(days=1)
        # Default: Start of 6 month period ending at previous month
        default_start_date = (default_end_date - relativedelta(months=5)).replace(day=1)

        # Handle Query Parameters (from filters)
        start_date_param = request.GET.get("start_date")
        end_date_param = request.GET.get("end_date")

        try:
            start_date = date.fromisoformat(start_date_param).replace(day=1) if start_date_param else default_start_date
        except (ValueError, TypeError):
            start_date = default_start_date

        try:
            end_date = date.fromisoformat(end_date_param) if end_date_param else default_end_date
        except (ValueError, TypeError):
            end_date = default_end_date

        # Generate months list
        months = []
        current = start_date
        # Boundary: include the month of the end_date
        while current <= end_date.replace(day=1):
            months.append(current)
            current += relativedelta(months=1)

        labels = [m.strftime("%b %Y") for m in months]

        # 2. Monthly Data Aggregation
        revenue_actual = []
        revenue_planned = []
        cost_actual = []
        cost_planned = []
        profit_actual = []

        for m_start in months:
            m_end = (m_start + relativedelta(months=1)) - timedelta(days=1)

            # --- Actual Revenue ---
            # Sum of actual transactions in APPROVED certificates in this month
            rev_act = (
                ActualTransaction.objects.filter(
                    line_item__project=project,
                    payment_certificate__status=PaymentCertificate.Status.APPROVED,
                    payment_certificate__approved_on__date__range=(m_start, m_end),
                ).aggregate(total=Sum("total_price"))["total"]
                or Decimal("0.00")
            )
            revenue_actual.append(float(rev_act))

            # --- Planned Revenue ---
            rev_plan = (
                PlannedValue.objects.filter(project=project, period=m_start).aggregate(
                    total=Sum("value")
                )["total"]
                or Decimal("0.00")
            )
            revenue_planned.append(float(rev_plan))

            # --- Actual Cost (Sum of all trackers) ---
            cost_m = (
                MaterialCostTracker.objects.filter(
                    project=project, date__range=(m_start, m_end)
                ).aggregate(total=Sum(F("quantity") * F("rate")))["total"]
                or 0
            )
            cost_l = (
                LabourCostTracker.objects.filter(
                    project=project, date__range=(m_start, m_end)
                ).aggregate(total=Sum(F("amount_of_days") * F("salary")))["total"]
                or 0
            )
            cost_s = (
                SubcontractorCostTracker.objects.filter(
                    project=project, date__range=(m_start, m_end)
                ).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"]
                or 0
            )
            cost_p = (
                PlantCostTracker.objects.filter(
                    project=project, date__range=(m_start, m_end)
                ).aggregate(total=Sum(F("usage_hours") * F("hourly_rate")))["total"]
                or 0
            )
            total_cost_m = Decimal(str(cost_m + cost_l + cost_s + cost_p))
            cost_actual.append(float(total_cost_m))

            # --- Planned Cost (Assumption: 60% of planned revenue) ---
            cost_plan = rev_plan * Decimal("0.60")
            cost_planned.append(float(cost_plan))

            # --- Monthly Profit ---
            profit_actual.append(float(rev_act - total_cost_m))

        # 3. Overall Totals for Breakdowns (Current Project Total)
        total_materials = (
            MaterialCostTracker.objects.filter(project=project).aggregate(
                total=Sum(F("quantity") * F("rate"))
            )["total"]
            or 0
        )
        total_labour = (
            LabourCostTracker.objects.filter(project=project).aggregate(
                total=Sum(F("amount_of_days") * F("salary"))
            )["total"]
            or 0
        )
        total_subcon = (
            SubcontractorCostTracker.objects.filter(project=project).aggregate(
                total=Sum(F("amount_of_days") * F("rate"))
            )["total"]
            or 0
        )
        total_plant = (
            PlantCostTracker.objects.filter(project=project).aggregate(
                total=Sum(F("usage_hours") * F("hourly_rate"))
            )["total"]
            or 0
        )

        total_overheads = (
            OverheadCostTracker.objects.filter(project=project).aggregate(
                total=Sum(F("amount_of_days") * F("rate"))
            )["total"]
            or 0
        )
        total_journals = (
            JournalEntry.objects.filter(
                project=project, category=JournalEntry.Category.OVERHEAD
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        return JsonResponse(
            {
                "labels": labels,
                "datasets": {
                    "revenue_actual": revenue_actual,
                    "revenue_planned": revenue_planned,
                    "cost_actual": cost_actual,
                    "cost_planned": cost_planned,
                    "profit_actual": profit_actual,
                    "cost_breakdown": [
                        float(total_materials),
                        float(total_labour),
                        float(total_subcon),
                        float(total_plant),
                    ],
                    "opex_breakdown": [float(total_overheads), float(total_journals)],
                },
            }
        )
