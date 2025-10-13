"""Views for managing Project.clients"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    UpdateView,
    View,
)

from app.Account.models import Account
from app.Project.forms import ClientForm, ClientUserInviteForm
from app.Project.models import Client, Project


class ProjectAddClientView(LoginRequiredMixin, CreateView):
    """Add a client to a project."""

    model = Client
    form_class = ClientForm
    template_name = "client/client_form.html"

    def dispatch(self, request, *args, **kwargs):
        """Get the project and verify ownership."""
        self.project = get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
            deleted=False,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context

    def form_valid(self, form):
        """Save the client and associate with project."""
        client = form.save(commit=False)
        client.save()

        # Associate client with project
        self.project.client = client
        self.project.save()

        messages.success(
            self.request, f"Client '{client.name}' has been added to the project."
        )
        return redirect("project:project-detail", pk=self.project.pk)


class ClientInviteUserView(LoginRequiredMixin, FormView):
    """Invite a user to a client."""

    form_class = ClientUserInviteForm
    template_name = "client/client_invite_user.html"

    def dispatch(self, request, *args, **kwargs):
        """Get the client and verify project ownership."""
        self.client = get_object_or_404(
            Client, pk=self.kwargs["client_pk"], deleted=False
        )

        # Verify that the user owns the project associated with this client
        if not Project.objects.filter(
            client=self.client, account=self.request.user, deleted=False
        ).exists():
            messages.error(
                self.request,
                "You do not have permission to invite users to this client.",
            )
            return redirect("project:project-list")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add client to context."""
        context = super().get_context_data(**kwargs)
        context["client"] = self.client
        return context

    def form_valid(self, form):
        """Create the user account and associate with client."""
        from django.conf import settings
        from django.contrib.auth.tokens import default_token_generator
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        email = form.cleaned_data["email"]

        # Check if user already exists
        try:
            user = Account.objects.get(email=email, deleted=False)
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
        self.client.user = user
        self.client.save()

        # Send email
        if settings.USE_EMAIL:
            # Get project details
            project = Project.objects.filter(client=self.client, deleted=False).first()

            if user_exists:
                # Send notification email for existing user
                context = {
                    "user": user,
                    "site_name": "Profit Pro",
                    "client_name": self.client.name,
                    "project_name": project.name if project else None,
                    "project_description": project.description if project else None,
                    "protocol": "https" if self.request.is_secure() else "http",
                    "domain": self.request.get_host(),
                }

                subject = f"You've been added to {self.client.name} on Profit Pro"
                html_message = render_to_string(
                    "client/client_added_email.html", context
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
                    "site_name": "Profit Pro",
                    "expiry_hours": 24,
                    "client_name": self.client.name,
                    "project_name": project.name if project else None,
                    "project_description": project.description if project else None,
                }

                subject = f"You've been invited to {self.client.name} on Profit Pro"
                html_message = render_to_string(
                    "client/password_reset_email.html", context
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
                        f"Existing user '{user.email}' has been added to client '{self.client.name}'. "
                        f"A notification email has been sent.",
                    )
                else:
                    messages.success(
                        self.request,
                        f"User '{user.email}' has been invited to client '{self.client.name}'. "
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
                f"User '{user.email}' has been added to client '{self.client.name}'. "
                f"Email is disabled.",
            )

        # Get the project associated with this client
        project = Project.objects.filter(client=self.client, deleted=False).first()
        if project:
            return redirect("project:project-detail", pk=project.pk)
        return redirect("project:project-list")


class ProjectEditClientView(LoginRequiredMixin, UpdateView):
    """Edit a client for a project."""

    model = Client
    form_class = ClientForm
    template_name = "client/client_form.html"

    def get_queryset(self):
        """Filter clients by current user and project."""
        return Client.objects.filter(
            project=self.kwargs["project_pk"],
            id=self.kwargs["pk"],
            deleted=False,
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
        return context

    def get_success_url(self):
        """Redirect to the project list."""
        return reverse_lazy(
            "project:project-detail", kwargs={"pk": self.kwargs["project_pk"]}
        )


class ClientRemoveUserView(LoginRequiredMixin, View):
    """Remove user association from client."""

    def dispatch(self, request, *args, **kwargs):
        """Get the client and verify project ownership."""
        self.client = get_object_or_404(
            Client, pk=self.kwargs["client_pk"], deleted=False
        )

        # Verify that the user owns the project associated with this client
        if not Project.objects.filter(
            client=self.client, account=self.request.user, deleted=False
        ).exists():
            messages.error(
                self.request,
                "You do not have permission to modify this client.",
            )
            return redirect("project:project-list")

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Remove the user from the client."""
        if self.client.user:
            user_email = self.client.user.email
            self.client.user = None
            self.client.save()
            messages.success(
                self.request,
                f"User '{user_email}' has been removed from client '{self.client.name}'.",
            )
        else:
            messages.warning(
                self.request, "This client does not have an associated user."
            )

        # Redirect back to project detail
        project = Project.objects.filter(client=self.client, deleted=False).first()
        if project:
            return redirect("project:project-detail", pk=project.pk)
        return redirect("project:project-list")


class ClientResendInviteView(LoginRequiredMixin, DetailView):
    """Resend invitation email to client user."""

    model = Client

    def dispatch(self, request, *args, **kwargs):
        """Get the client and verify project ownership."""
        self.client = get_object_or_404(
            Client, pk=self.kwargs["client_pk"], deleted=False
        )

        # Verify that the user owns the project associated with this client
        if not Project.objects.filter(
            client=self.client, account=self.request.user, deleted=False
        ).exists():
            messages.error(
                self.request,
                "You do not have permission to resend invites for this client.",
            )
            return redirect("project:project-list")

        # Check if client has a user
        if not self.client.user:
            messages.error(
                self.request, "This client does not have an associated user to invite."
            )
            project = Project.objects.filter(client=self.client, deleted=False).first()
            if project:
                return redirect("project:project-detail", pk=project.pk)
            return redirect("project:project-list")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Send the invitation email."""
        from django.conf import settings
        from django.contrib.auth.tokens import default_token_generator
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = self.client.user

        # Send password reset email
        if settings.USE_EMAIL:
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Build reset URL
            protocol = "https" if self.request.is_secure() else "http"
            domain = self.request.get_host()

            # Get project details
            project = Project.objects.filter(client=self.client, deleted=False).first()

            # Prepare email context
            context = {
                "user": user,
                "protocol": protocol,
                "domain": domain,
                "uid": uid,
                "token": token,
                "site_name": "Profit Pro",
                "expiry_hours": 24,
                "client_name": self.client.name,
                "project_name": project.name if project else None,
                "project_description": project.description if project else None,
            }

            # Render email templates
            subject = f"You've been invited to {self.client.name} on Profit Pro"
            html_message = render_to_string("client/password_reset_email.html", context)

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
                    self.request,
                    f"Invitation email has been resent to {user.email}.",
                )
            except Exception as e:
                messages.error(
                    self.request,
                    f"Failed to send invitation email. Error: {str(e)}",
                )
        else:
            messages.warning(
                self.request,
                "Email is disabled. Cannot send invitation.",
            )

        # Redirect back to project detail
        project = Project.objects.filter(client=self.client, deleted=False).first()
        if project:
            return redirect("project:project-detail", pk=project.pk)
        return redirect("project:project-list")
