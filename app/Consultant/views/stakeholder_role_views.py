from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import DeleteView, FormView, UpdateView

from app.Account.models import Account
from app.Consultant.forms import CompanyUserInviteForm, ProjectCompanyUserRoleForm
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Company, ProjectCompanyUserRole, Role


class ProjectCompanyUserRoleAllocateView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, FormView
):
    """Allocate a user to a company on a project with a role."""

    form_class = ProjectCompanyUserRoleForm
    template_name = "stakeholder_role/allocate_user_role_form.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_project()
        self.company = get_object_or_404(Company, pk=kwargs["company_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["company"] = self.company
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        user_pk = self.request.GET.get("user")
        if user_pk:
            initial["user"] = user_pk
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["company"] = self.company
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title=f"Allocate User - {self.company.name}",
                url=None,
            ),
        ]

    def form_valid(self, form):
        user_role = form.save(commit=False)
        user_role.project = self.project
        user_role.company = self.company

        # Validate unique constraint before saving to avoid database integrity errors breaking the transaction
        if ProjectCompanyUserRole.objects.filter(
            project=self.project, company=self.company, user=user_role.user
        ).exists():
            form.add_error(
                "user",
                f"User '{user_role.user}' is already assigned a role for this company on this project.",
            )
            messages.error(
                self.request,
                f"User '{user_role.user}' is already assigned a role for this company on this project.",
            )
            return self.form_invalid(form)

        user_role.save()
        messages.success(
            self.request,
            f"User '{user_role.user}' assigned as {user_role.role} for {self.company.name} successfully.",
        )
        return redirect("project:project-setup", pk=self.project.pk)


class ProjectCompanyUserRoleUpdateView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, UpdateView
):
    """Update stakeholder role for a user."""

    model = ProjectCompanyUserRole
    form_class = ProjectCompanyUserRoleForm
    template_name = "stakeholder_role/allocate_user_role_form.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_project()
        self.company = get_object_or_404(Company, pk=kwargs["company_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["company"] = self.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["company"] = self.company
        context["is_update"] = True
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title=f"Edit Role - {self.get_object().user}",
                url=None,
            ),
        ]

    def form_valid(self, form):
        user_role = form.save()
        messages.success(
            self.request,
            f"Updated role for '{user_role.user}' to {user_role.role} successfully.",
        )
        return redirect("project:project-setup", pk=self.project.pk)


class ProjectCompanyUserRoleRemoveView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, DeleteView
):
    """Remove user stakeholder role assignment."""

    model = ProjectCompanyUserRole
    template_name = "stakeholder_role/confirm_remove_user_role.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_project()
        self.company = get_object_or_404(Company, pk=kwargs["company_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["company"] = self.company
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title=f"Remove User Role - {self.get_object().user}",
                url=None,
            ),
        ]

    def get_success_url(self):
        messages.success(
            self.request, "User stakeholder assignment removed successfully."
        )
        return reverse("project:project-setup", kwargs={"pk": self.project.pk})


