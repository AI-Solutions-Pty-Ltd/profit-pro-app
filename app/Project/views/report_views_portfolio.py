"""Portfolio Report Views for Compliance, Impact, and Risk Reports."""

from decimal import Decimal
from typing import Any

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.views.generic import TemplateView

from app.Account.models import Account
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import (
    AdministrativeCompliance,
    ContractualCompliance,
    FinalAccountCompliance,
    Portfolio,
    Project,
    ProjectImpact,
    Risk,
)


class PortfolioReportMixin(UserHasGroupGenericMixin, BreadcrumbMixin, TemplateView):
    """Base mixin for portfolio reports."""

    permissions = ["consultant", "contractor"]

    def get_portfolio(self) -> Portfolio:
        """Get the current user's portfolio."""
        user: Account = self.request.user  # type: ignore
        if not user.portfolio:
            new_portfolio = Portfolio.objects.create()
            new_portfolio.users.add(user)
            user.refresh_from_db()
        return user.portfolio  # type: ignore

    def get_active_projects(self) -> list[Project]:
        """Get active projects for the current user."""
        return list(
            Project.objects.filter(
                account=self.request.user,
                status=Project.Status.ACTIVE,
            ).order_by("name")
        )


class ComplianceReportView(PortfolioReportMixin):
    """Portfolio Compliance Report covering Contractual, Administrative, Final Account."""

    template_name = "portfolio/reports/compliance_report.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {"title": "Portfolio", "url": "/"},
            {"title": "Reports", "url": None},
            {"title": "Compliance Report", "url": None},
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        portfolio = self.get_portfolio()
        projects = self.get_active_projects()

        # Get filter parameters
        party_filter = self.request.GET.get("party", "")  # contractor or consultant

        # Build report data per project
        report_data = []
        for project in projects:
            # Get responsible party filter
            party_q = Q()
            if party_filter:
                party_q = Q(responsible_party__groups__name__iexact=party_filter)

            # Contractual Compliance stats
            contractual_items = ContractualCompliance.objects.filter(
                project=project, deleted=False
            ).filter(party_q)
            contractual_total = contractual_items.count()
            contractual_completed = contractual_items.filter(
                status=ContractualCompliance.Status.COMPLETED
            ).count()
            contractual_overdue = contractual_items.filter(
                status=ContractualCompliance.Status.OVERDUE
            ).count()
            contractual_pct = (
                round(contractual_completed / contractual_total * 100, 1)
                if contractual_total > 0
                else 0
            )

            # Administrative Compliance stats
            admin_items = AdministrativeCompliance.objects.filter(
                project=project, deleted=False
            ).filter(party_q)
            admin_total = admin_items.count()
            admin_completed = admin_items.filter(
                status=AdministrativeCompliance.Status.APPROVED
            ).count()
            admin_overdue = admin_items.filter(
                status=AdministrativeCompliance.Status.OVERDUE
            ).count()
            admin_pct = (
                round(admin_completed / admin_total * 100, 1) if admin_total > 0 else 0
            )

            # Final Account Compliance stats
            final_items = FinalAccountCompliance.objects.filter(
                project=project, deleted=False
            ).filter(party_q)
            final_total = final_items.count()
            final_completed = final_items.filter(
                status=FinalAccountCompliance.Status.APPROVED
            ).count()
            final_pct = (
                round(final_completed / final_total * 100, 1) if final_total > 0 else 0
            )

            # Overall compliance
            total_items = contractual_total + admin_total + final_total
            total_completed = contractual_completed + admin_completed + final_completed
            overall_pct = (
                round(total_completed / total_items * 100, 1) if total_items > 0 else 0
            )

            report_data.append(
                {
                    "project": project,
                    "contractual": {
                        "total": contractual_total,
                        "completed": contractual_completed,
                        "overdue": contractual_overdue,
                        "percentage": contractual_pct,
                    },
                    "administrative": {
                        "total": admin_total,
                        "completed": admin_completed,
                        "overdue": admin_overdue,
                        "percentage": admin_pct,
                    },
                    "final_account": {
                        "total": final_total,
                        "completed": final_completed,
                        "percentage": final_pct,
                    },
                    "overall_percentage": overall_pct,
                    "total_overdue": contractual_overdue + admin_overdue,
                }
            )

        # Calculate portfolio totals
        total_contractual = sum(r["contractual"]["total"] for r in report_data)
        total_admin = sum(r["administrative"]["total"] for r in report_data)
        total_final = sum(r["final_account"]["total"] for r in report_data)
        completed_contractual = sum(r["contractual"]["completed"] for r in report_data)
        completed_admin = sum(r["administrative"]["completed"] for r in report_data)
        completed_final = sum(r["final_account"]["completed"] for r in report_data)

        context["report_data"] = report_data
        context["portfolio"] = portfolio
        context["party_filter"] = party_filter
        context["summary"] = {
            "contractual_pct": (
                round(completed_contractual / total_contractual * 100, 1)
                if total_contractual > 0
                else 0
            ),
            "admin_pct": (
                round(completed_admin / total_admin * 100, 1) if total_admin > 0 else 0
            ),
            "final_pct": (
                round(completed_final / total_final * 100, 1) if total_final > 0 else 0
            ),
            "total_overdue": sum(r["total_overdue"] for r in report_data),
        }

        return context


