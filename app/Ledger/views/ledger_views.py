"""Views for Ledger model."""

from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.Ledger.models import Ledger

from ..mixins import UserHasCompanyRoleMixin


class LedgerListView(UserHasCompanyRoleMixin, ListView):
    """List all ledgers for a company."""

    model = Ledger
    template_name = "ledger/ledger_list.html"
    context_object_name = "ledgers"
    paginate_by = 25

    def get_queryset(self):
        """Filter ledgers by company and apply filters."""
        company = self.get_company()
        queryset = Ledger.objects.filter(company=company).select_related("company")

        # Get filter parameters from GET request
        financial_statement = self.request.GET.get("financial_statement")
        code = self.request.GET.get("code")
        name = self.request.GET.get("name")

        # Apply filters
        if financial_statement:
            queryset = queryset.filter(financial_statement=financial_statement)

        if code:
            queryset = queryset.filter(code__icontains=code)

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context["company"] = self.company

        # Preserve filter values in context
        context["filter_financial_statement"] = self.request.GET.get(
            "financial_statement", ""
        )
        context["filter_code"] = self.request.GET.get("code", "")
        context["filter_name"] = self.request.GET.get("name", "")

        # Add financial statement choices for filter
        context["financial_statement_choices"] = [
            {"value": "", "label": "All"},
            {"value": "balance_sheet", "label": "Balance Sheet"},
            {"value": "income_statement", "label": "Income Statement"},
        ]

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
            {"title": "Ledgers", "url": None},
        ]


class LedgerCreateView(UserHasCompanyRoleMixin, CreateView):
    """Create a new ledger."""

    model = Ledger
    template_name = "ledger/ledger_form.html"
    fields = ["code", "name", "financial_statement"]
    success_url = None

    def form_valid(self, form):
        """Set company and add success message."""
        form.instance.company = self.get_company()
        messages.success(
            self.request, f"Ledger '{form.instance.name}' created successfully!"
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to ledger list."""
        return reverse_lazy(
            "ledger:ledger-list", kwargs={"company_id": self.company.pk}
        )

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context["company"] = self.company
        context["title"] = "Create Ledger"
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
            {
                "title": "Ledgers",
                "url": reverse("ledger:ledger-list", kwargs={"company_id": company.pk}),
            },
            {"title": "New Ledger", "url": None},
        ]
