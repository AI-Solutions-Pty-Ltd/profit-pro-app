"""Views for managing Project.clients"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    UpdateView,
    View,
)

from app.Account.models import Account
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.forms import ClientCreateUpdateForm, ClientUserInviteForm
from app.Project.models import Company, Project, ProjectRole, Role


class ClientMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_queryset(self) -> QuerySet[Company]:
        project = self.get_project()
        return Company.objects.filter(
            type=Company.Type.CLIENT, projects=project
        ).order_by("-created_at")

    def get_object(self) -> Company:
        if not hasattr(self, "project") or not self.project:
            self.project = self.get_project()
        queryset = self.get_queryset()
        return get_object_or_404(
            queryset,
            pk=self.kwargs["pk"],  ## MAKE SURE SLUG REMAINS "pk"
        )

    def get_client(self, slug: int) -> Company:
        if not hasattr(self, "project") or not self.project:
            self.project = self.get_project()
        return get_object_or_404(Company, pk=slug)


class ProjectAddClientView(ClientMixin, CreateView):
    """Add a client to a project."""

    model = Company
    form_class = ClientCreateUpdateForm
    template_name = "client/client_form.html"

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
            BreadcrumbItem(title=f"Add Client to {self.get_project().name}", url=None),
        ]

    def form_valid(self, form):
        """Save the client and associate with project."""
        project = self.get_project()

        # Check if a company with this name already exists
        name = form.cleaned_data.get("name")
        existing_client = Company.objects.filter(name__iexact=name).first()

        if existing_client:
            # Use the existing client
            client = existing_client
            messages.info(
                self.request,
                f"Client '{client.name}' already exists. Using existing client.",
            )
        else:
            # Create new client
            client = form.save(commit=False)
            client.save()
            messages.success(
                self.request, f"Client '{client.name}' has been added to the project."
            )

        # Associate client with project
        project.client = client
        project.save()

        return redirect("project:project-management", pk=project.pk)


class ClientInviteUserView(ClientMixin, FormView):
    """Invite a user to a client."""

    form_class = ClientUserInviteForm
    template_name = "client/client_invite_user.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Return to Project Detail",
                url=reverse(
                    "project:project-management", kwargs={"pk": self.project.pk}
                ),
            ),
            BreadcrumbItem(title=f"Invite User to {self.client.name}", url=None),
        ]

    def dispatch(self, request, *args, **kwargs):
        """Get the client and verify project ownership."""
        # Verify that the user owns the project associated with this client
        self.project = self.get_project()
        self.client = self.get_client(self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add client to context."""
        context = super().get_context_data(**kwargs)
        context["client"] = self.client
        return context

    def form_valid(self, form):
        """Create the user account and associate with client."""

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
        self.client.users.add(user)
        self.client.save()

        # get_or_create project role:
        ProjectRole.objects.get_or_create(
            project=self.project, users=user, role=Role.CLIENT
        )

        # Send email
        if settings.USE_EMAIL:
            # Get project details
            if user_exists:
                # Send notification email for existing user
                context = {
                    "user": user,
                    "site_name": settings.SITE_NAME,
                    "client_name": self.client.name,
                    "project_name": self.project.name,
                    "project_description": self.project.description,
                    "protocol": "https" if self.request.is_secure() else "http",
                    "domain": self.request.get_host(),
                }

                subject = (
                    f"You've been added to {self.client.name} on {settings.SITE_NAME}"
                )
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
                    "site_name": settings.SITE_NAME,
                    "expiry_hours": 24,
                    "client_name": self.client.name,
                    "project_name": self.project.name,
                    "project_description": self.project.description,
                }

                subject = (
                    f"You've been invited to {self.client.name} on {settings.SITE_NAME}"
                )
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
        project = Project.objects.filter(client=self.client).first()
        if project:
            return redirect("project:project-management", pk=project.pk)
        return redirect("project:portfolio-dashboard")


class ClientEditView(ClientMixin, UpdateView):
    """Edit a client for a project."""

    model = Company
    form_class = ClientCreateUpdateForm
    template_name = "client/client_form.html"

    def get_breadcrumbs(self: "ClientEditView") -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Return to Project Detail",
                url=reverse(
                    "project:project-management", kwargs={"pk": self.project.pk}
                ),
            ),
            BreadcrumbItem(
                title=f"Edit Client {self.get_client(slug=self.kwargs['pk']).name}",
                url=None,
            ),
        ]

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_success_url(self):
        """Redirect to the project list."""
        return reverse_lazy(
            "project:project-management", kwargs={"pk": self.kwargs["project_pk"]}
        )


