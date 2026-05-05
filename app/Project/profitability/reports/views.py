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
    BaseProjectEntity,
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
        lookback_param = request.GET.get("lookback")

        # end_date always defaults to today if not provided
        try:
            end_date = (
                date.fromisoformat(end_date_param)
                if end_date_param
                else default_end_date
            )
        except (ValueError, TypeError):
            end_date = default_end_date

        # start_date logic based on lookback or explicit param
        if lookback_param and lookback_param != "ALL":
            months_map = {"1M": 1, "3M": 3, "6M": 6, "12M": 12}
            months = months_map.get(lookback_param, 0)
            if months > 0:
                start_date = end_date - relativedelta(months=months)
            else:
                start_date = default_start_date
        elif start_date_param:
            try:
                start_date = date.fromisoformat(start_date_param)
            except (ValueError, TypeError):
                start_date = default_start_date
        else:
            start_date = default_start_date

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
        project = self.project
        start_date = context["start_date"]
        end_date = context["end_date"]

        # 1. Certificates Detail (Certified Work)
        certificates = PaymentCertificate.objects.filter(
            project=project,
            status__in=[
                PaymentCertificate.Status.APPROVED,
                PaymentCertificate.Status.SIGNATORIES_APPROVED,
            ],
            approved_on__date__range=(start_date, end_date),
        ).order_by("-approved_on")

        # 2. Journals Detail (Other Income)
        journal_entries = JournalEntry.objects.filter(
            project=project,
            transaction_type=JournalEntry.EntryType.CREDIT,
            date__range=(start_date, end_date),
        ).order_by("-date")

        cert_total = sum(
            getattr(c, "total_certified_amount", Decimal("0.00")) for c in certificates
        )
        journal_total = sum(j.amount for j in journal_entries)

        # 3. Cost of Sales (COS) Breakdown
        cos_code = BaseProjectEntity.ExpenseCode.COS
        cos_tracker_filters = {
            "project": project,
            "date__range": (start_date, end_date),
        }

        cos_trackers = {
            "materials": MaterialCostTracker.objects.filter(
                **cos_tracker_filters, material_entity__expense_code=cos_code
            ),
            "labour": LabourCostTracker.objects.filter(
                **cos_tracker_filters, labour_entity__expense_code=cos_code
            ),
            "subcontractors": SubcontractorCostTracker.objects.filter(
                **cos_tracker_filters, subcontractor_entity__expense_code=cos_code
            ),
            "plant": PlantCostTracker.objects.filter(
                **cos_tracker_filters, plant_entity__expense_code=cos_code
            ),
            "overhead": OverheadCostTracker.objects.filter(
                **cos_tracker_filters, overhead_entity__expense_code=cos_code
            ),
        }

        cos_journal_items = JournalEntry.objects.filter(
            project=project,
            transaction_type=JournalEntry.EntryType.DEBIT,
            date__range=(start_date, end_date),
            category__in=[
                JournalEntry.Category.MATERIAL,
                JournalEntry.Category.LABOUR,
                JournalEntry.Category.SUBCONTRACTOR,
                JournalEntry.Category.PLANT,
            ],
        ).order_by("-date")

        # 4. Operating Expenses (OpEx) Breakdown
        opex_code = BaseProjectEntity.ExpenseCode.OPEX
        opex_tracker_filters = {
            "project": project,
            "date__range": (start_date, end_date),
        }

        opex_trackers = {
            "materials": MaterialCostTracker.objects.filter(
                **opex_tracker_filters, material_entity__expense_code=opex_code
            ),
            "labour": LabourCostTracker.objects.filter(
                **opex_tracker_filters, labour_entity__expense_code=opex_code
            ),
            "subcontractors": SubcontractorCostTracker.objects.filter(
                **opex_tracker_filters, subcontractor_entity__expense_code=opex_code
            ),
            "plant": PlantCostTracker.objects.filter(
                **opex_tracker_filters, plant_entity__expense_code=opex_code
            ),
            "overhead": OverheadCostTracker.objects.filter(
                **opex_tracker_filters, overhead_entity__expense_code=opex_code
            ),
        }

        opex_journal_items = JournalEntry.objects.filter(
            project=project,
            transaction_type=JournalEntry.EntryType.DEBIT,
            date__range=(start_date, end_date),
            category__in=[
                JournalEntry.Category.OVERHEAD,
                JournalEntry.Category.OTHER,
            ],
        ).order_by("-date")

        # Aggregates for Summary Rows
        total_revenue = cert_total + journal_total

        # Helper to sum trackers
        def sum_trackers(models_map, code):
            total = Decimal("0.00")
            tracker_data = {}
            sub_totals = {}

            for tracker_type, model_class in models_map.items():
                try:
                    # Use the provided helper logic for each model
                    entity_field = f"{tracker_type}_entity"
                    if tracker_type == "subcontractors":
                        entity_field = "subcontractor_entity"

                    filters = {
                        f"{entity_field}__expense_code": code,
                        "project": project,
                        "date__range": (start_date, end_date),
                    }
                    qs = model_class.objects.filter(**filters)

                    # Aggregate total
                    if tracker_type == "labour":
                        agg = qs.aggregate(t=Sum(F("amount_of_days") * F("salary")))[
                            "t"
                        ]
                    elif tracker_type == "materials":
                        agg = qs.aggregate(t=Sum(F("quantity") * F("rate")))["t"]
                    elif tracker_type == "subcontractors":
                        agg = qs.aggregate(t=Sum(F("amount_of_days") * F("rate")))["t"]
                    elif tracker_type == "plant":
                        agg = qs.aggregate(t=Sum(F("usage_hours") * F("hourly_rate")))[
                            "t"
                        ]
                    elif tracker_type == "overhead":
                        agg = qs.aggregate(t=Sum(F("amount_of_days") * F("rate")))["t"]
                    else:
                        agg = 0

                    val = Decimal(str(agg or 0))
                    total += val
                    tracker_data[tracker_type] = qs
                    sub_totals[f"{tracker_type}_total"] = val
                except Exception:
                    tracker_data[tracker_type] = []
                    sub_totals[f"{tracker_type}_total"] = Decimal("0.00")

            return {"total": total, "items": tracker_data, "sub_totals": sub_totals}

        tracker_models = {
            "materials": MaterialCostTracker,
            "labour": LabourCostTracker,
            "subcontractors": SubcontractorCostTracker,
            "plant": PlantCostTracker,
            "overhead": OverheadCostTracker,
        }

        cos_results = sum_trackers(tracker_models, cos_code)
        cos_tracker_total = cos_results["total"]
        cos_journal_total = sum(j.amount for j in cos_journal_items)
        cos_total = cos_tracker_total + cos_journal_total

        opex_results = sum_trackers(tracker_models, opex_code)
        opex_tracker_total = opex_results["total"]
        opex_journal_total = sum(j.amount for j in opex_journal_items)
        opex_total = opex_tracker_total + opex_journal_total

        context["cos_breakdown"] = {
            "trackers": cos_results,
            "journals": {"items": cos_journal_items, "total": cos_journal_total},
            "total": cos_total,
        }

        context["opex_breakdown"] = {
            "trackers": opex_results,
            "journals": {"items": opex_journal_items, "total": opex_journal_total},
            "total": opex_total,
        }

        context["revenue_breakdown"] = {
            "certificates": {
                "items": certificates,
                "total": cert_total,
                "pct": (cert_total / total_revenue * 100) if total_revenue > 0 else 0,
            },
            "journals": {
                "items": journal_entries,
                "total": journal_total,
                "pct": (journal_total / total_revenue * 100)
                if total_revenue > 0
                else 0,
            },
            "total": total_revenue,
        }

        # Final Profit Aggregates
        gross_profit = total_revenue - cos_total
        net_profit = gross_profit - opex_total

        gross_profit_pct = (
            (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        )
        net_profit_pct = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        context["gross_profit"] = {"total": gross_profit, "pct": gross_profit_pct}
        context["net_profit"] = {"total": net_profit, "pct": net_profit_pct}

        context["tab"] = "performance_report"
        context["report_name"] = "Detailed Financial Breakdown"
        context["generated_at"] = datetime.now()
        context["total_revenue"] = (
            total_revenue  # Ensure this is also available directly
        )
        return context


class IncomeStatementView(FinancialBreakdownView):
    """
    Simplified Income Statement Report. Now inherits from FinancialBreakdownView
    to provide the same high-fidelity drill-down capabilities.
    """

    template_name = "profitability/reports/financial_breakdown.html"


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
