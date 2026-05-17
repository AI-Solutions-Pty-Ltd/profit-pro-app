"""Views for Company model."""

import json
import random
from datetime import datetime
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, QuerySet, Sum
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView

from app.Account.models import Account
from app.Account.subscription_config import Subscription
from app.core.Utilities.dates import get_previous_n_months
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Estimator.models import BOQItem
from app.Project.models import (
    Company,
    ContractualCompliance,
    OverheadCostTracker,
    Portfolio,
    Project,
)
from app.Project.production_progress.production_models import (
    DailyActivityEntry,
    ProductionPlan,
)
from app.Project.profitability.baseline.models import ProfitabilityBaseline

from .company_forms import CompanyFilterForm, CompanyForm


class CompanyMetricsMixin:
    """Mixin to calculate financial metrics for companies and projects."""

    def get_metrics_context(self, projects: QuerySet[Project]) -> dict:
        """Calculate financial metrics for a given set of projects."""
        current_date = datetime.now()

        # Baseline revenue and overheads are pure stored-field arithmetic —
        # do them in a single SQL aggregate each.
        baseline_rev_agg = BOQItem.objects.filter(project__in=projects).aggregate(
            total=Sum(F("contract_quantity") * F("contract_rate"))
        )
        total_baseline_revenue = float(baseline_rev_agg["total"] or 0)

        overheads_agg = OverheadCostTracker.objects.filter(
            project__in=projects
        ).aggregate(total=Sum(F("amount_of_days") * F("rate")))
        total_overheads = float(overheads_agg["total"] or 0)

        # Cost / progress / forecast totals depend on `baseline_new_price`,
        # a Python property that traverses spec FKs and component rates —
        # we can't aggregate it in SQL. Pull every BoQ row in ONE query with
        # the related specs prefetched, then sum in Python.
        total_baseline_cost = 0.0
        total_progress_revenue = 0.0
        total_progress_cost = 0.0
        total_forecast_revenue = 0.0
        total_forecast_cost = 0.0

        boq_items = (
            BOQItem.objects.filter(project__in=projects)
            .select_related(
                "specification",
                "labour_specification",
                "plant_specification",
                "preliminary_specification",
                "material",
                "project__estimator_assumptions",
            )
            .prefetch_related(
                "specification__spec_components__material",
                "plant_specification__components__plant_type",
            )
        )
        for item in boq_items:
            bnp = float(item.baseline_new_price or 0)
            if not bnp:
                continue
            total_baseline_cost += bnp * float(item.contract_quantity or 0)
            pq = float(item.progress_quantity or 0)
            total_progress_revenue += bnp * pq
            total_progress_cost += bnp * pq
            fq = float(item.forecast_quantity or 0)
            total_forecast_revenue += bnp * fq
            total_forecast_cost += bnp * fq

        baseline_profit = total_baseline_revenue - total_baseline_cost
        progress_profit = total_progress_revenue - total_progress_cost
        forecast_profit = total_forecast_revenue - total_forecast_cost

        # Compliance Stats
        total_compliance_items = ContractualCompliance.objects.filter(
            project__in=projects
        ).count()
        completed_compliance_items = ContractualCompliance.objects.filter(
            project__in=projects,
            status=ContractualCompliance.Status.COMPLETED,
        ).count()
        urgent_compliance_count = ContractualCompliance.objects.filter(
            project__in=projects,
            status=ContractualCompliance.Status.OVERDUE,
        ).count()

        compliance_percentage = (
            round((completed_compliance_items / total_compliance_items * 100), 1)
            if total_compliance_items > 0
            else 0
        )

        metrics: dict[str, Any] = {
            "current_date": current_date,
            "revenue": total_baseline_revenue,
            "baseline_profit": baseline_profit,
            "baseline_profit_margin": (
                (baseline_profit / total_baseline_revenue * 100)
                if total_baseline_revenue > 0
                else 0
            ),
            "progress_profit": progress_profit,
            "progress_profit_margin": (
                (progress_profit / total_progress_revenue * 100)
                if total_progress_revenue > 0
                else 0
            ),
            "forecast_profit": forecast_profit,
            "forecast_profit_margin": (
                (forecast_profit / total_forecast_revenue * 100)
                if total_forecast_revenue > 0
                else 0
            ),
            "total_overheads": total_overheads,
            "overheads_percentage": (
                (total_overheads / total_baseline_revenue * 100)
                if total_baseline_revenue > 0
                else 0
            ),
            "compliance_percentage": compliance_percentage,
            "total_compliance_items": total_compliance_items,
            "urgent_compliance_count": urgent_compliance_count,
        }

        # Profit trend data for charts
        profit_data = self._get_profit_trend_data()
        metrics.update(
            {
                "profit_labels": json.dumps(profit_data["labels"]),
                "gross_profit_percentage_data": json.dumps(
                    profit_data["gross_profit_percentages"]
                ),
                "net_profit_data": json.dumps(profit_data["net_profit_values"]),
            }
        )
        return metrics

    def _get_profit_trend_data(self) -> dict:
        """Generate 6 months of profit trend data for charts."""
        labels = [month.strftime("%b %Y") for month in get_previous_n_months(6)]
        gross_profit_percentages = [round(random.uniform(10, 30), 1) for _ in range(6)]
        net_profit_values = [
            round(random.uniform(500000, 1500000), 0) for _ in range(6)
        ]
        return {
            "labels": labels,
            "gross_profit_percentages": gross_profit_percentages,
            "net_profit_values": net_profit_values,
        }


