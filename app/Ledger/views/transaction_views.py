"""Views for Transaction model."""

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, View

from app.BillOfQuantities.models import Structure
from app.core.Utilities.mixins import BreadcrumbItem
from app.Ledger.forms import (
    NonVatTransactionCreateUpdateForm,
    VatTransactionCreateUpdateForm,
)
from app.Ledger.mixins import UserHasCompanyRoleMixin
from app.Ledger.models import Ledger, Transaction, Vat


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
            .select_related("ledger", "bill", "vat_rate")
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
            "ledger", "bill", "vat_rate"
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


class TransactionCreateRouterView(UserHasCompanyRoleMixin, View):
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


class TransactionUpdateRouterView(UserHasCompanyRoleMixin, View):
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


class VatRegisteredTransactionCreateView(UserHasCompanyRoleMixin, View):
    """Create transaction form for VAT-registered companies."""

    template_name = "ledger/transaction_form_vat.html"

    def get(self, request, company_id, *args, **kwargs):
        """Handle GET requests - display the form."""
        company = self.get_company()
        form = VatTransactionCreateUpdateForm(company=company)
        context = self.get_context_data(form=form, company=company)
        return render(request, self.template_name, context)

    def post(self, request, company_id, *args, **kwargs):
        """Handle POST requests - process form submission."""
        company = self.get_company()
        form = VatTransactionCreateUpdateForm(
            company=company, data=request.POST, files=request.FILES
        )

        if form.is_valid():
            transaction = form.save()
            messages.success(
                request, f"Transaction '{transaction.pk}' created successfully!"
            )
            return HttpResponseRedirect(
                reverse(
                    "ledger:transaction-detail",
                    kwargs={"company_id": company.pk, "pk": transaction.pk},
                )
            )
        else:
            messages.error(request, "Transaction could not be created.")
            context = self.get_context_data(form=form, company=company)
            return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """Add context data for template."""
        context = {}
        context["company"] = kwargs.get("company")
        context["form"] = kwargs.get("form")
        context["title"] = "Create Transaction"
        context["structures"] = Structure.objects.filter(
            project__client=context["company"]
        ).select_related("project")
        context["all_vat_rates"] = Vat.objects.all()
        return context


class NonVatRegisteredTransactionCreateView(UserHasCompanyRoleMixin, View):
    """Create transaction form for non-VAT registered companies."""

    template_name = "ledger/transaction_form_non_vat.html"

    def get(self, request, company_id, *args, **kwargs):
        """Handle GET requests - display the form."""
        company = self.get_company()
        form = NonVatTransactionCreateUpdateForm(company=company)
        context = self.get_context_data(form=form, company=company)
        return render(request, self.template_name, context)

    def post(self, request, company_id, *args, **kwargs):
        """Handle POST requests - process form submission."""
        company = self.get_company()
        form = NonVatTransactionCreateUpdateForm(
            company=company, data=request.POST, files=request.FILES
        )

        if form.is_valid():
            transaction = form.save()
            messages.success(
                request, f"Transaction '{transaction.pk}' created successfully!"
            )
            return HttpResponseRedirect(
                reverse(
                    "ledger:transaction-detail",
                    kwargs={"company_id": company.pk, "pk": transaction.pk},
                )
            )
        else:
            messages.error(request, "Transaction could not be created.")
            context = self.get_context_data(form=form, company=company)
            return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """Add context data for template."""
        context = {}
        context["company"] = kwargs.get("company")
        context["form"] = kwargs.get("form")
        context["title"] = "Create Transaction"
        context["structures"] = Structure.objects.filter(
            project__client=context["company"]
        ).select_related("project")
        return context


