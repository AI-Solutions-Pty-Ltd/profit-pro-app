"""Mixins for Ledger app."""

from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View

from app.Account.models import Account
from app.BillOfQuantities.models import Structure
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.Ledger.forms import ProjectFilterForm, TransactionForm
from app.Ledger.models import Transaction, Vat
from app.Project.models import Company


class UserHasCompanyRoleMixin(LoginRequiredMixin, BreadcrumbMixin):
    """
    Mixin to check if user has access to a company.

    This mixin verifies that the authenticated user is associated
    with the company specified in the URL parameters.
    """

    company_url_kwarg = "company_id"
    transaction_url_kwarg = "pk"
    company: Company
    transaction: Transaction | None
    vat_view: bool = False

    def get_company(self) -> Company:
        """Get the company from URL parameters."""
        company_id = self.kwargs.get(self.company_url_kwarg)
        if not company_id:
            raise AttributeError(
                f"'{self.__class__.__name__}' must have a '{self.company_url_kwarg}' "
                "parameter in the URL"
            )
        user: Account = self.request.user  # type: ignore
        if user.is_superuser:
            company = get_object_or_404(Company, pk=company_id)
        else:
            company = get_object_or_404(Company, pk=company_id, users=user)
        self.company = company
        return company

    def get_transaction(self) -> Transaction | None:
        """Get the transaction object."""
        pk = self.kwargs.get(self.transaction_url_kwarg)
        if not pk:
            return None
        return get_object_or_404(Transaction, pk=pk, company=self.get_company())

    def get_context_data(self, **kwargs) -> dict:
        """Add context data for template."""
        try:
            context = super().get_context_data(**kwargs)
        except Exception as _:
            context = {}
        context.update(
            {
                "company": self.get_company(),
                "transaction": self.get_transaction(),
            }
        )
        return context


class TransactionFormViewMixin(UserHasCompanyRoleMixin, BreadcrumbMixin, View):
    """
    Mixin to check if user has access to a company.

    This mixin verifies that the authenticated user is associated
    with the company specified in the URL parameters.
    """

    company_url_kwarg = "company_id"
    template_name: str
    form: TransactionForm | None = None
    project_filter_form: ProjectFilterForm | None = None
    structures: QuerySet[Structure] | None = None

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Check user permissions before dispatching the view."""
        company = self.get_company()
        transaction = self.get_transaction()
        if company.vat_registered and not self.vat_view:
            if transaction:
                return redirect(
                    "ledger:transaction-update-vat",
                    company_id=company.id,
                    pk=transaction.id,
                )
            else:
                return redirect("ledger:transaction-create-vat", company_id=company.id)
        elif not company.vat_registered and self.vat_view:
            if transaction:
                return redirect(
                    "ledger:transaction-update-non-vat",
                    company_id=company.id,
                    pk=transaction.id,
                )
            else:
                return redirect(
                    "ledger:transaction-create-non-vat", company_id=company.id
                )
        return super().dispatch(request, *args, **kwargs)  # type: ignore

    def filter_form(self, request) -> dict:
        company = self.get_company()

        self.project_filter_form = ProjectFilterForm(
            data=request.GET,
            initial={"company": company},
        )
        if self.project_filter_form.is_valid():
            filter_data = self.project_filter_form.cleaned_data
        else:
            filter_data = {}

        filter_data["company"] = company
        return filter_data

    def get(self, request, company_id, pk=None, *args, **kwargs):
        """Handle GET requests - display the form."""

        filter_data = self.filter_form(request)
        self.form = TransactionForm(
            company=self.get_company(),
            instance=self.get_transaction(),
            initial=filter_data,
        )
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, company_id=None, pk=None, *args, **kwargs):
        """Handle POST requests - process form submission."""
        company = self.get_company()
        transaction = self.get_transaction()
        data = self.filter_form(request)
        data["date"] = request.POST.get("date")
        data["type"] = request.POST.get("type")
        data["ledger"] = request.POST.get("ledger")
        data["amount"] = request.POST.get("amount")
        data["vat_rate"] = request.POST.get("vat_rate")
        data["vat_mode"] = request.POST.get("vat_mode")
        self.form = TransactionForm(
            company=company,
            instance=transaction,
            data=data,
        )

        if self.form.is_valid():
            updated_transaction = self.form.save()
            messages.success(
                request,
                f"Transaction {'created' if not transaction else 'updated'} successfully!",
            )
            return HttpResponseRedirect(
                reverse(
                    "ledger:transaction-detail",
                    kwargs={"company_id": company.pk, "pk": updated_transaction.pk},
                )
            )
        else:
            messages.error(
                request,
                f"Transaction could not be {'created' if not transaction else 'updated'}.",
            )
            context = self.get_context_data()
            return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        """Add context data for template."""
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["project_filter_form"] = self.project_filter_form
        context["object"] = self.get_transaction()
        context["breadcrumbs"] = self.get_breadcrumb_items()
        context["all_vat_rates"] = Vat.objects.all()
        return context

    def get_breadcrumb_items(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation items."""
        company = self.get_company()
        transaction = self.get_transaction()
        return [
            {
                "title": "Companies",
                "url": str(reverse_lazy("project:company-list")),
            },
            {
                "title": company.name,
                "url": str(
                    reverse("project:company-detail", kwargs={"pk": company.pk})
                ),
            },
            {
                "title": "Ledgers",
                "url": str(
                    reverse_lazy(
                        "ledger:ledger-list", kwargs={"company_id": company.pk}
                    )
                ),
            },
            {
                "title": "Transactions",
                "url": str(
                    reverse_lazy(
                        "ledger:transaction-list", kwargs={"company_id": company.pk}
                    )
                ),
            },
            {
                "title": f"{'Update' if transaction else 'New'} Transaction",
                "url": None,
            },
        ]
