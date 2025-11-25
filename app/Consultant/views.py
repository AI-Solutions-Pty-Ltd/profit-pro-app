from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import DetailView, ListView, UpdateView

from app.BillOfQuantities.forms import PaymentCertificateFinalApprovalForm
from app.BillOfQuantities.models import PaymentCertificate
from app.BillOfQuantities.views.payment_certificate_views import LineItemDetailMixin
from app.core.Utilities.django_email_service import django_email_service
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Client, Project


class GetProjectMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    permissions = ["consultant"]

    def get_project(self) -> Project:
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            client__consultant=self.request.user,
        )


class ConsultantMixin(GetProjectMixin):
    def get_queryset(self):
        return Client.objects.filter(consultant=self.request.user)


# Create your views here.
class ClientListView(ConsultantMixin, ListView):
    model = Client
    template_name = "consultant/client_list.html"
    context_object_name = "clients"


class ClientDetailView(ConsultantMixin, DetailView):
    model = Client
    template_name = "consultant/client_detail.html"
    context_object_name = "client"

    def get_breadcrumbs(self: "ClientDetailView") -> list[BreadcrumbItem]:
        return [
            {"title": "Return to Clients", "url": reverse("consultant:client-list")},
            {"title": f"Client {self.get_object().name}", "url": None},
        ]


class PaymentCertificateFinalApprovalView(
    ConsultantMixin, LineItemDetailMixin, UpdateView
):
    """Final approval/rejection view - choose between APPROVED or REJECTED."""

    model = PaymentCertificate
    form_class = PaymentCertificateFinalApprovalForm
    template_name = "consultant/payment_certificate_final_approval.html"
    context_object_name = "payment_certificate"

    def get_breadcrumbs(
        self: "PaymentCertificateFinalApprovalView",
    ) -> list[BreadcrumbItem]:
        return [
            {"title": "Return to Clients", "url": reverse("consultant:client-list")},
            {
                "title": f"{self.get_object().project.client.name}",
                "url": reverse(
                    "consultant:client-detail",
                    kwargs={"pk": self.get_object().project.client.pk},
                ),
            },
            {
                "title": f"Payment Certificate #{self.get_object().certificate_number}",
                "url": None,
            },
        ]

    def get_queryset(self):
        return (
            PaymentCertificate.objects.filter(
                project__client__consultant=self.request.user
            )
            .select_related("project")
            .prefetch_related(
                "actual_transactions__line_item__structure",
                "actual_transactions__line_item__bill",
                "actual_transactions__line_item__package",
            )
        )

    def form_valid(self, form):
        payment_certificate = form.save(commit=False)
        payment_certificate.save()
        project = payment_certificate.project

        # Mark all transactions as claimed based on status
        if payment_certificate.status == PaymentCertificate.Status.APPROVED:
            payment_certificate.actual_transactions.update(claimed=True)
            messages.success(
                self.request,
                f"Payment Certificate #{payment_certificate.certificate_number} has been approved!",
            )
            payment_certificate.refresh_from_db()

            # Send approval email
            subject = f"Payment Certificate #{payment_certificate.certificate_number} Approved"
            context = {
                "payment_certificate": payment_certificate,
                "project": project,
            }
            html_body = render_to_string("consultant/email_approval.html", context)

            django_email_service(
                to=project.account.email,
                subject=subject,
                html_body=html_body,
                plain_body="",
            )

        else:
            payment_certificate.actual_transactions.update(
                claimed=False, approved=False
            )
            messages.warning(
                self.request,
                f"Payment Certificate #{payment_certificate.certificate_number} has been rejected.",
            )

            # Send rejection email
            subject = f"Payment Certificate #{payment_certificate.certificate_number} Rejected"
            context = {
                "payment_certificate": payment_certificate,
                "project": project,
            }
            html_body = render_to_string("consultant/email_rejection.html", context)

            django_email_service(
                to=project.account.email,
                subject=subject,
                html_body=html_body,
                plain_body="",
            )

        return redirect(
            "consultant:client-detail",
            pk=payment_certificate.project.client.pk,
        )