class CompanyListView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, ListView
):
    """List all companies for the current user."""

    model: Project
    template_name = "company/company_list.html"
    context_object_name = "companies"
    paginate_by = 25
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self) -> QuerySet:
        """Filter companies to show only those the user has access to."""
        user: Account = self.request.user  # type: ignore
        return user.get_projects

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Business Dashbaord",
                "url": reverse("project:company-dashboard"),
            },
            {"title": "Companies", "url": None},
        ]


class CompanyManagementView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """Display company details and management options."""

    model = Company
    template_name = "company/company_management.html"
    context_object_name = "company"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Business Dashbaord",
                "url": reverse("project:company-dashboard"),
            },
            {
                "title": "Companies",
                "url": str(reverse_lazy("project:company-list")),
            },
            {"title": self.object.name, "url": None},
        ]

    def get_queryset(self) -> QuerySet["Project"]:
        """Filter companies to show only those the user has access to."""
        return self.request.user.get_projects  # type: ignore

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tab"] = "dashboard"
        return context


class CompanyUpdateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, UpdateView
):
    """Update a company."""

    model = Company
    form_class = CompanyForm
    template_name = "company/company_update.html"
    success_url = reverse_lazy("project:company-list")
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self) -> QuerySet:
        """Filter companies to show only those the user has access to."""
        return self.request.user.get_contractors  # type: ignore

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context["title"] = f"Update {self.object.name}"
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Home",
                "url": "/",
            },
            {
                "title": "Companies",
                "url": str(reverse_lazy("project:company-list")),
            },
            {"title": f"Update {self.object.name}", "url": None},
        ]


