"""Views for Ledger reports."""

from django.urls import reverse

from datetime import datetime
from decimal import Decimal
from typing import Any

from django.db.models import Sum
from django.http import HttpRequest, HttpResponse
from django.views.generic import TemplateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.Ledger.models import Ledger, Transaction

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

        # Get all transactions for the period
        transactions = Transaction.objects.filter(
            company=company,
            date__gte=start_date,
            date__lte=end_date,
        ).select_related("ledger")

        # Calculate revenue (credit transactions from revenue accounts)
        revenue_ledgers = Ledger.objects.filter(
            company=company,
            financial_statement=Ledger.FinancialStatement.INCOME_STATEMENT,
        ).filter(code__regex=r"^4")  # Revenue accounts starting with 4

        revenue_data = (
            transactions.filter(
                ledger__in=revenue_ledgers, type=Transaction.TransactionType.CREDIT
            )
            .values("ledger__code", "ledger__name")
            .annotate(total=Sum("amount_incl_vat"))
            .order_by("ledger__code")
        )

        total_revenue = Decimal("0")
        revenue_items = []
        for item in revenue_data:
            total_revenue += item["total"] or Decimal("0")
            revenue_items.append(
                {
                    "code": item["ledger__code"],
                    "name": item["ledger__name"],
                    "amount": item["total"] or Decimal("0"),
                }
            )

        # Calculate expenses (debit transactions from expense accounts)
        expense_ledgers = Ledger.objects.filter(
            company=company,
            financial_statement=Ledger.FinancialStatement.INCOME_STATEMENT,
        ).filter(code__regex=r"^[5-8]")  # Expense accounts starting with 5, 6, 7, or 8

        expense_data = (
            transactions.filter(
                ledger__in=expense_ledgers, type=Transaction.TransactionType.DEBIT
            )
            .values("ledger__code", "ledger__name")
            .annotate(total=Sum("amount_incl_vat"))
            .order_by("ledger__code")
        )

        total_expenses = Decimal("0")
        expense_items = []
        for item in expense_data:
            total_expenses += item["total"] or Decimal("0")
            expense_items.append(
                {
                    "code": item["ledger__code"],
                    "name": item["ledger__name"],
                    "amount": item["total"] or Decimal("0"),
                }
            )

        # Calculate net profit/loss
        net_profit = total_revenue - total_expenses

        context.update(
            {
                "revenue_items": revenue_items,
                "total_revenue": total_revenue,
                "expense_items": expense_items,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
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