class VatRegisteredTransactionUpdateView(UserHasCompanyRoleMixin, View):
    """Update transaction form for VAT-registered companies."""

    template_name = "ledger/transaction_form_vat.html"

    def get_object(self, company_id, pk):
        """Get the transaction object."""
        return get_object_or_404(Transaction, pk=pk, company_id=company_id)

    def get(self, request, company_id, pk, *args, **kwargs):
        """Handle GET requests - display the form."""
        company = self.get_company()
        transaction = self.get_object(company_id, pk)
        form = VatTransactionCreateUpdateForm(company=company, instance=transaction)
        context = self.get_context_data(form=form, company=company, object=transaction)
        return render(request, self.template_name, context)

    def post(self, request, company_id, pk, *args, **kwargs):
        """Handle POST requests - process form submission."""
        company = self.get_company()
        transaction = self.get_object(company_id, pk)
        form = VatTransactionCreateUpdateForm(
            company=company,
            instance=transaction,
            data=request.POST,
        )

        if form.is_valid():
            updated_transaction = form.save()
            messages.success(
                request, f"Transaction '{updated_transaction.pk}' updated successfully!"
            )
            return HttpResponseRedirect(
                reverse(
                    "ledger:transaction-detail",
                    kwargs={"company_id": company.pk, "pk": updated_transaction.pk},
                )
            )
        else:
            messages.error(request, "Transaction could not be updated.")
            context = self.get_context_data(
                form=form, company=company, object=transaction
            )
            return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """Add context data for template."""
        context = {}
        context["company"] = kwargs.get("company")
        context["form"] = kwargs.get("form")
        context["object"] = kwargs.get("object")
        context["title"] = "Update Transaction"
        context["structures"] = Structure.objects.filter(
            project__client=context["company"]
        ).select_related("project")
        context["all_vat_rates"] = Vat.objects.all()
        return context


class NonVatRegisteredTransactionUpdateView(UserHasCompanyRoleMixin, View):
    """Update transaction form for non-VAT registered companies."""

    template_name = "ledger/transaction_form_non_vat.html"

    def get_object(self, company_id, pk):
        """Get the transaction object."""
        return get_object_or_404(Transaction, pk=pk, company_id=company_id)

    def get(self, request, company_id, pk, *args, **kwargs):
        """Handle GET requests - display the form."""
        company = self.get_company()
        transaction = self.get_object(company_id, pk)
        form = NonVatTransactionCreateUpdateForm(company=company, instance=transaction)
        context = self.get_context_data(form=form, company=company, object=transaction)
        return render(request, self.template_name, context)

    def post(self, request, company_id, pk, *args, **kwargs):
        """Handle POST requests - process form submission."""
        company = self.get_company()
        transaction = self.get_object(company_id, pk)
        form = NonVatTransactionCreateUpdateForm(
            company=company,
            instance=transaction,
            data=request.POST,
        )

        if form.is_valid():
            updated_transaction = form.save()
            messages.success(
                request, f"Transaction '{updated_transaction.pk}' updated successfully!"
            )
            return HttpResponseRedirect(
                reverse(
                    "ledger:transaction-detail",
                    kwargs={"company_id": company.pk, "pk": updated_transaction.pk},
                )
            )
        else:
            messages.error(request, "Transaction could not be updated.")
            context = self.get_context_data(
                form=form, company=company, object=transaction
            )
            return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """Add context data for template."""
        context = {}
        context["company"] = kwargs.get("company")
        context["form"] = kwargs.get("form")
        context["object"] = kwargs.get("object")
        context["title"] = "Update Transaction"
        context["structures"] = Structure.objects.filter(
            project__client=context["company"]
        ).select_related("project")
        return context


class TransactionDeleteView(UserHasCompanyRoleMixin, DeleteView):
    """Delete a transaction."""

    model = Transaction
    template_name = "ledger/transaction_confirm_delete.html"
    context_object_name = "transaction"

    def get_queryset(self):
        """Filter transactions by company."""
        company = self.get_company()
        return Transaction.objects.filter(ledger__company=company).select_related(
            "ledger", "bill", "vat_rate"
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
