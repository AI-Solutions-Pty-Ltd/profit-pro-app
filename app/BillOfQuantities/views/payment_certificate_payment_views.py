"""Views for payment certificate payments."""

import json
from decimal import Decimal
from typing import Any

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import validate_email
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView, View

from app.BillOfQuantities.models.payment_certificate_models import PaymentCertificate
from app.BillOfQuantities.models.payment_certificate_payment_models import (
    PaymentCertificatePayment,
)
from app.core.Utilities.django_email_service import django_email_service
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
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


class PaymentCertificatePaymentStatementView(
    PaymentCertificatePaymentMixin, BreadcrumbMixin, View
):
    """Generate and display payment statement for a payment certificate."""

    template_name = "payments/payment_statement.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Return breadcrumbs for payment statement view."""
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects",
                url=reverse("project:portfolio-project-list"),
            ),
            BreadcrumbItem(
                title=project.name,
                url=reverse("project:project-management", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Payment Certificates",
                url=reverse(
                    "bill_of_quantities:payment-certificate-list",
                    kwargs={"project_pk": project.pk},
                ),
            ),
            BreadcrumbItem(
                title="Payment Statement",
                url=None,
            ),
        ]

    def get(self, request: HttpRequest, project_pk: int) -> HttpResponse:
        project = self.get_project()
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
            "breadcrumbs": self.get_breadcrumbs(),
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

        return render(request, self.template_name, context)


class EmailPaymentStatementView(PaymentCertificatePaymentMixin, View):
    """Email payment statement to client."""

    def post(self, request: HttpRequest, project_pk: int) -> JsonResponse:
        """Handle POST request to email payment statement."""
        # Get project for permission checking (handled by mixin)
        project = self.get_project()

        # Parse JSON body to get emails list
        try:
            data = json.loads(request.body)
            emails = data.get("emails", [])
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Invalid request format."}
            )

        if not emails:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Please provide at least one email address.",
                }
            )

        # Validate emails
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse(
                    {"success": False, "message": f"Invalid email address: {email}"}
                )

        try:
            # Generate the same data as the statement view
            all_certificates = PaymentCertificate.objects.filter(
                project=project,
                status__in=[
                    PaymentCertificate.Status.APPROVED,
                    PaymentCertificate.Status.SUBMITTED,
                ],
            ).order_by("certificate_number")

            # Get all payments for this project
            payments = PaymentCertificatePayment.objects.filter(
                project=project
            ).order_by("date")

            # Build statement entries (same logic as PaymentCertificatePaymentStatementView)
            statement_entries = []

            # Add payment certificates as debits
            for cert in all_certificates:
                if cert.current_claim_total > 0:
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
                            "balance": None,
                        }
                    )

            # Add payments as credits
            for payment in payments:
                payment_date = payment.date
                if hasattr(payment_date, "date"):
                    payment_date = payment.date.date()
                statement_entries.append(
                    {
                        "date": payment_date,
                        "type": "credit",
                        "description": f"Payment Received - Ref #PMT-{payment.pk}",
                        "debit": None,
                        "credit": payment.amount,
                        "balance": None,
                    }
                )

            # Sort and calculate balance
            statement_entries.sort(key=lambda x: x["date"])
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

            # Get the latest certificate for period info
            latest_certificate = all_certificates.last()

            context = {
                "project": project,
                "statement_entries": statement_entries,
                "payments": payments,
                "total_debits": total_debits,
                "total_credits": total_credits,
                "final_balance": running_balance,
                "payment_certificate": latest_certificate,
            }

            # Generate PDF
            from app.core.Utilities.generate_pdf import generate_pdf

            html_content = render_to_string(
                "payments/payment_statement_pdf.html", context
            )
            pdf_file = generate_pdf(html_content)

            # Create email body
            latest_date = statement_entries[-1]["date"] if statement_entries else None
            latest_date_str = (
                latest_date.strftime("%d %B %Y") if latest_date else "today"
            )

            email_body = f"""Dear Valued Client,

Please find attached the payment statement for {project.name}.

This statement shows all transactions and the current balance as of {latest_date_str}.

Should you have any questions, please don't hesitate to contact us.

Best regards,
{getattr(request.user, "get_full_name", lambda: str(request.user))() or str(request.user)}"""

            # Create PDF attachment
            pdf_attachment = ContentFile(
                pdf_file.read(),
                name=f"payment_statement_{project.name.replace(' ', '_')}.pdf",
            )

            # Send email using the email service
            success, message = django_email_service(
                to=emails,
                subject=f"Payment Statement - {project.name}",
                plain_body=email_body,
                attachments=[pdf_attachment],
                from_email=settings.DEFAULT_FROM_EMAIL,
            )

            if success:
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Payment statement sent to {len(emails)} recipient(s)",
                    }
                )
            else:
                return JsonResponse({"success": False, "message": message})

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Failed to send email: {str(e)}"}
            )