class CompanyDashboardView(
    SubscriptionRequiredMixin, BreadcrumbMixin, CompanyMetricsMixin, ListView
):
    """Projects dashboard showing financial metrics for Portfolio."""

    model = Project
    template_name = "company/company_dashboard.html"
    context_object_name = "projects"
    required_tiers = [Subscription.BUSINESS_MANAGEMENT]

    def get_breadcrumbs(self: "CompanyDashboardView") -> list[BreadcrumbItem]:
        return [
            {"title": "Business Dashboard", "url": None},
        ]

    def get_queryset(self: "CompanyDashboardView") -> QuerySet[Project]:
        """Get filtered projects for dashboard view."""
        # Initialize filter form with user's projects
        user: Account = self.request.user  # type: ignore
        return user.get_projects

    def get(self, request, *args, **kwargs):
        """Handle GET request and check for project redirect."""
        # Initialize filter form with user's projects
        user: Account = self.request.user  # type: ignore

        # Initialize filter form with the base queryset
        filter_form = CompanyFilterForm(self.request.GET or {}, user=user)

        if filter_form.is_valid():
            company = filter_form.cleaned_data.get("company")
            if company:
                return redirect(
                    "project:company-management",
                    pk=company.pk,
                )

        # Continue with normal GET processing
        return super().get(request, *args, **kwargs)

    def get_context_data(self: "CompanyDashboardView", **kwargs):
        """Add financial metrics to context."""
        context = super().get_context_data(**kwargs)
        user: Account = self.request.user  # type: ignore
        active_projects = self.get_queryset()

        if user.portfolio:
            portfolio = user.portfolio
        else:
            portfolio = Portfolio.objects.create()
            portfolio.users.add(user)
            user.get_projects.update(portfolio=portfolio)

        filter_form = CompanyFilterForm(
            self.request.GET or None, user=self.request.user
        )

        # Add the already-validated form to context
        context["filter_form"] = filter_form
        current_date = datetime.now()
        context["current_date"] = current_date

        # Highlights
        context["active_companies"] = (
            active_projects.values("contractor").distinct().count()
        )
        context["urgent_projects_count"] = len(
            portfolio.get_projects_requiring_urgent_intervention(current_date)
        )
        context["attention_projects_count"] = len(
            portfolio.get_projects_requiring_attention(current_date)
        )

        # Use mixin to get metrics
        metrics = self.get_metrics_context(active_projects)
        context.update(metrics)

        return context


class CompanyDetailDashboardView(
    SubscriptionRequiredMixin, BreadcrumbMixin, CompanyMetricsMixin, DetailView
):
    """Dedicated dashboard for a single company."""

    model = Company
    template_name = "company/company_detail_dashboard.html"
    context_object_name = "company"
    required_tiers = [Subscription.BUSINESS_MANAGEMENT]

    def get(self, request, *args, **kwargs):
        """Redirect to company management as detail dashboard is disabled."""
        self.object = self.get_object()
        return redirect("project:company-management", pk=self.object.pk)

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {
                "title": "Business Dashboard",
                "url": reverse("project:company-dashboard"),
            },
            {
                "title": "Companies",
                "url": reverse("project:company-list"),
            },
            {"title": self.object.name, "url": None},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.object

        # Get projects related to this company (as contractor)
        projects = Project.objects.filter(contractor=company)

        # Use mixin to get metrics
        metrics = self.get_metrics_context(projects)
        context.update(metrics)

        context["active_projects_count"] = projects.count()
        context["tab"] = "dashboard"

        return context


class BusinessSetupView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """View for business setup configuration."""

    model = Company
    template_name = "company/business_setup.html"
    context_object_name = "company"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Business Dashboard",
                "url": reverse("project:company-dashboard"),
            },
            {
                "title": "Companies",
                "url": reverse("project:company-list"),
            },
            {
                "title": self.object.name,
                "url": reverse(
                    "project:company-management", kwargs={"pk": self.object.pk}
                ),
            },
            {"title": "Business Setup", "url": None},
        ]


class CompanyReportView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    model = Project
    template_name = "company/company_report.html"
    context_object_name = "company"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    report_titles = {
        "income_statement": "Income Statement",
        "production_report": "Production Report",
        "progress_report": "Progress Report",
        "cashflow_statement": "Cashflow Statement",
        "debtors_creditors": "Debtors & Creditors",
        "profitability_risk": "Profitability Risk Report",
        "contractors_report": "Contractors Report",
    }

    def get_queryset(self) -> QuerySet[Project]:
        return self.request.user.get_projects  # type: ignore

    def dispatch(self, request, *args, **kwargs):
        report = kwargs.get("report")
        if report not in self.report_titles:
            raise Http404("Unknown report")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.kwargs["report"]
        context["tab"] = report
        context["report"] = report
        context["report_title"] = self.report_titles[report]
        context["current_date"] = datetime.now()

        context["revenue"] = 100_000_000
        context["gross_profit_margin"] = 20.0
        context["gross_profit"] = 20_000_000
        context["variable_costs"] = 12_000_000
        context["net_profit"] = 8_000_000
        context["net_profit_margin"] = 8.0
        context["forecast_profit"] = 6_500_000
        return context


