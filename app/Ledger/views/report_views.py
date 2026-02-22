"""Views for Ledger reports."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from django.db.models import Q, Sum
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views.generic import TemplateView

from app.core.Utilities.mixins import BreadcrumbItem
from app.Ledger.models import FinancialStatement, Ledger, Transaction

from ..mixins import UserHasCompanyRoleMixin


class IncomeStatementView(UserHasCompanyRoleMixin, TemplateView):
    """View and generate income statement reports."""

    template_name = "ledger/income_statement.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Get context data for the income statement."""
        context = super().get_context_data(**kwargs)
        company = self.get_company()
        context["company"] = company

        # Get date range from query parameters or use defaults
        start_date_str = self.request.GET.get("start_date")
        end_date_str = self.request.GET.get("end_date")

        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        else:
            start_date = (
                datetime.now().date().replace(day=1)
            )  # First day of current month

        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            end_date = datetime.now().date()  # Today

        context["start_date"] = start_date
        context["end_date"] = end_date
        context["start_date_str"] = start_date_str or start_date.strftime("%Y-%m-%d")
        context["end_date_str"] = end_date_str or end_date.strftime("%Y-%m-%d")

        # Get Income Statement financial statement
        income_statement_fs = FinancialStatement.objects.filter(
            name="Income Statement"
        ).first()

        if not income_statement_fs:
            # If no Income Statement found, return empty data
            context.update(
                {
                    "revenue_items": [],
                    "expense_items": [],
                    "total_revenue": Decimal("0"),
                    "total_expenses": Decimal("0"),
                    "net_profit": Decimal("0"),
                }
            )
            return context

        # Get all ledgers for Income Statement
        income_statement_ledgers = Ledger.objects.filter(
            company=company,
            financial_statement=income_statement_fs,
        ).order_by("code")

        # Get all transactions for the period
        transactions = (
            Transaction.objects.filter(
                company=company,
                date__gte=start_date,
                date__lte=end_date,
            )
            .filter(
                Q(credit_ledger__in=income_statement_ledgers)
                | Q(debit_ledger__in=income_statement_ledgers)
            )
            .select_related("credit_ledger", "debit_ledger")
        )

        # Calculate totals for each ledger
        income_statement_items = []
        total_sum = Decimal("0")

        for ledger in income_statement_ledgers:
            # Sum all credit transactions for this ledger
            credit_total = transactions.filter(
                credit_ledger=ledger,
            ).aggregate(total=Sum("amount_excl_vat"))["total"] or Decimal("0")

            # Sum all debit transactions for this ledger
            debit_total = transactions.filter(
                debit_ledger=ledger,
            ).aggregate(total=Sum("amount_excl_vat"))["total"] or Decimal("0")

            net_amount = debit_total - credit_total

            if net_amount != 0:  # Only show ledgers with activity
                income_statement_items.append(
                    {
                        "code": ledger.code,
                        "name": ledger.name,
                        "amount": net_amount,
                    }
                )
                total_sum += net_amount

        context.update(
            {
                "income_statement_items": income_statement_items,
                "total_sum": total_sum,
                "has_transactions": transactions.exists(),
            }
        )

        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        company = self.get_company()
        return [
            {
                "title": "Companies",
                "url": reverse("project:company-list"),
            },
            {
                "title": company.name,
                "url": reverse("project:company-detail", kwargs={"pk": company.pk}),
            },
            {"title": "Income Statement", "url": None},
        ]

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle GET requests."""
        company = self.get_company()
        self.company = company
        return super().get(request, *args, **kwargs)