class ImpactReportView(PortfolioReportMixin):
    """Portfolio Impact Report covering Jobs, Poverty, Local Subcontracts, Local Spend, ROI."""

    template_name = "portfolio/reports/impact_report.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {"title": "Portfolio", "url": "/"},
            {"title": "Reports", "url": None},
            {"title": "Impact Report", "url": None},
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        portfolio = self.get_portfolio()
        projects = self.get_active_projects()

        # Get filter parameters
        demographic_filter = self.request.GET.get("demographic", "")
        locality_filter = self.request.GET.get("locality", "")

        # Build report data per project
        report_data = []
        for project in projects:
            # Build filter for impacts
            impact_q = Q(project=project, deleted=False)
            if demographic_filter:
                impact_q &= Q(demographic=demographic_filter)
            if locality_filter:
                impact_q &= Q(locality=locality_filter)

            impacts = ProjectImpact.objects.filter(impact_q)

            # Aggregate impact data
            aggregated = impacts.aggregate(
                total_jobs_created=Coalesce(Sum("jobs_created"), 0),
                total_jobs_retained=Coalesce(Sum("jobs_retained"), 0),
                total_poverty_beneficiaries=Coalesce(Sum("poverty_beneficiaries"), 0),
                total_poverty_spend=Coalesce(Sum("poverty_spend"), Decimal("0.00")),
                total_local_subcontracts=Coalesce(Sum("local_subcontract_count"), 0),
                total_local_subcontract_value=Coalesce(
                    Sum("local_subcontract_value"), Decimal("0.00")
                ),
                total_local_spend=Coalesce(Sum("local_spend_amount"), Decimal("0.00")),
                total_investment=Coalesce(Sum("investment_amount"), Decimal("0.00")),
                total_return=Coalesce(Sum("return_amount"), Decimal("0.00")),
            )

            # Calculate ROI
            roi = None
            if aggregated["total_investment"] > 0:
                roi = (
                    (aggregated["total_return"] - aggregated["total_investment"])
                    / aggregated["total_investment"]
                    * 100
                )

            report_data.append(
                {
                    "project": project,
                    "jobs_created": aggregated["total_jobs_created"],
                    "jobs_retained": aggregated["total_jobs_retained"],
                    "total_jobs": (
                        aggregated["total_jobs_created"]
                        + aggregated["total_jobs_retained"]
                    ),
                    "poverty_beneficiaries": aggregated["total_poverty_beneficiaries"],
                    "poverty_spend": aggregated["total_poverty_spend"],
                    "local_subcontracts": aggregated["total_local_subcontracts"],
                    "local_subcontract_value": aggregated[
                        "total_local_subcontract_value"
                    ],
                    "local_spend": aggregated["total_local_spend"],
                    "investment": aggregated["total_investment"],
                    "return_amount": aggregated["total_return"],
                    "roi": roi,
                }
            )

        # Calculate portfolio totals
        context["report_data"] = report_data
        context["portfolio"] = portfolio
        context["demographic_filter"] = demographic_filter
        context["locality_filter"] = locality_filter
        context["demographic_choices"] = ProjectImpact.Demographic.choices
        context["locality_choices"] = ProjectImpact.Locality.choices
        context["summary"] = {
            "total_jobs": sum(r["total_jobs"] for r in report_data),
            "total_poverty_beneficiaries": sum(
                r["poverty_beneficiaries"] for r in report_data
            ),
            "total_local_subcontracts": sum(
                r["local_subcontracts"] for r in report_data
            ),
            "total_local_spend": sum(r["local_spend"] for r in report_data),
        }

        return context


class RiskReportView(PortfolioReportMixin):
    """Portfolio Risk Report covering Time Impact and Cost Impact."""

    template_name = "portfolio/reports/risk_report.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {"title": "Portfolio", "url": "/"},
            {"title": "Reports", "url": None},
            {"title": "Risk Report", "url": None},
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        portfolio = self.get_portfolio()
        projects = self.get_active_projects()

        # Get filter parameters
        category_filter = self.request.GET.get("category", "")

        # Build report data per project
        report_data = []
        for project in projects:
            # Build filter for risks
            risk_q = Q(project=project, deleted=False, is_active=True)
            if category_filter:
                risk_q &= Q(category=category_filter)

            risks = Risk.objects.filter(risk_q)

            # Aggregate risk data
            risk_count = risks.count()
            total_cost_impact = risks.aggregate(
                total=Coalesce(Sum("cost_impact"), Decimal("0.00"))
            )["total"]
            estimated_cost_impact = sum(r.estimated_cost_impact for r in risks)

            # Calculate time impact
            total_time_days = sum(r.time_impact_days or 0 for r in risks)
            estimated_time_days = sum(
                float(r.estimated_time_impact_days or 0) for r in risks
            )

            # Risk breakdown by category
            category_breakdown = (
                risks.values("category").annotate(count=Count("id")).order_by("-count")
            )

            report_data.append(
                {
                    "project": project,
                    "risk_count": risk_count,
                    "total_cost_impact": total_cost_impact,
                    "estimated_cost_impact": estimated_cost_impact,
                    "total_time_days": total_time_days,
                    "estimated_time_days": round(estimated_time_days, 1),
                    "category_breakdown": list(category_breakdown),
                }
            )

        # Calculate portfolio totals
        context["report_data"] = report_data
        context["portfolio"] = portfolio
        context["category_filter"] = category_filter
        context["category_choices"] = Risk.RiskCategory.choices
        context["summary"] = {
            "total_risks": sum(r["risk_count"] for r in report_data),
            "total_cost_impact": sum(r["total_cost_impact"] for r in report_data),
            "estimated_cost_impact": sum(
                r["estimated_cost_impact"] for r in report_data
            ),
            "total_time_days": sum(r["total_time_days"] for r in report_data),
            "estimated_time_days": round(
                sum(r["estimated_time_days"] for r in report_data), 1
            ),
        }

        return context
