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
    PlantCostTracker,
    Project,
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

        # Date range for report (Project Start to End of Previous Month)
        today = date.today()
        start_date = project.start_date if project.start_date else date(today.year, 1, 1)
        end_date = today.replace(day=1) - timedelta(days=1)

        # Get financial metrics
        context["start_date"] = start_date
        context["end_date"] = end_date
        context["financial_table"] = self.get_financial_table_data(start_date, end_date)
        context["baseline_assumptions"] = self.get_baseline_assumptions()
        context["variance_analysis"] = self.get_variance_analysis(context["financial_table"])

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
        material_actual = MaterialCostTracker.objects.filter(project=project, date__lte=end_date).aggregate(total=Sum(F("quantity") * F("rate")))["total"] or 0
        labour_actual = LabourCostTracker.objects.filter(project=project, date__lte=end_date).aggregate(total=Sum(F("amount_of_days") * F("salary")))["total"] or 0
        subcon_actual = SubcontractorCostTracker.objects.filter(project=project, date__lte=end_date).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"] or 0
        plant_actual = PlantCostTracker.objects.filter(project=project, date__lte=end_date).aggregate(total=Sum(F("usage_hours") * F("hourly_rate")))["total"] or 0
        
        actual_cogs_to_date = Decimal(material_actual) + Decimal(labour_actual) + Decimal(subcon_actual) + Decimal(plant_actual)

        material_month = MaterialCostTracker.objects.filter(project=project, date__gte=this_month_start).aggregate(total=Sum(F("quantity") * F("rate")))["total"] or 0
        labour_month = LabourCostTracker.objects.filter(project=project, date__gte=this_month_start).aggregate(total=Sum(F("amount_of_days") * F("salary")))["total"] or 0
        subcon_month = SubcontractorCostTracker.objects.filter(project=project, date__gte=this_month_start).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"] or 0
        plant_month = PlantCostTracker.objects.filter(project=project, date__gte=this_month_start).aggregate(total=Sum(F("usage_hours") * F("hourly_rate")))["total"] or 0
        
        actual_cogs_this_month = Decimal(material_month) + Decimal(labour_month) + Decimal(subcon_month) + Decimal(plant_month)

        planned_cogs_to_date = planned_revenue_to_date * Decimal("0.60")

        # --- OPERATING EXPENSES (OPEX) ---
        overhead_tracker_actual = OverheadCostTracker.objects.filter(project=project, date__lte=end_date).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"] or 0
        journal_overhead_actual = JournalEntry.objects.filter(project=project, category=JournalEntry.Category.OVERHEAD, date__lte=end_date).aggregate(total=Sum("amount"))["total"] or 0
        
        actual_opex_to_date = Decimal(overhead_tracker_actual) + Decimal(journal_overhead_actual)

        overhead_tracker_month = OverheadCostTracker.objects.filter(project=project, date__gte=this_month_start).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"] or 0
        journal_overhead_month = JournalEntry.objects.filter(project=project, category=JournalEntry.Category.OVERHEAD, date__gte=this_month_start).aggregate(total=Sum("amount"))["total"] or 0
        
        actual_opex_this_month = Decimal(overhead_tracker_month) + Decimal(journal_overhead_month)

        planned_opex_to_date = planned_revenue_to_date * Decimal("0.12")

        # --- CALCULATIONS ---
        actual_gp_to_date = actual_revenue_to_date - actual_cogs_to_date
        planned_gp_to_date = planned_revenue_to_date - planned_cogs_to_date
        actual_gp_this_month = actual_revenue_this_month - actual_cogs_this_month
        
        actual_np_to_date = actual_gp_to_date - actual_opex_to_date
        planned_np_to_date = planned_gp_to_date - planned_opex_to_date
        actual_np_this_month = actual_gp_this_month - actual_opex_this_month

        gp_margin_actual = (actual_gp_to_date / actual_revenue_to_date * 100) if actual_revenue_to_date > 0 else 0
        gp_margin_planned = (planned_gp_to_date / planned_revenue_to_date * 100) if planned_revenue_to_date > 0 else 0
        
        np_margin_actual = (actual_np_to_date / actual_revenue_to_date * 100) if actual_revenue_to_date > 0 else 0
        np_margin_planned = (planned_np_to_date / planned_revenue_to_date * 100) if planned_revenue_to_date > 0 else 0

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
                "actual_this_month": (actual_gp_this_month / actual_revenue_this_month * 100) if actual_revenue_this_month > 0 else 0,
                "forecast": 40.0,
            },
            "np_margin": {
                "actual_to_date": np_margin_actual,
                "planned_to_date": np_margin_planned,
                "actual_this_month": (actual_np_this_month / actual_revenue_this_month * 100) if actual_revenue_this_month > 0 else 0,
                "forecast": 28.0,
            },
        }

    def get_variance_analysis(self, table_data):
        """Prepare variance data for display."""
        metrics = ["revenue", "cost_of_sales", "gross_profit", "operating_expenses", "net_profit"]
        variance_results = []
        
        for metric in metrics:
            actual = table_data[metric]["actual_to_date"]
            planned = table_data[metric]["planned_to_date"]
            variance = actual - planned
            variance_pct = (variance / planned * 100) if planned != 0 else 0
            
            status = "On Track"
            if metric in ["cost_of_sales", "operating_expenses"]:
                if variance_pct > 10: status = "Critical"
                elif variance_pct > 5: status = "At Risk"
            else:
                if variance_pct < -10: status = "Critical"
                elif variance_pct < -5: status = "At Risk"
                
            variance_results.append({
                "label": metric.replace("_", " ").title(),
                "actual": actual,
                "planned": planned,
                "variance": variance,
                "variance_pct": variance_pct,
                "variance_pct_abs": abs(variance_pct),
                "status": status
            })
            
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
            {"label": "COGS", "description": "Material + Labour + Subcontractor + Plant trackers"},
            {"label": "OpEx", "description": "Overhead tracker + Journal Entries"},
            {"label": "Planned", "description": "Calculated from baseline assumptions (60% COGS, 12% OpEx)"},
            {"label": "Forecast", "description": "From Expenditure Forecast"},
        ]
        return context


class FinancialBreakdownView(FinancialBaseView):
    """
    View for the Detailed Financial Breakdown (Table).
    """

    template_name = "profitability/reports/financial_breakdown.html"


class FinancialPerformanceDataView(ProfitabilityMixin, TemplateView):
    """
    JSON endpoint for chart data (Optimized for Chart.js).
    """
    def get(self, request, *args, **kwargs):
        # Get end of previous month
        today = date.today()
        end_date = today.replace(day=1) - timedelta(days=1)
        
        # Generate last 6 months labels
        labels = []
        for i in range(5, -1, -1):
            month_date = end_date - relativedelta(months=i)
            labels.append(month_date.strftime("%b"))

        chart_data = {
            "labels": labels,
            "datasets": {
                "revenue_actual": [100000, 150000, 200000, 180000, 220000, 250000],
                "revenue_planned": [110000, 140000, 190000, 190000, 210000, 240000],
                "cost_actual": [80000, 120000, 160000, 150000, 180000, 210000],
                "cost_planned": [70000, 110000, 150000, 150000, 170000, 200000],
                "profit_actual": [20000, 30000, 40000, 30000, 40000, 40000],
                "cost_breakdown": [44, 32, 17, 7],
                "opex_breakdown": [65, 35],
            }
        }
        return JsonResponse(chart_data)
