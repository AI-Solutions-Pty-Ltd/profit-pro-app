from datetime import date, datetime, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import F, Sum
from django.http import JsonResponse
from django.views.generic import TemplateView

from app.BillOfQuantities.models import (
    ActualTransaction,
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
from app.Project.profitability.mixins import FinancialCalculationMixin
from app.Project.profitability.views import ProfitabilityMixin


class FinancialBaseView(ProfitabilityMixin, FinancialCalculationMixin, TemplateView):
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
            {
                "label": "OpEx",
                "description": "All tracker items classified as 'Operating Expense' + Journal Overheads",
            },
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


class IncomeStatementView(FinancialBaseView):
    """
    Detailed Income Statement Report with COS and OpEx breakdown.
    """

    template_name = "profitability/reports/income_statement.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.project
        start_date = context["start_date"]
        end_date = context["end_date"]

        from app.Project.models.entity_definitions import BaseProjectEntity

        cos_code = BaseProjectEntity.ExpenseCode.COS
        opex_code = BaseProjectEntity.ExpenseCode.OPEX

        # 1. Revenue
        revenue_items = []
        # Certificates
        cert_rev = (
            ActualTransaction.objects.filter(
                line_item__project=project,
                payment_certificate__status=PaymentCertificate.Status.APPROVED,
                payment_certificate__approved_on__date__range=(start_date, end_date),
            ).aggregate(total=Sum("total_price"))["total"]
            or Decimal("0.00")
        )
        if cert_rev > 0:
            revenue_items.append({"label": "Certified Work", "amount": cert_rev})

        # Journal Credits
        journal_rev = (
            JournalEntry.objects.filter(
                project=project,
                transaction_type=JournalEntry.EntryType.CREDIT,
                date__range=(start_date, end_date),
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        if journal_rev > 0:
            revenue_items.append({"label": "Other Income (Journals)", "amount": journal_rev})

        total_revenue = cert_rev + journal_rev

        # Helper for manual journal entries
        def get_manual_journal_total(categories):
            if isinstance(categories, str):
                categories = [categories]
                
            return (
                JournalEntry.objects.filter(
                    project=project,
                    transaction_type=JournalEntry.EntryType.DEBIT,
                    category__in=categories,
                    source_log_id__isnull=True,  # Manual entries only
                    date__range=(start_date, end_date),
                ).aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

        # Helper for tracker summaries
        def get_tracker_summary(code):
            filters = {"project": project, "date__range": (start_date, end_date)}
            items = []

            # Labour
            lab_tracker = (
                LabourCostTracker.objects.filter(
                    **filters, labour_entity__expense_code=code
                ).aggregate(total=Sum(F("amount_of_days") * F("salary")))["total"]
                or 0
            )
            lab_manual = Decimal("0.00")
            # If we are in COS, add manual labour journals.
            if code == cos_code:
                lab_manual = get_manual_journal_total(JournalEntry.Category.LABOUR)
                
            lab_total = Decimal(str(lab_tracker)) + lab_manual
            if lab_total > 0:
                items.append({"label": "Labour Costs", "amount": lab_total})

            # Materials
            mat_tracker = (
                MaterialCostTracker.objects.filter(
                    **filters, material_entity__expense_code=code
                ).aggregate(total=Sum(F("quantity") * F("rate")))["total"]
                or 0
            )
            mat_manual = Decimal("0.00")
            if code == cos_code:
                mat_manual = get_manual_journal_total(JournalEntry.Category.MATERIAL)

            mat_total = Decimal(str(mat_tracker)) + mat_manual
            if mat_total > 0:
                items.append({"label": "Material Costs", "amount": mat_total})

            # Subcontractors
            sub_tracker = (
                SubcontractorCostTracker.objects.filter(
                    **filters, subcontractor_entity__expense_code=code
                ).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"]
                or 0
            )
            sub_manual = Decimal("0.00")
            if code == cos_code:
                sub_manual = get_manual_journal_total(JournalEntry.Category.SUBCONTRACTOR)

            sub_total = Decimal(str(sub_tracker)) + sub_manual
            if sub_total > 0:
                items.append({"label": "Subcontractor Costs", "amount": sub_total})

            # Plant
            plt_tracker = (
                PlantCostTracker.objects.filter(
                    **filters, plant_entity__expense_code=code
                ).aggregate(total=Sum(F("usage_hours") * F("hourly_rate")))["total"]
                or 0
            )
            plt_manual = Decimal("0.00")
            if code == cos_code:
                plt_manual = get_manual_journal_total(JournalEntry.Category.PLANT)

            plt_total = Decimal(str(plt_tracker)) + plt_manual
            if plt_total > 0:
                items.append({"label": "Plant & Equipment", "amount": plt_total})

            # Overheads Tracker
            ovh_tracker = (
                OverheadCostTracker.objects.filter(
                    **filters, overhead_entity__expense_code=code
                ).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"]
                or 0
            )
            ovh_manual = Decimal("0.00")
            # Overheads manual journals go to OpEx usually
            if code == opex_code:
                ovh_manual = get_manual_journal_total([
                    JournalEntry.Category.OVERHEAD,
                    JournalEntry.Category.OTHER
                ])

            ovh_total = Decimal(str(ovh_tracker)) + ovh_manual
            if ovh_total > 0:
                label = "Administrative Overheads" if code == opex_code else "Direct Overheads"
                items.append({"label": label, "amount": ovh_total})

            return items

        # 2. Cost of Sales (COS)
        cos_items = get_tracker_summary(cos_code)
        total_cos = sum(item["amount"] for item in cos_items)

        # Gross Profit
        gross_profit = total_revenue - total_cos
        gp_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

        # 3. Operating Expenses (OpEx)
        opex_items = get_tracker_summary(opex_code)
        
        total_opex = sum(item["amount"] for item in opex_items)

        # Net profit
        net_profit = gross_profit - total_opex
        np_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        # Inject percentages
        def add_pct(items, base):
            for item in items:
                item["pct"] = (item["amount"] / base * 100) if base > 0 else 0
            return items

        context["income_statement"] = {
            "revenue": {
                "items": add_pct(revenue_items, total_revenue),
                "total": total_revenue,
            },
            "cos": {
                "items": add_pct(cos_items, total_revenue),
                "total": total_cos,
                "pct": (total_cos / total_revenue * 100) if total_revenue > 0 else 0,
            },
            "gross_profit": {
                "amount": gross_profit,
                "margin": gp_margin,
            },
            "opex": {
                "items": add_pct(opex_items, total_revenue),
                "total": total_opex,
                "pct": (total_opex / total_revenue * 100) if total_revenue > 0 else 0,
            },
            "net_profit": {
                "amount": net_profit,
                "margin": np_margin,
            },
        }

        context["tab"] = "performance_report"
        context["report_name"] = "Income Statement"
        context["generated_at"] = datetime.now()
        
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
        opex_actual = []  # Added

        from app.Project.models.entity_definitions import BaseProjectEntity

        cos_code = BaseProjectEntity.ExpenseCode.COS
        opex_code = BaseProjectEntity.ExpenseCode.OPEX

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
                MaterialCostTracker,
                "material_entity",
                m_start,
                m_end,
                cos_code,
                "quantity",
                "rate",
            )
            c_lab = get_m_total(
                LabourCostTracker,
                "labour_entity",
                m_start,
                m_end,
                cos_code,
                "amount_of_days",
                "salary",
            )
            c_sub = get_m_total(
                SubcontractorCostTracker,
                "subcontractor_entity",
                m_start,
                m_end,
                cos_code,
                "amount_of_days",
                "rate",
            )
            c_plt = get_m_total(
                PlantCostTracker,
                "plant_entity",
                m_start,
                m_end,
                cos_code,
                "usage_hours",
                "hourly_rate",
            )
            c_ovh = get_m_total(
                OverheadCostTracker,
                "overhead_entity",
                m_start,
                m_end,
                cos_code,
                "amount_of_days",
                "rate",
            )

            total_cos_m = Decimal(str(c_mat + c_lab + c_sub + c_plt + c_ovh))
            cost_actual.append(float(total_cos_m))

            # --- Planned Cost (Assumption: 60% of planned revenue) ---
            cost_plan = rev_plan * Decimal("0.60")
            cost_planned.append(float(cost_plan))

            # --- Monthly Profit (Revenue - Total Cost [COS + OPEX]) ---
            o_mat = get_m_total(
                MaterialCostTracker,
                "material_entity",
                m_start,
                m_end,
                opex_code,
                "quantity",
                "rate",
            )
            o_lab = get_m_total(
                LabourCostTracker,
                "labour_entity",
                m_start,
                m_end,
                opex_code,
                "amount_of_days",
                "salary",
            )
            o_sub = get_m_total(
                SubcontractorCostTracker,
                "subcontractor_entity",
                m_start,
                m_end,
                opex_code,
                "amount_of_days",
                "rate",
            )
            o_plt = get_m_total(
                PlantCostTracker,
                "plant_entity",
                m_start,
                m_end,
                opex_code,
                "usage_hours",
                "hourly_rate",
            )
            o_ovh = get_m_total(
                OverheadCostTracker,
                "overhead_entity",
                m_start,
                m_end,
                opex_code,
                "amount_of_days",
                "rate",
            )
            o_journal = (
                JournalEntry.objects.filter(
                    project=project,
                    category=JournalEntry.Category.OVERHEAD,
                    date__range=(m_start, m_end),
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )

            total_opex_m = Decimal(
                str(o_mat + o_lab + o_sub + o_plt + o_ovh + o_journal)
            )

            gross_profit_actual.append(float(rev_act - total_cos_m))
            opex_actual.append(float(total_opex_m))
            profit_actual.append(float(rev_act - total_cos_m - total_opex_m))

        # 3. Overall Totals for Breakdowns (Current Project Total)
        def get_total_breakdown(source, field1, field2):
            """Helper to sum costs from either a model class or a pre-filtered queryset."""
            if hasattr(source, "_default_manager"):
                qs = source.objects.filter(project=project)
            else:
                qs = source  # It's already a queryset
            return qs.aggregate(total=Sum(F(field1) * F(field2)))["total"] or 0

        total_materials = get_total_breakdown(MaterialCostTracker, "quantity", "rate")
        total_labour = get_total_breakdown(
            LabourCostTracker, "amount_of_days", "salary"
        )
        total_subcon = get_total_breakdown(
            SubcontractorCostTracker, "amount_of_days", "rate"
        )
        total_plant = get_total_breakdown(
            PlantCostTracker, "usage_hours", "hourly_rate"
        )
        total_overheads_all = get_total_breakdown(
            OverheadCostTracker, "amount_of_days", "rate"
        )

        # OPEX specifically (Overheads + Journals + Any tracker items marked OPEX)
        o_mat_total = get_total_breakdown(
            MaterialCostTracker.objects.filter(
                project=project, material_entity__expense_code=opex_code
            ),
            "quantity",
            "rate",
        )
        o_lab_total = get_total_breakdown(
            LabourCostTracker.objects.filter(
                project=project, labour_entity__expense_code=opex_code
            ),
            "amount_of_days",
            "salary",
        )
        o_sub_total = get_total_breakdown(
            SubcontractorCostTracker.objects.filter(
                project=project, subcontractor_entity__expense_code=opex_code
            ),
            "amount_of_days",
            "rate",
        )
        o_plt_total = get_total_breakdown(
            PlantCostTracker.objects.filter(
                project=project, plant_entity__expense_code=opex_code
            ),
            "usage_hours",
            "hourly_rate",
        )
        o_ovh_total = get_total_breakdown(
            OverheadCostTracker.objects.filter(
                project=project, overhead_entity__expense_code=opex_code
            ),
            "amount_of_days",
            "rate",
        )

        total_opex_trackers = Decimal(
            str(o_mat_total + o_lab_total + o_sub_total + o_plt_total + o_ovh_total)
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
                    "gross_profit_actual": gross_profit_actual,
                    "opex_actual": opex_actual,
                    "cost_breakdown": [
                        float(total_materials),
                        float(total_labour),
                        float(total_subcon),
                        float(total_plant),
                        float(total_overheads_all),
                    ],
                    "opex_breakdown": [
                        float(total_opex_trackers),
                        float(total_journals),
                    ],
                },
            }
        )
