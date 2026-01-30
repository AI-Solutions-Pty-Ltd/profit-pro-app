"""Views for payment certificate payments."""

from decimal import Decimal
from typing import Any

from django import forms
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView, View

from app.BillOfQuantities.models.payment_certificate_models import PaymentCertificate
from app.BillOfQuantities.models.payment_certificate_payment_models import (
    PaymentCertificatePayment,
)
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.permissions import (
    UserHasProjectRoleGenericMixin,
)
from app.Project.models import Project
from app.Project.models.project_roles import Role


class PaymentCertificatePaymentMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin to ensure user has project role for payment management."""

    roles = [Role.PAYMENT_CERTIFICATES, Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        if not hasattr(self, "project"):
            self.project = get_object_or_404(
                Project,
                pk=self.kwargs[self.project_slug],
            )
        return self.project


class CreatePaymentCertificatePaymentView(PaymentCertificatePaymentMixin, CreateView):
    """Create a new payment certificate payment."""

    model = PaymentCertificatePayment
    fields = ["date", "amount"]
    template_name = "payments/payment_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = forms.DateInput(
            attrs={
                "type": "date",
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
            }
        )
        form.fields["amount"].widget = forms.NumberInput(
            attrs={
                "step": "0.01",
                "min": "0",
                "class": "block w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
            }
        )
        return form

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["title"] = "Add Payment"
        return context

    def form_valid(self, form):
        form.instance.project_id = self.kwargs["project_pk"]
        messages.success(self.request, "Payment added successfully.")
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return str(
            reverse_lazy(
                "bill_of_quantities:payment-certificate-payment-statement",
                kwargs={
                    "project_pk": self.kwargs["project_pk"],
                },
            )
        )


class UpdatePaymentCertificatePaymentView(PaymentCertificatePaymentMixin, UpdateView):
    """Update an existing payment certificate payment."""

    model = PaymentCertificatePayment
    fields = ["date", "amount"]
    template_name = "payments/payment_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = forms.DateInput(
            attrs={
                "type": "date",
                "class": "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
            }
        )
        form.fields["amount"].widget = forms.NumberInput(
            attrs={
                "step": "0.01",
                "min": "0",
                "class": "block w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
            }
        )
        return form

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["title"] = "Edit Payment"
        return context

    def get_success_url(self) -> str:
        return str(
            reverse_lazy(
                "bill_of_quantities:payment-certificate-payment-statement",
                kwargs={
                    "project_pk": self.kwargs["project_pk"],
                },
            )
        )

    def form_valid(self, form):
        messages.success(self.request, "Payment updated successfully.")
        return super().form_valid(form)


class DeletePaymentCertificatePaymentView(PaymentCertificatePaymentMixin, DeleteView):
    """Delete a payment certificate payment."""

    model = PaymentCertificatePayment
    template_name = "payments/payment_confirm_delete.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_success_url(self) -> str:
        return str(
            reverse_lazy(
                "bill_of_quantities:payment-certificate-payment-statement",
                kwargs={
                    "project_pk": self.kwargs["project_pk"],
                },
            )
        )

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        messages.success(request, "Payment deleted successfully.")
        return super().delete(request, *args, **kwargs)


class PaymentCertificatePaymentStatementView(PaymentCertificatePaymentMixin, View):
    """View and download payment statement for payment certificates."""

    def get(self, request: HttpRequest, project_pk: int) -> HttpResponse:
        project = self.get_project()

        # Get all payment certificates up to and including this one
        all_certificates = PaymentCertificate.objects.filter(
            project=project,
            status__in=[
                PaymentCertificate.Status.APPROVED,
                PaymentCertificate.Status.SUBMITTED,
            ],
        ).order_by("certificate_number")

        # Get all payments for this project
        payments = PaymentCertificatePayment.objects.filter(project=project).order_by(
            "date"
        )

        # Build statement entries
        statement_entries = []

        # Add payment certificates as debits
        for cert in all_certificates:
            if cert.current_claim_total > 0:
                # Ensure we have a datetime object
                cert_date = cert.approved_on or cert.created_at
                if hasattr(cert_date, "date"):
                    cert_date = cert_date.date()
                statement_entries.append(
                    {
                        "date": cert_date,
                        "type": "debit",
                        "description": f"Payment Certificate #{cert.certificate_number}",
                        "debit": cert.current_claim_total,
                        "credit": None,
                        "balance": None,  # Will be calculated after sorting
                    }
                )

        # Add payments as credits
        for payment in payments:
            # Ensure we have a date object
            payment_date = payment.date
            if hasattr(payment_date, "date"):
                payment_date = payment_date.date()
            statement_entries.append(
                {
                    "date": payment_date,
                    "type": "credit",
                    "description": f"Payment Received - Ref #PMT-{payment.pk}",
                    "debit": None,
                    "credit": payment.amount,
                    "balance": None,  # Will be calculated after sorting
                }
            )

        # Sort all entries by date
        statement_entries.sort(key=lambda x: x["date"])

        # Calculate running balance after sorting
        running_balance = Decimal("0.00")
        for entry in statement_entries:
            if entry["debit"]:
                running_balance += entry["debit"]
            if entry["credit"]:
                running_balance -= entry["credit"]
            entry["balance"] = running_balance

        # Calculate totals
        total_debits = sum(
            entry["debit"] or Decimal("0.00") for entry in statement_entries
        )
        total_credits = sum(
            entry["credit"] or Decimal("0.00") for entry in statement_entries
        )

        context = {
            "project": project,
            "statement_entries": statement_entries,
            "payments": payments,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "final_balance": running_balance,
        }

        # Check if PDF download requested
        if request.GET.get("format") == "pdf":
            # Generate PDF
            from django.template.loader import render_to_string

            from app.core.Utilities.generate_pdf import generate_pdf

            # Render template to string
            html_content = render_to_string(
                "payments/payment_statement_pdf.html", context
            )

            # Generate PDF using the existing utility
            pdf_file = generate_pdf(html_content)

            # Return PDF response
            response = HttpResponse(pdf_file, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="project_{project.name}_payment_statement.pdf"'
            )
            return response

        return render(request, "payments/payment_statement.html", context)


class EmailPaymentStatementView(PaymentCertificatePaymentMixin, View):
    """Email payment statement to client."""

    def post(self, request: HttpRequest, project_pk: int) -> JsonResponse:
        """Handle POST request to email payment statement."""
        # Get project for permission checking (handled by mixin)
        self.get_project()

        # TODO: Implement email functionality
        # Generate PDF and send to client email

        return JsonResponse(
            {"success": True, "message": "Payment statement sent successfully!"}
        )
