from datetime import date
from decimal import Decimal

from django.db.models import F, Sum

from app.BillOfQuantities.models import (
    ActualTransaction,
    CashflowForecast,
    PaymentCertificate,
)
from app.Project.models import (
    JournalEntry,
    LabourCostTracker,
    MaterialCostTracker,
    OverheadCostTracker,
    PlantCostTracker,
    ProfitabilityBaseline,
    SubcontractorCostTracker,
)


class FinancialCalculationMixin:
    """Mixin to provide financial calculation methods for profitability reporting."""

    def get_baseline_assumptions(self):
        """Fetch baseline assumptions from DB or use defaults."""
        project = self.project  # type: ignore
        try:
            baseline = project.profitability_baseline
            return {
                "cost_of_sales_percent": float(baseline.cost_of_sales_percent),
                "operating_expenses_percent": float(
                    baseline.operating_expenses_percent
                ),
                "net_profit_percent": float(baseline.net_profit_percent),
            }
        except (AttributeError, ProfitabilityBaseline.DoesNotExist):
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

        this_month_start = end_date.replace(day=1)

        from app.Project.models.entity_definitions import BaseProjectEntity

        cos_code = BaseProjectEntity.ExpenseCode.COS
        opex_code = BaseProjectEntity.ExpenseCode.OPEX

        # Helper to get actuals for a period/filter
        def get_actuals(start=None, end=None):
            # 1. Revenue: CREDIT journals in range
            rev_filters = {
                "project": project,
                "transaction_type": JournalEntry.EntryType.CREDIT,
            }
            if start:
                rev_filters["date__gte"] = start
            if end:
                rev_filters["date__lte"] = end

            revenue_total = JournalEntry.objects.filter(**rev_filters).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")

            # 2. Trackers & Journals helper
            def get_tracker_and_journal_total(code):
                total = Decimal("0.00")

                # Sum Trackers
                models_map = {
                    "materials": MaterialCostTracker,
                    "labour": LabourCostTracker,
                    "subcontractors": SubcontractorCostTracker,
                    "plant": PlantCostTracker,
                    "overhead": OverheadCostTracker,
                }
                for tracker_type, model_class in models_map.items():
                    try:
                        entity_field = f"{tracker_type}_entity"
                        if tracker_type == "subcontractors":
                            entity_field = "subcontractor_entity"
                        elif tracker_type == "materials":
                            entity_field = "material_entity"

                        filters = {
                            f"{entity_field}__expense_code": code,
                            "project": project,
                        }
                        if start:
                            filters["date__gte"] = start
                        if end:
                            filters["date__lte"] = end

                        qs = model_class.objects.filter(**filters)

                        if tracker_type == "labour":
                            agg = qs.aggregate(
                                t=Sum(F("amount_of_days") * F("salary"))
                            )["t"]
                        elif tracker_type == "materials":
                            agg = qs.aggregate(t=Sum(F("quantity") * F("rate")))[
                                "t"
                            ]
                        elif tracker_type == "subcontractors":
                            agg = qs.aggregate(
                                t=Sum(F("amount_of_days") * F("rate"))
                            )["t"]
                        elif tracker_type == "plant":
                            agg = qs.aggregate(
                                t=Sum(F("usage_hours") * F("hourly_rate"))
                            )["t"]
                        elif tracker_type == "overhead":
                            agg = qs.aggregate(
                                t=Sum(F("amount_of_days") * F("rate"))
                            )["t"]
                        else:
                            agg = 0
                        total += Decimal(str(agg or 0))
                    except Exception:
                        pass

                # Sum Journals
                if code == cos_code:
                    categories = [
                        JournalEntry.Category.MATERIAL,
                        JournalEntry.Category.LABOUR,
                        JournalEntry.Category.SUBCONTRACTOR,
                        JournalEntry.Category.PLANT,
                    ]
                else:
                    categories = [
                        JournalEntry.Category.OVERHEAD,
                        JournalEntry.Category.OTHER,
                    ]

                j_filters = {
                    "project": project,
                    "transaction_type": JournalEntry.EntryType.DEBIT,
                    "category__in": categories,
                    "source_log_id__isnull": True,
                }
                if start:
                    j_filters["date__gte"] = start
                if end:
                    j_filters["date__lte"] = end

                journals = JournalEntry.objects.filter(**j_filters)
                journal_total = journals.aggregate(total=Sum("amount"))[
                    "total"
                ] or Decimal("0.00")
                return total + journal_total

            cos_total = get_tracker_and_journal_total(cos_code)
            opex_total = get_tracker_and_journal_total(opex_code)

            return {
                "revenue": revenue_total,
                "cos": cos_total,
                "opex": opex_total,
            }

        # Calculate actuals
        to_date_data = get_actuals(end=end_date)
        actual_revenue_to_date = to_date_data["revenue"]
        actual_cogs_to_date = to_date_data["cos"]
        actual_opex_to_date = to_date_data["opex"]

        this_month_data = get_actuals(start=this_month_start, end=end_date)
        actual_revenue_this_month = this_month_data["revenue"]
        actual_cogs_this_month = this_month_data["cos"]
        actual_opex_this_month = this_month_data["opex"]

        # Force Planned values to match actual
        planned_revenue_to_date = actual_revenue_to_date
        planned_revenue_this_month = actual_revenue_this_month
        planned_cogs_to_date = actual_cogs_to_date
        planned_opex_to_date = actual_opex_to_date
        planned_cogs_this_month = actual_cogs_this_month
        planned_opex_this_month = actual_opex_this_month

        forecast_revenue = CashflowForecast.objects.filter(
            project=project,
            status=CashflowForecast.Status.APPROVED,
        ).aggregate(total=Sum("forecast_value"))["total"] or Decimal("0.00")

        # Use Baseline Assumptions for forecasts and margins
        baseline = self.get_baseline_assumptions()

        # --- CALCULATIONS ---
        actual_gp_to_date = actual_revenue_to_date - actual_cogs_to_date
        planned_gp_to_date = planned_revenue_to_date - planned_cogs_to_date

        actual_gp_this_month = actual_revenue_this_month - actual_cogs_this_month
        planned_gp_this_month = planned_revenue_this_month - planned_cogs_this_month

        actual_np_to_date = actual_gp_to_date - actual_opex_to_date
        planned_np_to_date = planned_gp_to_date - planned_opex_to_date

        actual_np_this_month = actual_gp_this_month - actual_opex_this_month
        planned_np_this_month = planned_gp_this_month - planned_opex_this_month

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
                "planned_this_month": planned_revenue_this_month,
                "forecast": forecast_revenue,
            },
            "cost_of_sales": {
                "actual_to_date": actual_cogs_to_date,
                "planned_to_date": planned_cogs_to_date,
                "actual_this_month": actual_cogs_this_month,
                "planned_this_month": planned_cogs_this_month,
                "forecast": forecast_revenue
                * Decimal(str(baseline["cost_of_sales_percent"] / 100)),
            },
            "gross_profit": {
                "actual_to_date": actual_gp_to_date,
                "planned_to_date": planned_gp_to_date,
                "actual_this_month": actual_gp_this_month,
                "planned_this_month": planned_gp_this_month,
                "forecast": forecast_revenue
                * Decimal(str(1 - baseline["cost_of_sales_percent"] / 100)),
            },
            "operating_expenses": {
                "actual_to_date": actual_opex_to_date,
                "planned_to_date": planned_opex_to_date,
                "actual_this_month": actual_opex_this_month,
                "planned_this_month": planned_opex_this_month,
                "forecast": forecast_revenue
                * Decimal(str(baseline["operating_expenses_percent"] / 100)),
            },
            "net_profit": {
                "actual_to_date": actual_np_to_date,
                "planned_to_date": planned_np_to_date,
                "actual_this_month": actual_np_this_month,
                "planned_this_month": planned_np_this_month,
                "forecast": forecast_revenue
                * Decimal(str(baseline["net_profit_percent"] / 100)),
            },
            "gp_margin": {
                "actual_to_date": gp_margin_actual,
                "planned_to_date": gp_margin_planned,
                "actual_this_month": (
                    actual_gp_this_month / actual_revenue_this_month * 100
                )
                if actual_revenue_this_month > 0
                else 0,
                "forecast": baseline["cost_of_sales_percent"],
            },
            "np_margin": {
                "actual_to_date": np_margin_actual,
                "planned_to_date": np_margin_planned,
                "actual_this_month": (
                    actual_np_this_month / actual_revenue_this_month * 100
                )
                if actual_revenue_this_month > 0
                else 0,
                "forecast": baseline["net_profit_percent"],
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

        def get_m_journal_total(categories):
            """Internal helper to sum manual journals for this month."""
            return JournalEntry.objects.filter(
                project=project,
                transaction_type=JournalEntry.EntryType.DEBIT,
                source_log_id__isnull=True,
                category__in=categories,
                date__gte=this_month_start,
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        labour_tracker = get_m_total(
            LabourCostTracker, "date", ("amount_of_days", "salary")
        )
        labour_manual = get_m_journal_total([JournalEntry.Category.LABOUR])
        labour = Decimal(str(labour_tracker)) + labour_manual

        subcontractor_tracker = get_m_total(
            SubcontractorCostTracker, "date", ("amount_of_days", "rate")
        )
        subcontractor_manual = get_m_journal_total(
            [JournalEntry.Category.SUBCONTRACTOR]
        )
        subcontractor = Decimal(str(subcontractor_tracker)) + subcontractor_manual

        overhead_tracker = get_m_total(
            OverheadCostTracker, "date", ("amount_of_days", "rate")
        )
        overhead_manual = get_m_journal_total(
            [JournalEntry.Category.OVERHEAD, JournalEntry.Category.OTHER]
        )
        overhead = Decimal(str(overhead_tracker)) + overhead_manual

        mat_logs = get_m_total(MaterialCostTracker, "date", ("quantity", "rate"))
        plt_logs = get_m_total(PlantCostTracker, "date", ("usage_hours", "hourly_rate"))
        material_manual = get_m_journal_total(
            [JournalEntry.Category.MATERIAL, JournalEntry.Category.PLANT]
        )
        material = Decimal(str(mat_logs)) + Decimal(str(plt_logs)) + material_manual

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
