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
        default_end_date = today
        default_start_date = (
            project.start_date if project.start_date else date(today.year, 1, 1)
        )

        # Handle Query Parameters (from filters)
        start_date_param = request.GET.get("start_date")
        end_date_param = request.GET.get("end_date")

        try:
            start_date = (
                date.fromisoformat(start_date_param)
                if start_date_param
                else default_start_date
            )
        except (ValueError, TypeError):
            start_date = default_start_date

        try:
            end_date = (
                date.fromisoformat(end_date_param)
                if end_date_param
                else default_end_date
            )
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
        # Sum of actual transactions in APPROVED certificates up to end_date
        actual_revenue_to_date = (
            ActualTransaction.objects.filter(
                line_item__project=project,
                payment_certificate__status=PaymentCertificate.Status.APPROVED,
                payment_certificate__approved_on__date__lte=end_date,
            ).aggregate(total=Sum("total_price"))["total"]
            or Decimal("0.00")
        )

        this_month_start = date.today().replace(day=1)
        actual_revenue_this_month = (
            ActualTransaction.objects.filter(
                line_item__project=project,
                payment_certificate__status=PaymentCertificate.Status.APPROVED,
                payment_certificate__approved_on__gte=this_month_start,
            ).aggregate(total=Sum("total_price"))["total"]
            or Decimal("0.00")
        )

        planned_revenue_to_date = BaselineCashflow.objects.filter(
            project=project,
            status=BaselineCashflow.Status.APPROVED,
            period__lte=end_date,
        ).aggregate(total=Sum("planned_value"))["total"] or Decimal("0.00")

        forecast_revenue = CashflowForecast.objects.filter(
            project=project,
            status=CashflowForecast.Status.APPROVED,
        ).aggregate(total=Sum("forecast_value"))["total"] or Decimal("0.00")

        # --- COST CALCULATIONS (SEGMENTED BY COS/OPEX) ---
        from app.Project.models.entity_definitions import BaseProjectEntity

        COS = BaseProjectEntity.ExpenseCode.COS
        OPEX = BaseProjectEntity.ExpenseCode.OPEX

        def get_tracker_totals(start=None, end=None, code=COS):
            """Internal helper to sum costs from all trackers for a given classification."""
            filters = {"project": project}
            if start:
                filters["date__gte"] = start
            if end:
                filters["date__lte"] = end

            mat = (
                MaterialCostTracker.objects.filter(
                    **filters, material_entity__expense_code=code
                ).aggregate(total=Sum(F("quantity") * F("rate")))["total"]
                or 0
            )
            lab = (
                LabourCostTracker.objects.filter(
                    **filters, labour_entity__expense_code=code
                ).aggregate(total=Sum(F("amount_of_days") * F("salary")))["total"]
                or 0
            )
            sub = (
                SubcontractorCostTracker.objects.filter(
                    **filters, subcontractor_entity__expense_code=code
                ).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"]
                or 0
            )
            plt = (
                PlantCostTracker.objects.filter(
                    **filters, plant_entity__expense_code=code
                ).aggregate(total=Sum(F("usage_hours") * F("hourly_rate")))["total"]
                or 0
            )
            ovh = (
                OverheadCostTracker.objects.filter(
                    **filters, overhead_entity__expense_code=code
                ).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"]
                or 0
            )
            return Decimal(str(mat)) + Decimal(str(lab)) + Decimal(str(sub)) + Decimal(str(plt)) + Decimal(str(ovh))

        # 1. Totals to Date
        actual_cogs_to_date = get_tracker_totals(end=end_date, code=COS)
        actual_opex_trackers_to_date = get_tracker_totals(end=end_date, code=OPEX)

        journal_overhead_actual = (
            JournalEntry.objects.filter(
                project=project,
                category=JournalEntry.Category.OVERHEAD,
                date__lte=end_date,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        actual_opex_to_date = actual_opex_trackers_to_date + Decimal(
            str(journal_overhead_actual)
        )

        # 2. This Month Totals
        actual_cogs_this_month = get_tracker_totals(start=this_month_start, code=COS)
        actual_opex_trackers_month = get_tracker_totals(
            start=this_month_start, code=OPEX
        )

        journal_overhead_month = (
            JournalEntry.objects.filter(
                project=project,
                category=JournalEntry.Category.OVERHEAD,
                date__gte=this_month_start,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        actual_opex_this_month = actual_opex_trackers_month + Decimal(
            str(journal_overhead_month)
        )

        planned_cogs_to_date = planned_revenue_to_date * Decimal("0.60")
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
                "description": "All tracker items classified as 'Cost of Sales' (including Labour, Materials, etc.)",
            },
            {"label": "OpEx", "description": "All tracker items classified as 'Operating Expense' + Journal Overheads"},
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
            start_date = (
                date.fromisoformat(start_date_param).replace(day=1)
                if start_date_param
                else default_start_date
            )
        except (ValueError, TypeError):
            start_date = default_start_date

        try:
            end_date = (
                date.fromisoformat(end_date_param)
                if end_date_param
                else default_end_date
            )
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
        gross_profit_actual = []  # Added
        opex_actual = []          # Added

        from app.Project.models.entity_definitions import BaseProjectEntity
        COS_CODE = BaseProjectEntity.ExpenseCode.COS
        OPEX_CODE = BaseProjectEntity.ExpenseCode.OPEX

        for m_start in months:
            m_end = (m_start + relativedelta(months=1)) - timedelta(days=1)

            # --- Actual Revenue ---
            rev_act = ActualTransaction.objects.filter(
                line_item__project=project,
                payment_certificate__status=PaymentCertificate.Status.APPROVED,
                payment_certificate__approved_on__date__range=(m_start, m_end),
            ).aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")
            revenue_actual.append(float(rev_act))

            # --- Planned Revenue ---
            rev_plan = PlannedValue.objects.filter(
                project=project, period=m_start
            ).aggregate(total=Sum("value"))["total"] or Decimal("0.00")
            revenue_planned.append(float(rev_plan))

            # --- Actual Cost (COS only for comparison with Planned COS) ---
            def get_m_total(model, attr, start, end, code, field1, field2):
                filters = {
                    "project": project,
                    "date__range": (start, end),
                    f"{attr}__expense_code": code,
                }
                return (
                    model.objects.filter(**filters).aggregate(
                        total=Sum(F(field1) * F(field2))
                    )["total"]
                    or 0
                )

            c_mat = get_m_total(
                MaterialCostTracker, "material_entity", m_start, m_end, COS_CODE, "quantity", "rate"
            )
            c_lab = get_m_total(
                LabourCostTracker, "labour_entity", m_start, m_end, COS_CODE, "amount_of_days", "salary"
            )
            c_sub = get_m_total(
                SubcontractorCostTracker, "subcontractor_entity", m_start, m_end, COS_CODE, "amount_of_days", "rate"
            )
            c_plt = get_m_total(
                PlantCostTracker, "plant_entity", m_start, m_end, COS_CODE, "usage_hours", "hourly_rate"
            )
            c_ovh = get_m_total(
                OverheadCostTracker, "overhead_entity", m_start, m_end, COS_CODE, "amount_of_days", "rate"
            )

            total_cos_m = Decimal(str(c_mat + c_lab + c_sub + c_plt + c_ovh))
            cost_actual.append(float(total_cos_m))

            # --- Planned Cost (Assumption: 60% of planned revenue) ---
            cost_plan = rev_plan * Decimal("0.60")
            cost_planned.append(float(cost_plan))

            # --- Monthly Profit (Revenue - Total Cost [COS + OPEX]) ---
            o_mat = get_m_total(
                MaterialCostTracker, "material_entity", m_start, m_end, OPEX_CODE, "quantity", "rate"
            )
            o_lab = get_m_total(
                LabourCostTracker, "labour_entity", m_start, m_end, OPEX_CODE, "amount_of_days", "salary"
            )
            o_sub = get_m_total(
                SubcontractorCostTracker, "subcontractor_entity", m_start, m_end, OPEX_CODE, "amount_of_days", "rate"
            )
            o_plt = get_m_total(
                PlantCostTracker, "plant_entity", m_start, m_end, OPEX_CODE, "usage_hours", "hourly_rate"
            )
            o_ovh = get_m_total(
                OverheadCostTracker, "overhead_entity", m_start, m_end, OPEX_CODE, "amount_of_days", "rate"
            )
            o_journal = (
                JournalEntry.objects.filter(
                    project=project,
                    category=JournalEntry.Category.OVERHEAD,
                    date__range=(m_start, m_end),
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )

            total_opex_m = Decimal(str(o_mat + o_lab + o_sub + o_plt + o_ovh + o_journal))
            
            gross_profit_actual.append(float(rev_act - total_cos_m))
            opex_actual.append(float(total_opex_m))
            profit_actual.append(float(rev_act - total_cos_m - total_opex_m))

        # 3. Overall Totals for Breakdowns (Current Project Total)
        def get_total_breakdown(source, field1, field2):
            """Helper to sum costs from either a model class or a pre-filtered queryset."""
            if hasattr(source, "_default_manager"):
                qs = source.objects.filter(project=project)
            else:
                qs = source # It's already a queryset
            return (
                qs.aggregate(total=Sum(F(field1) * F(field2)))["total"]
                or 0
            )

        total_materials = get_total_breakdown(MaterialCostTracker, "quantity", "rate")
        total_labour = get_total_breakdown(LabourCostTracker, "amount_of_days", "salary")
        total_subcon = get_total_breakdown(SubcontractorCostTracker, "amount_of_days", "rate")
        total_plant = get_total_breakdown(PlantCostTracker, "usage_hours", "hourly_rate")
        total_overheads_all = get_total_breakdown(OverheadCostTracker, "amount_of_days", "rate")

        # OPEX specifically (Overheads + Journals + Any tracker items marked OPEX)
        o_mat_total = get_total_breakdown(MaterialCostTracker.objects.filter(project=project, material_entity__expense_code=OPEX_CODE), "quantity", "rate")
        o_lab_total = get_total_breakdown(LabourCostTracker.objects.filter(project=project, labour_entity__expense_code=OPEX_CODE), "amount_of_days", "salary")
        o_sub_total = get_total_breakdown(SubcontractorCostTracker.objects.filter(project=project, subcontractor_entity__expense_code=OPEX_CODE), "amount_of_days", "rate")
        o_plt_total = get_total_breakdown(PlantCostTracker.objects.filter(project=project, plant_entity__expense_code=OPEX_CODE), "usage_hours", "hourly_rate")
        o_ovh_total = get_total_breakdown(OverheadCostTracker.objects.filter(project=project, overhead_entity__expense_code=OPEX_CODE), "amount_of_days", "rate")
        
        total_opex_trackers = Decimal(str(o_mat_total + o_lab_total + o_sub_total + o_plt_total + o_ovh_total))
        
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
                    "gross_profit_actual": gross_profit_actual,
                    "opex_actual": opex_actual,
                    "cost_breakdown": [
                        float(total_materials),
                        float(total_labour),
                        float(total_subcon),
                        float(total_plant),
                        float(total_overheads_all),
                    ],
                    "opex_breakdown": [float(total_opex_trackers), float(total_journals)],
                },
            }
        )