class PaymentCertificateInvoiceView(PaymentCertificatePaymentMixin, DetailView):
    """Generate and display/download invoice for a payment certificate."""

    model = PaymentCertificate
    template_name = "payments/invoice.html"
    pdf_template_name = "payments/invoice_pdf_template.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Return breadcrumbs for invoice view."""
        project = self.get_project()
        payment_certificate = self.get_object()
        return [
            BreadcrumbItem(
                title="Project Management",
                url=reverse("project:project-management", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Payment Certificates",
                url=reverse(
                    "bill_of_quantities:payment-certificate-list",
                    kwargs={"project_pk": project.pk},
                ),
            ),
            BreadcrumbItem(
                title=f"Certificate #{payment_certificate.certificate_number}",
                url=reverse(
                    "bill_of_quantities:payment-certificate-detail",
                    kwargs={"project_pk": project.pk, "pk": payment_certificate.pk},
                ),
            ),
            BreadcrumbItem(
                title="Invoice",
                url=None,
            ),
        ]

    def dispatch(self, request, *args, **kwargs):
        """Check if payment certificate is approved before allowing access."""
        obj = self.get_object()
        if obj.status != obj.Status.APPROVED:
            messages.error(
                request, "Invoice is only available for approved payment certificates."
            )
            return redirect(
                "bill_of_quantities:payment-certificate-detail",
                project_pk=obj.project.pk,
                pk=obj.pk,
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["vat_rate"] = settings.VAT_RATE
        context["payment_certificate"] = self.get_object()

        # Get the user's company (contractor company)
        user_company = None
        if self.request.user.is_authenticated and hasattr(
            self.request.user, "companies"
        ):
            user_company = self.request.user.companies.first()  # type: ignore

        # Calculate VAT amounts
        from decimal import Decimal

        vat_rate = Decimal(str(settings.VAT_RATE))

        # Check if either company or client is VAT registered
        is_vat_applicable = bool(
            user_company.vat_number
            if user_company
            else False
            or (self.get_project().client and self.get_project().client.vat_number)
        )

        if is_vat_applicable:
            # Calculate subtotal (excluding VAT)
            subtotal = self.get_object().current_claim_total / (Decimal("1") + vat_rate)
            vat_amount = self.get_object().current_claim_total - subtotal
        else:
            subtotal = self.get_object().current_claim_total
            vat_amount = Decimal("0.00")

        context["subtotal"] = subtotal
        context["vat_amount"] = vat_amount
        context["is_vat_applicable"] = is_vat_applicable
        context["user_company"] = user_company

        return context

    def render_to_response(self, context, **response_kwargs):
        """Check if PDF download is requested."""
        if self.request.GET.get("format") == "pdf":
            # Generate PDF using the template
            from django.template.loader import render_to_string

            from app.core.Utilities.generate_pdf import generate_pdf

            context["pdf"] = True

            # Render template to string
            html_content = render_to_string(str(self.pdf_template_name), context)

            # Generate PDF using the existing utility
            pdf_file = generate_pdf(html_content)

            # Return PDF response
            response = HttpResponse(pdf_file, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="invoice_{context["payment_certificate"].certificate_number}.pdf"'
            )
            return response

        return super().render_to_response(context, **response_kwargs)


class EmailPaymentCertificateView(PaymentCertificatePaymentMixin, View):
    """Email payment certificate invoice to client."""

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Return breadcrumbs for email invoice view."""
        project = self.get_project()
        payment_certificate = get_object_or_404(
            PaymentCertificate, pk=self.kwargs["pk"], project=project
        )
        return [
            BreadcrumbItem(
                title="Projects",
                url=reverse("project:project-list"),
            ),
            BreadcrumbItem(
                title=project.name,
                url=reverse("project:project-detail", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Project Management",
                url=reverse("project:project-management", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Payment Certificates",
                url=reverse(
                    "bill_of_quantities:payment-certificate-list",
                    kwargs={"project_pk": project.pk},
                ),
            ),
            BreadcrumbItem(
                title=f"Certificate #{payment_certificate.certificate_number}",
                url=reverse(
                    "bill_of_quantities:payment-certificate-detail",
                    kwargs={"project_pk": project.pk, "pk": payment_certificate.pk},
                ),
            ),
            BreadcrumbItem(
                title="Invoice",
                url=reverse(
                    "bill_of_quantities:payment-certificate-invoice",
                    kwargs={"project_pk": project.pk, "pk": payment_certificate.pk},
                ),
            ),
            BreadcrumbItem(
                title="Email Invoice",
                url=None,
            ),
        ]

    def post(self, request: HttpRequest, project_pk: int, pk: int) -> JsonResponse:
        """Handle POST request to email invoice."""
        # Get project for permission checking (handled by mixin)
        project = self.get_project()

        # Get payment certificate
        payment_certificate = get_object_or_404(
            PaymentCertificate, pk=pk, project=project
        )

        # Check if certificate is approved
        if payment_certificate.status != payment_certificate.Status.APPROVED:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Invoice is only available for approved payment certificates.",
                }
            )

        # Parse JSON body to get emails list
        try:
            data = json.loads(request.body)
            emails = data.get("emails", [])
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Invalid request format."}
            )

        if not emails:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Please provide at least one email address.",
                }
            )

        # Validate emails
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse(
                    {"success": False, "message": f"Invalid email address: {email}"}
                )

        try:
            # Generate context for invoice
            context = {
                "project": project,
                "payment_certificate": payment_certificate,
                "vat_rate": settings.VAT_RATE,
            }

            # Generate PDF
            from app.core.Utilities.generate_pdf import generate_pdf

            html_content = render_to_string("payments/invoice_html.html", context)
            pdf_file = generate_pdf(html_content)

            # Create email body
            amount_str = f"{payment_certificate.current_claim_total:,.2f}"

            email_body = f"""Dear Valued Client,

Please find attached invoice #{payment_certificate.certificate_number} for {project.name}.

Invoice Details:
- Certificate Number: #{payment_certificate.certificate_number}
- Amount: R {amount_str}

Payment should be made according to the payment terms specified in the contract.
Our banking details are included in the attached invoice.

Should you have any questions, please don't hesitate to contact us.

Best regards,
{getattr(request.user, "get_full_name", lambda: str(request.user))() or str(request.user)}"""

            # Create PDF attachment
            pdf_attachment = ContentFile(
                pdf_file.read(),
                name=f"invoice_{payment_certificate.certificate_number}_{project.name.replace(' ', '_')}.pdf",
            )

            # Send email using the email service
            success, message = django_email_service(
                to=emails,
                subject=f"Invoice #{payment_certificate.certificate_number} - {project.name}",
                plain_body=email_body,
                attachments=[pdf_attachment],
                from_email=settings.DEFAULT_FROM_EMAIL,
            )

            if success:
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Invoice #{payment_certificate.certificate_number} sent to {len(emails)} recipient(s)",
                    }
                )
            else:
                return JsonResponse({"success": False, "message": message})

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Failed to send email: {str(e)}"}
            )
