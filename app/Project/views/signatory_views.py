"""Views for managing Project signatories."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import DeleteView, DetailView, FormView, ListView, UpdateView

from app.Account.models import Account
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.forms import SignatoryForm, SignatoryInviteForm
from app.Project.models import Project, Signatories
from app.Project.models.project_roles import Role


class SignatoryMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for signatory views."""

    roles = [Role.USER]
    project_slug = "project_pk"


class SignatoryListView(SignatoryMixin, ListView):
    """List all signatories for a project."""

    model = Signatories
    template_name = "signatory/signatory_list.html"
    context_object_name = "signatories"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-detail", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(title="Signatories", url=None),
        ]

    def get_context_data(self: "SignatoryListView", **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SignatoryInviteView(SignatoryMixin, FormView):
    """Invite a user as a signatory for a project."""

    form_class = SignatoryInviteForm
    template_name = "signatory/signatory_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Return to Project Detail",
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title=f"Add Signatory to {self.get_project().name}", url=None
            ),
        ]

    def get_context_data(self: "SignatoryInviteView", **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_initial(self):
        """Set initial sequence number."""
        initial = super().get_initial()
        project = self.get_project()
        # Get next sequence number
        max_seq = project.signatories.order_by("-sequence_number").first()
        initial["sequence_number"] = (max_seq.sequence_number + 1) if max_seq else 1
        return initial

    def form_valid(self, form):
        """Create user account and signatory record."""
        email: str = form.cleaned_data["email"]
        project = self.get_project()

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

        # Add user to 'signatory' group
        signatory_group, _ = Group.objects.get_or_create(name="signatory")
        user.groups.add(signatory_group)

        # Create signatory record
        Signatories.objects.create(
            project=project,
            user=user,
            sequence_number=form.cleaned_data["sequence_number"],
            role=form.cleaned_data["role"],
        )

        # Send email
        self._send_invite_email(user, project, user_exists)

        return redirect("project:signatory-list", project_pk=self.kwargs["project_pk"])

    def _send_invite_email(self, user: Account, project: Project, user_exists: bool):
        """Send invitation email to the signatory."""
        if not settings.USE_EMAIL:
            messages.success(
                self.request,
                f"Signatory '{user.email}' has been added to project '{project.name}'. "
                f"Email is disabled.",
            )
            return

        if user_exists:
            # Send notification email for existing user
            context = {
                "user": user,
                "site_name": settings.SITE_NAME,
                "project_name": project.name,
                "project_description": project.description,
                "protocol": "https" if self.request.is_secure() else "http",
                "domain": self.request.get_host(),
            }
            subject = f"You've been added as a signatory on {settings.SITE_NAME}"
            html_message = render_to_string(
                "signatory/signatory_added_email.html", context
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
                "project_name": project.name,
                "project_description": project.description,
            }
            subject = f"You've been invited as a signatory on {settings.SITE_NAME}"
            html_message = render_to_string(
                "signatory/signatory_invite_email.html", context
            )

        # Send email
        try:
            send_mail(
                subject=subject,
                message="",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            if user_exists:
                messages.success(
                    self.request,
                    f"Existing user '{user.email}' has been added as signatory. "
                    f"A notification email has been sent.",
                )
            else:
                messages.success(
                    self.request,
                    f"User '{user.email}' has been invited as signatory. "
                    f"A password setup email has been sent.",
                )
        except Exception as e:
            messages.warning(
                self.request,
                f"Signatory '{user.email}' has been added but email could not be sent. "
                f"Error: {str(e)}",
            )

    def get_success_url(self):
        """Redirect to the signatory list."""
        return reverse_lazy(
            "project:signatory-list", kwargs={"project_pk": self.kwargs["project_pk"]}
        )


class SignatoryUpdateView(SignatoryMixin, UpdateView):
    """Update an existing signatory."""

    model = Signatories
    form_class = SignatoryForm
    template_name = "signatory/signatory_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        signatory = self.get_object()
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Return to Project Detail",
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(title=f"Update Signatory {signatory}", url=None),
        ]

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["signatory"] = self.get_object()
        return context

    def form_valid(self, form):
        """Show success message."""
        messages.success(
            self.request,
            f"Signatory '{form.instance}' has been updated successfully.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to the signatory list."""
        return reverse_lazy(
            "project:signatory-register",
        )


class SignatoryDeleteView(SignatoryMixin, DeleteView):
    """Delete a signatory."""

    model = Signatories
    template_name = "signatory/signatory_confirm_delete.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        signatory = self.get_object()
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Return to Project Detail",
                url=reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(title=f"Delete Signatory {signatory}", url=None),
        ]

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def form_valid(self: "SignatoryDeleteView", form):
        """Soft delete the signatory."""
        signatory = self.get_object()
        signatory.soft_delete()
        messages.success(
            self.request, f"Signatory '{signatory}' has been deleted successfully."
        )
        return redirect(str(self.get_success_url()))

    def get_success_url(self):
        """Redirect to the signatory list."""
        return reverse_lazy(
            "project:signatory-list", kwargs={"project_pk": self.kwargs["project_pk"]}
        )


class SignatoryResendInviteView(SignatoryMixin, DetailView):
    """Resend invitation email to signatory user."""

    model = Signatories

    def dispatch(self, request, *args, **kwargs):
        """Get the signatory and verify."""
        self.project = self.get_project()
        self.signatory = self.get_object()

        if not self.signatory.user:
            messages.error(
                self.request, "This signatory does not have an associated user."
            )
            return redirect("project:signatory-list", project_pk=self.project.pk)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Send the invitation email."""
        user = self.signatory.user

        if not settings.USE_EMAIL:
            messages.warning(self.request, "Email is disabled. Cannot send invitation.")
            return redirect("project:signatory-list", project_pk=self.project.pk)

        # Generate password reset token
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
            "project_name": self.project.name,
            "project_description": self.project.description,
        }

        subject = f"You've been invited as a signatory on {settings.SITE_NAME}"
        html_message = render_to_string(
            "signatory/signatory_invite_email.html", context
        )

        try:
            send_mail(
                subject=subject,
                message="",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            messages.success(
                self.request, f"Invitation email has been resent to {user.email}."
            )
        except Exception as e:
            messages.error(
                self.request, f"Failed to send invitation email. Error: {str(e)}"
            )

        return redirect("project:signatory-list", project_pk=self.project.pk)
