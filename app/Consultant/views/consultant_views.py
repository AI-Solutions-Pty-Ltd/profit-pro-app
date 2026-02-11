"""Consultant views
User is a consultant and is approving/rejecting payment certificates
on behalf of their clients.

"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import (
    DetailView,
    ListView,
    UpdateView,
    View,
)

from app.Account.models import Account
from app.BillOfQuantities.forms import PaymentCertificateFinalApprovalForm
from app.BillOfQuantities.models import PaymentCertificate
from app.BillOfQuantities.views.payment_certificate_views import LineItemDetailMixin
from app.Consultant.forms import PaymentCertificateApprovedDateForm
from app.Consultant.views.mixins import ConsultantMixin, PaymentCertMixin
from app.core.Utilities.django_email_service import django_email_service
from app.core.Utilities.mixins import BreadcrumbItem
from app.core.Utilities.permissions import (
    UserHasGroupGenericMixin,
)
from app.Project.forms import ClientUserInviteForm
from app.Project.models import Company


class ClientListView(ConsultantMixin, ListView):
    model = Company
    template_name = "consultant/client_list.html"
    context_object_name = "clients"


class ClientDetailView(ConsultantMixin, DetailView):
    model = Company
    template_name = "consultant/client_detail.html"
    context_object_name = "client"

    def get_breadcrumbs(self: "ClientDetailView") -> list[BreadcrumbItem]:
        return [
            {
                "title": "Return to Clients",
                "url": reverse(
                    "client:consultant:client-list",
                ),
            },
            {"title": f"Client {self.get_object().name}", "url": None},
        ]


class ClientUserListView(UserHasGroupGenericMixin, View):
    """List all users for a client."""

    permissions_required = "consultant"
    template_name = "consultant/client_user_list.html"

    def get_breadcrumbs(self, client: Company) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=client.name,
                url=reverse(
                    "client:consultant:client-detail", kwargs={"pk": client.pk}
                ),
            ),
            BreadcrumbItem(title="Users", url=None),
        ]

    def get(self, request, pk, *args, **kwargs):
        """Display the list of users for the client."""
        client = get_object_or_404(Company, pk=pk)
        users = client.users.all()

        context = {
            "client": client,
            "users": users,
            "breadcrumbs": self.get_breadcrumbs(client),
        }
        return render(request, self.template_name, context)


class ClientInviteUserView(UserHasGroupGenericMixin, View):
    """Invite a user to a client."""

    permissions_required = "consultant"
    template_name = "client/client_invite_user.html"
    client_added_email_template = "client/client_added_email.html"
    password_reset_email_template = "client/password_reset_email.html"

    def get_breadcrumbs(self, client: Company) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=client.name,
                url=reverse(
                    "client:consultant:client-detail", kwargs={"pk": client.pk}
                ),
            ),
            BreadcrumbItem(title=f"Invite User to {client.name}", url=None),
        ]

    def get(self, request, pk, user_pk, *args, **kwargs):
        """Display the invite user form."""
        client = get_object_or_404(Company, pk=pk)
        form = ClientUserInviteForm()
        context = {
            "form": form,
            "client": client,
            "breadcrumbs": self.get_breadcrumbs(client),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Process the invite user form."""
        form = ClientUserInviteForm(request.POST)
        client = get_object_or_404(Company, pk=kwargs["pk"])

        if form.is_valid():
            email: str = form.cleaned_data["email"]

            # Check if user already exists
            try:
                user: Account = Account.objects.get(email=email.lower())
                user_exists = True
            except Account.DoesNotExist:
                # Create user account with type CLIENT and unusable password
                user = Account.objects.create_user(
                    email=email,
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data.get("last_name", ""),
                    primary_contact=form.cleaned_data["primary_contact"],
                    type=Account.Type.CLIENT,
                )
                user.set_unusable_password()
                user.save()
                user_exists = False

            # Associate user with client
            user.groups.add(Group.objects.get_or_create(name="consultant")[0])
            client.users.add(user)
            client.save()

            # Send email
            if settings.USE_EMAIL:
                # Get project details
                if user_exists:
                    # Send notification email for existing user
                    context = {
                        "user": user,
                        "site_name": settings.SITE_NAME,
                        "client_name": client.name,
                        "protocol": "https" if self.request.is_secure() else "http",
                        "domain": self.request.get_host(),
                    }

                    subject = (
                        f"You've been added to {client.name} on {settings.SITE_NAME}"
                    )
                    html_message = render_to_string(
                        self.client_added_email_template, context
                    )
                else:
                    # Send invitation email with password reset for new user
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))

                    context = {
                        "user": user,
                        "protocol": "https" if self.request.is_secure() else "http",
                        "domain": self.request.get_host(),
                        "uid": uid,
                        "token": token,
                        "site_name": settings.SITE_NAME,
                        "expiry_hours": 24,
                        "client_name": client.name,
                    }

                    subject = (
                        f"You've been invited to {client.name} on {settings.SITE_NAME}"
                    )
                    html_message = render_to_string(
                        self.password_reset_email_template, context
                    )

                # Send email
                try:
                    send_mail(
                        subject=subject,
                        message="",  # Plain text version (optional)
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    if user_exists:
                        messages.success(
                            self.request,
                            f"Existing user '{user.email}' has been added to client '{client.name}'. "
                            f"A notification email has been sent.",
                        )
                    else:
                        messages.success(
                            self.request,
                            f"User '{user.email}' has been invited to client '{client.name}'. "
                            f"A password setup email has been sent to {user.email}.",
                        )
                except Exception as e:
                    messages.warning(
                        self.request,
                        f"User '{user.email}' has been associated with the client but email could not be sent. "
                        f"Error: {str(e)}",
                    )
            else:
                messages.success(
                    self.request,
                    f"User '{user.email}' has been added to client '{client.name}'. "
                    f"Email is disabled.",
                )

            return redirect("client:consultant:client-user-list", pk=client.pk)
        else:
            # Form is invalid, re-render with errors
            context = {
                "form": form,
                "client": client,
                "breadcrumbs": self.get_breadcrumbs(client),
            }
            return render(request, self.template_name, context)


class ClientRemoveUserView(UserHasGroupGenericMixin, View):
    """Remove user association from client."""

    permissions_required = "consultant"

    def get_breadcrumbs(self, client: Company) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=client.name,
                url=reverse(
                    "client:consultant:client-detail", kwargs={"pk": client.pk}
                ),
            ),
            BreadcrumbItem(
                title="Remove User",
                url=None,
            ),
        ]

    def post(self, request, pk, user_pk, *args, **kwargs):
        """Remove the user from the client."""
        client = get_object_or_404(Company, pk=pk)
        user = get_object_or_404(Account, pk=user_pk)

        # Prevent users from removing themselves
        if user.pk == request.user.pk:
            messages.error(request, "You cannot remove yourself from the client.")
            return redirect("client:consultant:client-user-list", pk=client.pk)

        if user in client.users.all():
            client.users.remove(user)
            messages.success(
                request,
                f"User '{user.email}' has been removed from client '{client.name}'.",
            )
        else:
            messages.warning(request, "This user is not associated with this client.")

        return redirect("client:consultant:client-user-list", pk=client.pk)


