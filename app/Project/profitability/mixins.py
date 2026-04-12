from datetime import date
from decimal import Decimal

from django.db.models import F, Sum

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
    SubcontractorCostTracker,
)


class FinancialCalculationMixin:
    """Mixin to provide financial calculation methods for profitability reporting."""

    def get_baseline_assumptions(self):
        """Hardcoded baseline assumptions."""
        return {
            "cost_of_sales_percent": 60.0,
            "operating_expenses_percent": 12.0,
            "net_profit_percent": 28.0,
        }

    def get_financial_table_data(self, start_date=None, end_date=None):
        """Calculate values for the financial performance table."""
        project = self.project  # type: ignore

        if not end_date:
            end_date = date.today()

        # --- REVENUE ---
        # Sum of actual transactions in APPROVED certificates up to end_date
        actual_revenue_to_date = ActualTransaction.objects.filter(
            line_item__project=project,
            payment_certificate__status=PaymentCertificate.Status.APPROVED,
            payment_certificate__approved_on__date__lte=end_date,
        ).aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")

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

        # --- COST CALCULATIONS (SEGMENTED BY COS/OPEX) ---
        from app.Project.models.entity_definitions import BaseProjectEntity

        cos = BaseProjectEntity.ExpenseCode.COS
        opex = BaseProjectEntity.ExpenseCode.OPEX

        def get_tracker_totals(start=None, end=None, code=cos):
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
            return (
                Decimal(str(mat))
                + Decimal(str(lab))
                + Decimal(str(sub))
                + Decimal(str(plt))
                + Decimal(str(ovh))
            )

        # 1. Totals to Date
        actual_cogs_to_date = get_tracker_totals(end=end_date, code=cos)
        actual_opex_trackers_to_date = get_tracker_totals(end=end_date, code=opex)

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
        actual_cogs_this_month = get_tracker_totals(start=this_month_start, code=cos)
        actual_opex_trackers_month = get_tracker_totals(
            start=this_month_start, code=opex
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

    def get_monthly_category_summaries(self):
        """Calculate monthly totals for each cost category and high-level performace."""
        project = self.project  # type: ignore
        this_month_start = date.today().replace(day=1)

        # Helper to get monthly total for a category
        def get_m_total(model_class, date_field, amount_fields):
            filters = {"project": project, f"{date_field}__gte": this_month_start}
            if isinstance(amount_fields, tuple):
                return (
                    model_class.objects.filter(**filters).aggregate(
                        total=Sum(F(amount_fields[0]) * F(amount_fields[1]))
                    )["total"]
                    or 0
                )
            else:
                return (
                    model_class.objects.filter(**filters).aggregate(
                        total=Sum(amount_fields)
                    )["total"]
                    or 0
                )

        labour = get_m_total(LabourCostTracker, "date", ("amount_of_days", "salary"))
        subcontractor = get_m_total(
            SubcontractorCostTracker, "date", ("amount_of_days", "rate")
        )
        overhead = get_m_total(OverheadCostTracker, "date", ("amount_of_days", "rate"))

        mat_logs = get_m_total(MaterialCostTracker, "date", ("quantity", "rate"))
        plt_logs = get_m_total(PlantCostTracker, "date", ("usage_hours", "hourly_rate"))
        material = mat_logs + plt_logs

        total_expense = labour + subcontractor + overhead + material

        # Revenue this month
        revenue = ActualTransaction.objects.filter(
            line_item__project=project,
            payment_certificate__status=PaymentCertificate.Status.APPROVED,
            payment_certificate__approved_on__gte=this_month_start,
        ).aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")

        profit = revenue - Decimal(str(total_expense))
        margin = (profit / revenue * 100) if revenue > 0 else 0

        return {
            "labour": labour,
            "subcontractor": subcontractor,
            "overhead": overhead,
            "material": material,
            "total_expense": total_expense,
            "revenue": revenue,
            "profit": profit,
            "margin": margin,
        }