class CompanyInviteUserView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, FormView):
    """Invite a user and associate them with a stakeholder company."""

    form_class = CompanyUserInviteForm
    template_name = "stakeholder_role/company_invite_user.html"
    roles = [Role.ADMIN]
    project_slug = "project_pk"
    client_added_email_template = "client/client_added_email.html"
    password_reset_email_template = "client/password_reset_email.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_project()
        self.company = get_object_or_404(Company, pk=kwargs["company_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["company"] = self.company

        if self.company.type == Company.Type.CLIENT:
            context["back_url"] = reverse(
                "client:client-management:client-update",
                kwargs={"project_pk": self.project.pk, "pk": self.company.pk},
            )
        elif self.company.type == Company.Type.CONTRACTOR:
            context["back_url"] = reverse(
                "client:contractor-management:contractor-update",
                kwargs={"project_pk": self.project.pk, "pk": self.company.pk},
            )
        else:
            context["back_url"] = reverse(
                "client:lead-consultant-management:lead-consultant-update",
                kwargs={"project_pk": self.project.pk, "pk": self.company.pk},
            )
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        if self.company.type == Company.Type.CLIENT:
            back_url = reverse(
                "client:client-management:client-update",
                kwargs={"project_pk": self.project.pk, "pk": self.company.pk},
            )
        elif self.company.type == Company.Type.CONTRACTOR:
            back_url = reverse(
                "client:contractor-management:contractor-update",
                kwargs={"project_pk": self.project.pk, "pk": self.company.pk},
            )
        else:
            back_url = reverse(
                "client:lead-consultant-management:lead-consultant-update",
                kwargs={"project_pk": self.project.pk, "pk": self.company.pk},
            )

        return [
            BreadcrumbItem(
                title=self.project.name,
                url=reverse("project:project-setup", kwargs={"pk": self.project.pk}),
            ),
            BreadcrumbItem(
                title=f"Edit {self.company.name}",
                url=back_url,
            ),
            BreadcrumbItem(title=f"Invite User to {self.company.name}", url=None),
        ]

    def form_valid(self, form):
        email = form.cleaned_data["email"]

        # Check if user already exists
        try:
            user = Account.objects.get(email=email.lower())
            user_exists = True
        except Account.DoesNotExist:
            # Determine account type
            if self.company.type == Company.Type.CLIENT:
                account_type = Account.Type.CLIENT
            elif self.company.type == Company.Type.CONTRACTOR:
                account_type = Account.Type.CONTRACTOR
            else:
                account_type = Account.Type.CONSULTANT

            user = Account.objects.create_user(
                email=email,
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data.get("last_name", ""),
                primary_contact=form.cleaned_data["primary_contact"],
                type=account_type,
            )
            user.set_unusable_password()
            user.save()
            user_exists = False

        # Check if already associated
        if user in self.company.users.all():
            form.add_error(
                "email",
                f"User '{user.email}' is already associated with {self.company.name}.",
            )
            return self.form_invalid(form)

        # Determine group to add
        if self.company.type == Company.Type.CONTRACTOR:
            group_name = "contractor"
        else:
            group_name = "consultant"

        # Associate user
        user.groups.add(Group.objects.get_or_create(name=group_name)[0])
        self.company.users.add(user)
        self.company.save()

        # Send email
        if settings.USE_EMAIL:
            try:
                if user_exists:
                    # Notify existing user
                    context = {
                        "user": user,
                        "site_name": settings.SITE_NAME,
                        "client_name": self.company.name,
                        "protocol": "https" if self.request.is_secure() else "http",
                        "domain": self.request.get_host(),
                    }
                    subject = f"You've been added to {self.company.name} on {settings.SITE_NAME}"
                    html_message = render_to_string(
                        self.client_added_email_template, context
                    )
                else:
                    # Invite new user
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
                        "client_name": self.company.name,
                    }
                    subject = f"You've been invited to {self.company.name} on {settings.SITE_NAME}"
                    html_message = render_to_string(
                        self.password_reset_email_template, context
                    )

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
                        f"Existing user '{user.email}' has been added to '{self.company.name}'. "
                        f"A notification email has been sent.",
                    )
                else:
                    messages.success(
                        self.request,
                        f"User '{user.email}' has been invited to '{self.company.name}'. "
                        f"A password setup email has been sent to {user.email}.",
                    )
            except Exception as e:
                messages.warning(
                    self.request,
                    f"User '{user.email}' has been associated with '{self.company.name}' but email could not be sent. "
                    f"Error: {str(e)}",
                )
        else:
            messages.success(
                self.request,
                f"User '{user.email}' has been added to '{self.company.name}'. (Email is disabled)",
            )

        # Redirect back to company edit page
        if self.company.type == Company.Type.CLIENT:
            success_url = reverse(
                "client:client-management:client-update",
                kwargs={"project_pk": self.project.pk, "pk": self.company.pk},
            )
        elif self.company.type == Company.Type.CONTRACTOR:
            success_url = reverse(
                "client:contractor-management:contractor-update",
                kwargs={"project_pk": self.project.pk, "pk": self.company.pk},
            )
        else:
            success_url = reverse(
                "client:lead-consultant-management:lead-consultant-update",
                kwargs={"project_pk": self.project.pk, "pk": self.company.pk},
            )

        return redirect(success_url)