class ClientResendInviteView(UserHasGroupGenericMixin, View):
    """Resend invitation email to client user."""

    permissions_required = "consultant"
    password_reset_email_template = "client/password_reset_email.html"

    def post(self, request, pk, user_pk, *args, **kwargs):
        """Send the invitation email."""
        client = get_object_or_404(Company, pk=pk)
        user = get_object_or_404(Account, pk=user_pk)

        if user not in client.users.all():
            messages.error(request, "This user is not associated with this client.")
            return redirect("client:consultant:client-user-list", pk=client.pk)

        # Send password reset email
        if settings.USE_EMAIL:
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Build protocol and domain for email context
            protocol = "https" if request.is_secure() else "http"
            domain = request.get_host()

            # Prepare email context
            context = {
                "user": user,
                "protocol": protocol,
                "domain": domain,
                "uid": uid,
                "token": token,
                "site_name": settings.SITE_NAME,
                "expiry_hours": 24,
                "client_name": client.name,
            }

            # Render email templates
            subject = f"You've been invited to {client.name} on {settings.SITE_NAME}"
            html_message = render_to_string(self.password_reset_email_template, context)

            # Send email
            try:
                send_mail(
                    subject=subject,
                    message="",  # Plain text version (optional)
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                messages.success(
                    request,
                    f"Invitation email has been resent to {user.email}.",
                )
            except Exception as e:
                messages.error(
                    request,
                    f"Failed to send invitation email. Error: {str(e)}",
                )
        else:
            messages.warning(
                request,
                "Email is disabled. Cannot send invitation.",
            )

        return redirect("client:consultant:client-user-list", pk=client.pk)


class PaymentCertificateListView(PaymentCertMixin, ListView):
    """List all payment certificates for a project."""

    model = PaymentCertificate
    template_name = "consultant/payment_certificate_list.html"
    context_object_name = "payment_certificates"

    def get_breadcrumbs(self: "PaymentCertificateListView") -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            {
                "title": "Return to Clients",
                "url": reverse("client:consultant:client-list"),
            },
            {
                "title": f"{project.client.name}",
                "url": reverse(
                    "client:consultant:client-detail",
                    kwargs={"pk": self.client.pk},
                ),
            },
            {"title": f"{project.name} - Certificates", "url": None},
        ]


