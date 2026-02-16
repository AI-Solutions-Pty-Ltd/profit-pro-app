"""Views for Chart of Accounts management."""

from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.Ledger.models import Ledger
from app.Ledger.utils import create_standard_chart_of_accounts

from ..mixins import UserHasCompanyRoleMixin


class CreateStandardChartView(UserHasCompanyRoleMixin, BreadcrumbMixin, View):
    """Create standard chart of accounts for a company."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle POST request to create standard chart of accounts."""
        company = self.get_company()

        try:
            # Check if company already has ledgers
            if Ledger.objects.filter(company=company).exists():
                messages.warning(
                    request,
                    "This company already has ledgers. Standard chart was not created.",
                )
            else:
                # Create the standard chart of accounts
                ledgers = create_standard_chart_of_accounts(company)
                messages.success(
                    request,
                    f"Successfully created {len(ledgers)} standard ledgers for {company.name}.",
                )
        except Exception as e:
            messages.error(
                request, f"Error creating standard chart of accounts: {str(e)}"
            )

        return redirect(
            str(reverse_lazy("ledger:ledger-list", kwargs={"company_id": company.pk}))
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        company = self.get_company()
        return [
            {
                "title": "Companies",
                "url": "/companies/",
            },
            {"title": company.name, "url": None},
            {"title": "Ledgers", "url": None},
            {"title": "Create Standard Chart", "url": None},
        ]
