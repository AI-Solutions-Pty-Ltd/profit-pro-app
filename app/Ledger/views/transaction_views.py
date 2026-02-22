"""Views for Transaction model."""

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView

from app.core.Utilities.mixins import BreadcrumbItem
from app.Ledger.mixins import TransactionFormViewMixin, UserHasCompanyRoleMixin
from app.Ledger.models import Ledger, Transaction


class TransactionListView(UserHasCompanyRoleMixin, ListView):
    """List all transactions for a company."""

    model = Transaction
    template_name = "ledger/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 25

    def get_queryset(self):
        """Filter transactions by company."""
        company = self.get_company()
        return (
            Transaction.objects.filter(company=company)
            .select_related("debit_ledger", "credit_ledger", "bill", "vat_rate")
            .order_by("-date")
        )

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context["company"] = self.company
        context["ledgers"] = Ledger.objects.filter(company=self.company)
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        company = self.get_company()
        return [
            {
                "title": "Companies",
                "url": str(reverse_lazy("project:company-list")),
            },
            {
                "title": company.name,
                "url": reverse("project:company-detail", kwargs={"pk": company.pk}),
            },
            {"title": "Transactions", "url": None},
        ]


class TransactionDetailView(UserHasCompanyRoleMixin, DetailView):
    """Display a single transaction."""

    model = Transaction
    template_name = "ledger/transaction_detail.html"
    context_object_name = "transaction"

    def get_queryset(self):
        """Filter transactions by company."""
        company = self.get_company()
        return Transaction.objects.filter(company=company).select_related(
            "debit_ledger", "credit_ledger", "bill", "vat_rate"
        )

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context["company"] = self.company
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        company = self.get_company()
        return [
            {
                "title": "Companies",
                "url": str(reverse_lazy("project:company-list")),
            },
            {
                "title": company.name,
                "url": reverse("project:company-detail", kwargs={"pk": company.pk}),
            },
            {
                "title": "Transactions",
                "url": str(
                    reverse_lazy(
                        "ledger:transaction-list", kwargs={"company_id": company.pk}
                    )
                ),
            },
            {"title": f"Transaction {self.object.pk}", "url": None},
        ]


class TransactionCreateRouterView(UserHasCompanyRoleMixin):
    """Route create requests to VAT-aware transaction create forms."""

    def get(self, request, company_id, *args, **kwargs):
        """Redirect to appropriate create view based on company VAT registration."""
        company = self.get_company()
        target_name = (
            "ledger:transaction-create-vat"
            if company.vat_registered
            else "ledger:transaction-create-non-vat"
        )
        return HttpResponseRedirect(
            reverse_lazy(target_name, kwargs={"company_id": company_id})
        )

    def post(self, request, company_id, *args, **kwargs):
        """Redirect POST requests to the correct create form endpoint."""
        return self.get(request, company_id, *args, **kwargs)


class TransactionUpdateRouterView(UserHasCompanyRoleMixin):
    """Router that directs to appropriate update view based on company VAT status."""

    def get(self, request, company_id, pk, *args, **kwargs):
        """Redirect to appropriate update view based on company VAT registration."""
        company = self.get_company()
        target_name = (
            "ledger:transaction-update-vat"
            if company.vat_registered
            else "ledger:transaction-update-non-vat"
        )
        return HttpResponseRedirect(
            reverse_lazy(target_name, kwargs={"company_id": company_id, "pk": pk})
        )


class VatRegisteredTransactionCreateView(TransactionFormViewMixin):
    """Create transaction form for VAT-registered companies."""

    template_name = "ledger/transaction_form_vat.html"
    vat_view = True


class NonVatRegisteredTransactionCreateView(TransactionFormViewMixin):
    """Create transaction form for non-VAT registered companies."""

    template_name = "ledger/transaction_form_non_vat.html"
    vat_view = False


class VatRegisteredTransactionUpdateView(TransactionFormViewMixin):
    """Update transaction form for VAT-registered companies."""

    template_name = "ledger/transaction_form_vat.html"
    vat_view = True


class NonVatRegisteredTransactionUpdateView(TransactionFormViewMixin):
    """Update transaction form for non-VAT registered companies."""

    template_name = "ledger/transaction_form_non_vat.html"
    vat_view = False


class TransactionDeleteView(UserHasCompanyRoleMixin, DeleteView):
    """Delete a transaction."""

    model = Transaction
    template_name = "ledger/transaction_confirm_delete.html"
    context_object_name = "transaction"

    def get_queryset(self):
        """Filter transactions by company."""
        company = self.get_company()
        return Transaction.objects.filter(company=company).select_related(
            "debit_ledger", "credit_ledger", "bill", "vat_rate"
        )

    def form_valid(self, form):
        """Add success message."""
        messages.success(
            self.request, f"Transaction '{self.object.pk}' deleted successfully!"
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to transaction list."""
        return reverse_lazy(
            "ledger:transaction-list", kwargs={"company_id": self.company.pk}
        )
