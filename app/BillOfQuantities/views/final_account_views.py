from decimal import Decimal
from typing import Any

from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView

from app.BillOfQuantities.models import LineItem, PaymentCertificate
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models.projects_models import Project


class FinalAccountDetailView(UserHasGroupGenericMixin, BreadcrumbMixin, DetailView):
    model = PaymentCertificate
    template_name = "final_account/final_account_detail.html"
    context_object_name = "final_account"
    permissions = ["contractor"]
    project_slug = "project_pk"
    pk = "pk"

    def get_project(self: Any) -> Project:
        """Get the project for the current view."""
        if not hasattr(self, "project") or not self.project:
            self.project = get_object_or_404(
                Project,
                pk=self.kwargs[self.project_slug],
                account=self.request.user,
            )
        return self.project

    def get_object(self: "FinalAccountDetailView") -> PaymentCertificate:
        """Get the project for the current view."""
        if not hasattr(self, "payment_certificate") or not self.payment_certificate:
            self.payment_certificate = get_object_or_404(
                PaymentCertificate,
                pk=self.kwargs[self.pk],
                project=self.get_project(),
                is_final=True,
                project__account=self.request.user,
            )
        return self.payment_certificate

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {
                "title": "Payment Certificates",
                "url": reverse(
                    "bill_of_quantities:payment-certificate-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            },
            {
                "title": f"Final Payment Certificate: #{self.object.certificate_number}",
                "url": None,
            },
        ]

    def get_context_data(self: "FinalAccountDetailView", **kwargs):
        context = super().get_context_data(**kwargs)
        payment_certificate: PaymentCertificate = self.get_object()
        project = self.get_project()

        # Get line items from the payment certificate
        line_items_qs = LineItem.construct_payment_certificate(payment_certificate)

        # Process line items and calculate additional fields
        line_items = []
        contract_total = Decimal("0")
        final_account_total = Decimal("0")
        total_additions = Decimal("0")
        total_omissions = Decimal("0")
        total_qty_additions = Decimal("0")
        total_qty_omissions = Decimal("0")

        for line in line_items_qs:
            budgeted_qty = line.budgeted_quantity or Decimal("0")
            total_qty = line.total_qty or Decimal("0")
            total_price = line.total_price or Decimal("0")
            total_claimed = line.total_claimed or Decimal("0")

            # Calculate qty additions/omissions
            qty_addition = max(Decimal("0"), total_qty - budgeted_qty)
            qty_omission = max(Decimal("0"), budgeted_qty - total_qty)

            # Calculate amount additions/omissions
            amount_addition = max(Decimal("0"), total_claimed - total_price)
            amount_omission = max(Decimal("0"), total_price - total_claimed)

            # Calculate variance percentage
            if total_price and total_price != 0:
                variance_percent = ((total_claimed - total_price) / total_price) * 100
            else:
                variance_percent = Decimal("0")

            # Add calculated fields to line item
            line.qty_addition = qty_addition
            line.qty_omission = qty_omission
            line.amount_addition = amount_addition
            line.amount_omission = amount_omission
            line.variance_percent = variance_percent

            line_items.append(line)

            # Accumulate totals
            contract_total += total_price
            final_account_total += total_claimed
            total_additions += amount_addition
            total_omissions += amount_omission
            total_qty_additions += qty_addition
            total_qty_omissions += qty_omission

        # Calculate total variance percentage
        if contract_total and contract_total != 0:
            total_variance_percent = (
                (final_account_total - contract_total) / contract_total
            ) * 100
        else:
            total_variance_percent = Decimal("0")

        context["project"] = project
        context["line_items"] = line_items
        context["contract_total"] = contract_total
        context["final_account_total"] = final_account_total
        context["total_additions"] = total_additions
        context["total_omissions"] = total_omissions
        context["total_qty_additions"] = total_qty_additions
        context["total_qty_omissions"] = total_qty_omissions
        context["total_variance_percent"] = total_variance_percent
        return context