class MasterDashboardDataMixin:
    """Aggregates multi-module data for Master Dashboards."""

    def get_master_context(self, projects: QuerySet[Project]) -> dict:
        """Centralized logic for Production, Baseline, Revenue, and Profitability."""
        # Use existing financial metrics as a base
        metrics = {}

        # 1. Production Metrics
        production_data = self._get_production_summary(projects)
        metrics["production"] = production_data

        # 2. Baseline Metrics (Original vs Adjusted)
        baseline_data = self._get_baseline_comparison(projects)
        metrics["baseline_comparison"] = baseline_data

        # 3. Revenue & Profitability (Re-using some logic but expanding)
        financial_data = self._get_financial_performance(projects)
        metrics["financials"] = financial_data

        # 4. Portfolio Specific: Exception List
        if projects.count() > 1:
            metrics["exceptions"] = self._get_exception_list(projects)

        # 5. Charts Data (S-Curve & Profit Trend)
        import json

        from app.Project.production_progress.utils.production_utils import (
            get_project_productivity_report_data,
        )

        project_ids = list(projects.values_list("id", flat=True))
        charts_data = get_project_productivity_report_data(project_ids)
        metrics["charts_json"] = json.dumps(charts_data.get("charts", {}))

        # 6. Compliance / Correspondence (RFIs)
        from app.SiteManagement.models import (
            RFI,
            BiWeeklyQualityReport,
            BiWeeklySafetyReport,
            Incident,
            IncidentStatus,
            NCRStatus,
            NonConformance,
            RFIStatus,
        )

        pending_rfis = RFI.objects.filter(
            project__in=projects, status=RFIStatus.OPEN, deleted=False
        ).count()

        # Quality Matters: Sum of Open Quality NCRs and Quality Reports
        open_quality_ncrs = NonConformance.objects.filter(
            project__in=projects, status=NCRStatus.OPEN, deleted=False
        ).count()
        quality_reports = BiWeeklyQualityReport.objects.filter(
            project__in=projects, deleted=False
        ).count()

        # Safety Matters: Sum of Open Incidents and Safety Reports
        open_incidents = Incident.objects.filter(
            project__in=projects, status=IncidentStatus.OPEN, deleted=False
        ).count()
        safety_reports = BiWeeklySafetyReport.objects.filter(
            project__in=projects, deleted=False
        ).count()

        metrics["compliance"] = {
            "pending_rfis": pending_rfis,
            "quality_matters": open_quality_ncrs + quality_reports,
            "safety_matters": open_incidents + safety_reports,
        }

        return metrics

    def _get_exception_list(self, projects):
        """Identifies underperforming projects."""
        exceptions = []
        for project in projects:
            # Check progress vs time (Simplified)
            plans = ProductionPlan.objects.filter(project=project, is_leaf=True)
            actual = (
                DailyActivityEntry.objects.filter(production_plan__in=plans).aggregate(
                    total=Sum("quantity")
                )["total"]
                or 0
            )
            total = plans.aggregate(total=Sum("quantity"))["total"] or 0
            pct = (actual / total * 100) if total > 0 else 100

            if pct < 30:  # Flag projects with very low progress
                exceptions.append(
                    {
                        "project": project,
                        "reason": "Critical Low Progress",
                        "severity": "high",
                        "value": f"{round(pct, 1)}%",
                    }
                )
        return exceptions

    def _get_production_summary(self, projects):
        from app.Project.production_progress.utils.production_utils import (
            get_premium_productivity_report_data,
        )

        plans = ProductionPlan.objects.filter(project__in=projects, is_leaf=True)
        total_quantity = plans.aggregate(total=Sum("quantity"))["total"] or 0
        actual_quantity = (
            DailyActivityEntry.objects.filter(production_plan__in=plans).aggregate(
                actual=Sum("quantity")
            )["actual"]
            or 0
        )
        progress_pct = (
            (actual_quantity / total_quantity * 100) if total_quantity > 0 else 0
        )

        # Calculate U/MH (Simplified for dashboard)
        total_hours = (
            DailyActivityEntry.objects.filter(production_plan__in=plans).aggregate(
                hours=Sum("hours_on_activity")
            )["hours"]
            or 0
        )
        umh = (actual_quantity / total_hours) if total_hours > 0 else 0

        # Calculate Overruns
        cost_overruns = 0
        schedule_overruns = 0
        is_portfolio = projects.count() > 1

        # Aggregate PPI/CPI for single projects
        total_ppi = 0
        total_cpi = 0

        for project in projects:
            report_data = get_premium_productivity_report_data(project.id)
            summary = report_data.get("summary", {})

            total_ppi += summary.get("ppi", 1.0)
            total_cpi += summary.get("cpi", 1.0)

            if is_portfolio:
                # Portfolio Mode: Count Projects
                if summary.get("cpi", 1.0) < 1.0:
                    cost_overruns += 1
                if summary.get("days_impact", 0) > 0:
                    schedule_overruns += 1
            else:
                # Project Mode: Count Activities
                for section in report_data.get("sections", []):
                    for bill in section.get("bills", []):
                        for plan in bill.get("plans", []):
                            if plan.get("cpi", 1.0) < 1.0:
                                cost_overruns += 1
                            if plan.get("days_affected", 0) > 0:
                                schedule_overruns += 1

        avg_ppi = total_ppi / projects.count() if projects.count() > 0 else 1.0
        avg_cpi = total_cpi / projects.count() if projects.count() > 0 else 1.0

        return {
            "progress_pct": round(progress_pct, 1),
            "plan_count": plans.count(),
            "total_quantity": total_quantity,
            "actual_quantity": actual_quantity,
            "total_hours": total_hours,
            "umh": round(umh, 2),
            "ppi": round(avg_ppi, 2),
            "cpi": round(avg_cpi, 2),
            "cost_overruns": cost_overruns,
            "schedule_overruns": schedule_overruns,
            "overrun_type": "Projects" if is_portfolio else "Activities",
            "status": "On Track" if progress_pct >= 50 else "Behind Schedule",
        }

    def _get_baseline_comparison(self, projects):
        boq_items = (
            BOQItem.objects.filter(project__in=projects)
            .select_related(
                "specification",
                "labour_specification",
                "labour_specification__crew",
                "plant_specification",
                "preliminary_specification",
            )
            .prefetch_related(
                "specification__spec_components__material",
                "plant_specification__components__plant_type",
            )
        )

        # We must iterate because these are calculated properties, not DB fields
        original_cost = 0
        original_revenue = 0

        for item in boq_items:
            qty = item.contract_quantity or 0
            rate = item.contract_rate or 0
            original_revenue += float(qty * rate)

            # For cost, we'll use a simplified version of baseline_new_price or similar
            # Since baseline_new_price is a property, we call it here
            price = item.baseline_new_price or 0
            original_cost += float(qty * price)

        # Adjusted (Includes Variations)
        adjusted_cost = original_cost * 1.05  # Mocked 5% growth for now
        adjusted_revenue = original_revenue * 1.08  # Mocked 8% growth for now

        return {
            "original_cost": original_cost,
            "original_revenue": original_revenue,
            "adjusted_cost": adjusted_cost,
            "adjusted_revenue": adjusted_revenue,
            "revenue_growth": adjusted_revenue - original_revenue,
            "cost_growth": adjusted_cost - original_cost,
            "growth_pct": round(((adjusted_revenue / original_revenue - 1) * 100), 1)
            if original_revenue > 0
            else 0,
        }

    def _get_financial_performance(self, projects):
        """Aggregates financial performance metrics from Baselines and Actual Costs."""
        from decimal import Decimal

        from django.db.models import F, Sum

        from app.BillOfQuantities.models import ActualTransaction, PaymentCertificate
        from app.Project.models import (
            JournalEntry,
            LabourCostTracker,
            MaterialCostTracker,
            OverheadCostTracker,
            PlantCostTracker,
            SubcontractorCostTracker,
        )
        from app.Project.models.entity_definitions import BaseProjectEntity

        # 1. Baseline Ratios (Averages if portfolio)
        baselines = ProfitabilityBaseline.objects.filter(project__in=projects)

        avg_gross_margin = (
            baselines.aggregate(avg=Sum("cost_of_sales_percent"))["avg"] or 0
        )
        if baselines.count() > 0:
            avg_gross_margin = avg_gross_margin / baselines.count()

        avg_opex_ratio = (
            baselines.aggregate(avg=Sum("operating_expenses_percent"))["avg"] or 0
        )
        if baselines.count() > 0:
            avg_opex_ratio = avg_opex_ratio / baselines.count()

        avg_net_margin = baselines.aggregate(avg=Sum("net_profit_percent"))["avg"] or 0
        if baselines.count() > 0:
            avg_net_margin = avg_net_margin / baselines.count()

        # 2. Actual Revenue & Cost (Financial Performance Overview Logic)

        # Certified Revenue from Payment Certificates
        certified_revenue = ActualTransaction.objects.filter(
            payment_certificate__project__in=projects,
            payment_certificate__status__in=[
                PaymentCertificate.Status.APPROVED,
                PaymentCertificate.Status.SIGNATORIES_APPROVED,
            ],
            approved=True,
        ).aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")
        certified_revenue = float(certified_revenue)

        # Revenue from BoQ Progress (for pending/remaining calculations)
        revenue_agg = BOQItem.objects.filter(project__in=projects).aggregate(
            total=Sum(F("contract_quantity") * F("contract_rate")),
        )
        total_revenue = float(revenue_agg["total"] or 0)
        remaining_revenue = total_revenue - certified_revenue

        # Costs from Trackers & Journals (COS and OPEX)
        cos_code = BaseProjectEntity.ExpenseCode.COS
        opex_code = BaseProjectEntity.ExpenseCode.OPEX

        def get_tracker_sum(code):
            mat = (
                MaterialCostTracker.objects.filter(
                    project__in=projects, material_entity__expense_code=code
                ).aggregate(total=Sum(F("quantity") * F("rate")))["total"]
                or 0
            )
            lab = (
                LabourCostTracker.objects.filter(
                    project__in=projects, labour_entity__expense_code=code
                ).aggregate(total=Sum(F("amount_of_days") * F("salary")))["total"]
                or 0
            )
            sub = (
                SubcontractorCostTracker.objects.filter(
                    project__in=projects, subcontractor_entity__expense_code=code
                ).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"]
                or 0
            )
            plt = (
                PlantCostTracker.objects.filter(
                    project__in=projects, plant_entity__expense_code=code
                ).aggregate(total=Sum(F("usage_hours") * F("hourly_rate")))["total"]
                or 0
            )
            ovh = (
                OverheadCostTracker.objects.filter(
                    project__in=projects, overhead_entity__expense_code=code
                ).aggregate(total=Sum(F("amount_of_days") * F("rate")))["total"]
                or 0
            )

            if code == cos_code:
                cats = [
                    JournalEntry.Category.MATERIAL,
                    JournalEntry.Category.LABOUR,
                    JournalEntry.Category.SUBCONTRACTOR,
                    JournalEntry.Category.PLANT,
                ]
            else:
                cats = [JournalEntry.Category.OVERHEAD, JournalEntry.Category.OTHER]

            jou = (
                JournalEntry.objects.filter(
                    project__in=projects,
                    transaction_type=JournalEntry.EntryType.DEBIT,
                    source_log_id__isnull=True,
                    category__in=cats,
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )

            return (
                float(mat)
                + float(lab)
                + float(sub)
                + float(plt)
                + float(ovh)
                + float(jou)
            )

        cos_total = get_tracker_sum(cos_code)
        opex_total = get_tracker_sum(opex_code)
        actual_costs = cos_total + opex_total

        # Preliminaries (Aggregated from BoQ - Note: Financial Performance Overview does not have a "Preliminaries" specific metric)
        prelims_agg = BOQItem.objects.filter(
            project__in=projects, preliminary_specification__isnull=False
        ).aggregate(total=Sum(F("contract_quantity") * F("contract_rate")))
        preliminaries = float(prelims_agg["total"] or 0)

        # 3. Profitability Calculations
        gross_profit = certified_revenue - cos_total
        net_profit = gross_profit - opex_total

        margin = (net_profit / certified_revenue * 100) if certified_revenue > 0 else 0
        gross_margin_actual = (
            (gross_profit / certified_revenue * 100) if certified_revenue > 0 else 0
        )
        variance = margin - float(avg_net_margin)

        # Forecast Profit (Lighthouse value)
        forecast_revenue = total_revenue
        forecast_cost = actual_costs + (
            remaining_revenue * (1 - float(avg_net_margin) / 100)
        )
        forecast_profit = forecast_revenue - forecast_cost

        return {
            "net_profit": net_profit,
            "gross_profit": gross_profit,
            "preliminaries": preliminaries,
            "forecast_profit": forecast_profit,
            "margin": round(margin, 1),
            "variance": round(variance, 1),
            "gross_margin": round(gross_margin_actual, 1),
            "opex_ratio": round(avg_opex_ratio, 1),
            "certified_revenue": certified_revenue,
            "pending_revenue": total_revenue * 0.05,  # Placeholder for pending claims
            "remaining_revenue": remaining_revenue,
            "margin_trend": [10.2, 11.5, 11.0, 12.8, round(margin, 1)],
            "period_labels": ["Jan", "Feb", "Mar", "Apr", "May"],
            "revenue_trend": [
                100000,
                250000,
                220000,
                180000,
                150000,
                certified_revenue,
            ],
            "profit_trend": [5000, 15000, 10000, 18000, 12000, net_profit],
        }


class MasterProjectDashboardView(
    SubscriptionRequiredMixin,
    LoginRequiredMixin,
    BreadcrumbMixin,
    MasterDashboardDataMixin,
    DetailView,
):
    """Command Center Dashboard for a single project."""

    model = Project
    template_name = "company/master_project_dashboard.html"
    context_object_name = "project"
    required_tiers = [Subscription.BUSINESS_MANAGEMENT]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        context.update(self.get_master_context(Project.objects.filter(pk=project.pk)))
        context["tab"] = "master_dashboard"
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {
                "title": "Business Dashboard",
                "url": reverse("project:company-dashboard"),
            },
            {"title": self.object.name, "url": None},
            {"title": "Project Dashboard", "url": None},
        ]


class MasterPortfolioDashboardView(
    SubscriptionRequiredMixin,
    LoginRequiredMixin,
    BreadcrumbMixin,
    MasterDashboardDataMixin,
    ListView,
):
    """Executive Command Center for the entire portfolio."""

    model = Project
    template_name = "company/master_portfolio_dashboard.html"
    context_object_name = "projects"
    required_tiers = [Subscription.BUSINESS_MANAGEMENT]

    def get_queryset(self):
        return self.request.user.get_projects

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = self.get_queryset()
        context.update(self.get_master_context(projects))
        context["tab"] = "portfolio_master"
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {
                "title": "Portfolio Dashboard",
                "url": reverse("project:company-dashboard"),
            },
            {"title": "Portfolio Dashboard", "url": None},
        ]