class ClientRemoveView(ClientMixin, DeleteView):
    """Remove client from project."""

    model = Company
    template_name = "client/client_confirm_remove.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Return to Project Detail",
                url=reverse(
                    "project:project-management", kwargs={"pk": self.project.pk}
                ),
            ),
            BreadcrumbItem(
                title=f"Remove Client {self.get_client(slug=self.kwargs['pk']).name}",
                url=None,
            ),
        ]

    def dispatch(self, request, *args, **kwargs):
        """Get the client and verify project ownership."""
        # Verify that the user owns the project associated with this client
        self.project = self.get_project()
        self.client = self.get_client(self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        """Return the client object."""
        return self.client

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context

    def get_success_url(self):
        return reverse_lazy(
            "project:project-management", kwargs={"pk": self.project.pk}
        )

    def delete(self, request, *args, **kwargs):
        """Remove the client from the project (don't delete the client)."""
        if self.project.client == self.client:
            client_name = self.client.name
            self.project.client = None
            self.project.save()
            messages.success(
                self.request,
                f"Client '{client_name}' has been removed from project '{self.project.name}'.",
            )
        else:
            messages.warning(
                self.request, "This client is not assigned to this project."
            )

        # Redirect back to project detail
        return redirect("project:project-management", pk=self.project.pk)


class ClientRemoveUserView(ClientMixin, View):
    """Remove user association from client."""

    def get_breadcrumbs(self: "ClientRemoveUserView") -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Return to Project Detail",
                url=reverse(
                    "project:project-management", kwargs={"pk": self.project.pk}
                ),
            ),
            BreadcrumbItem(
                title=f"Remove User from Client {self.get_client(slug=self.kwargs['pk']).name}",
                url=None,
            ),
        ]

    def dispatch(self, request, *args, **kwargs):
        """Get the client and verify project ownership."""
        # Verify that the user owns the project associated with this client
        self.project = self.get_project()
        self.client = self.get_client(self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Remove the user from the client."""
        if self.client.users.exists():
            user = self.client.users.first()
            if user:  # Type guard
                user_email = user.email  # type: ignore
                self.client.users.remove(user)
                messages.success(
                    self.request,
                    f"User '{user_email}' has been removed from client '{self.client.name}'.",
                )
        else:
            messages.warning(
                self.request, "This client does not have an associated user."
            )

        # Redirect back to project detail
        if self.project:
            return redirect("project:project-management", pk=self.project.pk)
        return redirect("project:portfolio-dashboard")


class ClientResendInviteView(ClientMixin, DetailView):
    """Resend invitation email to client user."""

    model = Company

    def dispatch(self, request, *args, **kwargs):
        """Get the client and verify project ownership."""
        self.project = self.get_project()
        self.client = self.get_client(self.kwargs["pk"])

        # Check if client has a user
        if not self.client.users.exists():
            messages.error(
                self.request, "This client does not have an associated user to invite."
            )
            if self.project:
                return redirect("project:project-management", pk=self.project.pk)
            return redirect("project:portfolio-dashboard")

        return super().dispatch(request, *args, **kwargs)

    def get(self: "ClientResendInviteView", request, *args, **kwargs):
        """Send the invitation email."""

        user: Account | None = self.client.users.first()  # type: ignore
        if not user:
            messages.error(
                self.request, "This client does not have an associated user."
            )
            if self.project:
                return redirect("project:project-management", pk=self.project.pk)
            return redirect("project:portfolio-dashboard")

        # Send password reset email
        if settings.USE_EMAIL and user:
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Build protocol and domain for email context
            protocol = "https" if self.request.is_secure() else "http"
            domain = self.request.get_host()

            # Get project details
            project = Project.objects.filter(client=self.client).first()

            # Prepare email context
            context = {
                "user": user,
                "protocol": protocol,
                "domain": domain,
                "uid": uid,
                "token": token,
                "site_name": settings.SITE_NAME,
                "expiry_hours": 24,
                "client_name": self.client.name,
                "project_name": project.name if project else None,
                "project_description": project.description if project else None,
            }

            # Render email templates
            subject = (
                f"You've been invited to {self.client.name} on {settings.SITE_NAME}"
            )
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
        project = Project.objects.filter(client=self.client).first()
        if project:
            return redirect("project:project-management", pk=project.pk)
        return redirect("project:portfolio-dashboard")
