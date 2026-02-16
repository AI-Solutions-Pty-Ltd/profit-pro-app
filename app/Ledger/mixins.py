"""Mixins for Ledger app."""

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from app.Account.models import Account
from app.core.Utilities.mixins import BreadcrumbMixin
from app.Ledger.models import Vat
from app.Project.models import Company


class UserHasCompanyRoleMixin(LoginRequiredMixin, BreadcrumbMixin):
    """
    Mixin to check if user has access to a company.

    This mixin verifies that the authenticated user is associated
    with the company specified in the URL parameters.
    """

    company_url_kwarg = "company_id"

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
            return get_object_or_404(Company, pk=company_id)
        return get_object_or_404(Company, pk=company_id, users=user)

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Check user permissions before dispatching the view."""
        self.company = self.get_company()
        return super().dispatch(request, *args, **kwargs)  # type: ignore

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        context["company"] = self.company
        context["all_vat_rates"] = Vat.objects.all()
        return context