class PaymentCertificateFinalApprovalView(
    PaymentCertMixin, LineItemDetailMixin, UpdateView
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
            {
                "title": "Return to Clients",
                "url": reverse("client:consultant:client-list"),
            },
            {
                "title": f"{self.client.name}",
                "url": reverse(
                    "client:consultant:client-detail",
                    kwargs={"pk": self.client.pk},
                ),
            },
            {
                "title": f"Payment Certificate #{self.get_object().certificate_number}",
                "url": None,
            },
        ]

    def form_valid(self, form):
        payment_certificate = form.save(commit=False)
        payment_certificate.save()
        project = payment_certificate.project

        # Mark all transactions as claimed based on status
        if payment_certificate.status == PaymentCertificate.Status.APPROVED:
            payment_certificate.actual_transactions.update(claimed=True, approved=True)
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
                to=[user.email for user in project.users.all()],
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
                to=[user.email for user in project.users.all()],
                subject=subject,
                html_body=html_body,
                plain_body="",
            )

        return redirect(
            "client:consultant:client-detail",
            pk=self.client.pk,
        )


class PaymentCertificateEditApprovedDateView(PaymentCertMixin, UpdateView):
    """Edit only the approved_on date for a payment certificate."""

    model = PaymentCertificate
    form_class = PaymentCertificateApprovedDateForm
    template_name = "consultant/payment_certificate_edit_date.html"
    context_object_name = "payment_certificate"

    def get_breadcrumbs(
        self: "PaymentCertificateEditApprovedDateView",
    ) -> list[BreadcrumbItem]:
        return [
            {
                "title": "Return to Clients",
                "url": reverse("client:consultant:client-list"),
            },
            {
                "title": f"{self.client.name}",
                "url": reverse(
                    "client:consultant:client-detail",
                    kwargs={"pk": self.client.pk},
                ),
            },
            {
                "title": f"{self.project.name} - Certificates",
                "url": reverse(
                    "client:consultant:payment-certificate-list",
                    kwargs={"project_pk": self.project.pk},
                ),
            },
            {
                "title": f"Edit Certificate #{self.get_object().certificate_number}",
                "url": None,
            },
        ]

    def get_success_url(self):
        messages.success(
            self.request,
            f"Approval date updated for Certificate #{self.object.certificate_number}",
        )
        return reverse(
            "client:consultant:payment-certificate-list",
            kwargs={
                "project_pk": self.get_project().pk,
            },
        )
