from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from app.Account.models import Account
from app.Project.models.project_roles import Role
from app.Project.models.projects_models import Project


class UserHasGroupGenericMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Generic mixin for user group permissions."""

    permissions = []

    def test_func(self):
        if self.request.user.is_superuser:  # type: ignore
            return True
        if not self.permissions:
            raise ValueError("Permissions must be specified.")
        return self.request.user.groups.filter(name__in=self.permissions).exists()  # type: ignore

    def handle_no_permission(self):
        """Redirect to home with error message if user lacks permission."""
        messages.error(
            self.request,  # type: ignore
            f"Page restricted to {', '.join(self.permissions)}.",
        )
        return redirect("home")


class UserHasProjectRoleGenericMixin(UserPassesTestMixin, LoginRequiredMixin):
    """Generic mixin for user project role permissions."""

    roles: list[Role] = []
    project_slug: str | None = None

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to ensure LoginRequiredMixin runs first."""
        # First check authentication (LoginRequiredMixin)
        if not request.user.is_authenticated:
            # Use LoginRequiredMixin's redirect to login behavior
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(
                request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        # Then run the normal dispatch which will call test_func
        dispatch = super().dispatch(request, *args, **kwargs)
        return dispatch

    def get_project(self) -> Project:
        kwargs = self.kwargs  # type: ignore
        if not kwargs[self.project_slug]:
            raise ValueError("Project slug must be specified.")
        return get_object_or_404(Project, pk=kwargs[self.project_slug])

    def get_user(self) -> Account:
        request = self.request  # type: ignore
        if not request or not request.user:
            raise ValueError("User does not exist.")
        user = request.user
        if not user.is_authenticated:
            raise ValueError("User is not authenticated.")
        return user

    def test_func(self: "UserHasProjectRoleGenericMixin") -> bool:
        project = self.get_project()
        user = self.get_user()
        if user.is_superuser:
            return True
        if not self.roles:
            raise ValueError("Role must be specified.")
        if not self.project_slug:
            raise ValueError("Project slug must be specified.")
        return user.has_project_role(project, self.roles)

    def handle_no_permission(self):
        """Redirect to home with error message if user lacks permission."""
        messages.error(
            self.request,  # type: ignore
            f"Page restricted to {self.roles}.",
        )
        return redirect("home")

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)  # type: ignore
        context["project"] = self.get_project()
        return context


def unauthenticated_user():
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                # return redirect('AIC:home')
                return func(request, *args, **kwargs)
            else:
                return redirect("account_login")

        return wrapper

    return decorator


def permitted_groups(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            if request.user.groups.exists():
                groups = request.user.groups.all()
                for group in allowed_roles:
                    if groups.filter(name=group).exists():
                        return func(request, *args, **kwargs)
                return redirect("login")
            else:
                return redirect("login")

        return wrapper

    return decorator


def api_permitted_groups(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            group = None

            if request.user.groups.exists():
                group = request.user.groups.all()

                for group in request.user.groups.all():
                    if group.name in allowed_roles:
                        return func(request, *args, **kwargs)
                return HttpResponse("Unauthorized", status=401)
            else:
                return HttpResponse("Unauthorized", status=401)

        return wrapper

    return decorator


def permitted_rights(allowed_rights=None):
    if allowed_rights is None:
        allowed_rights = []

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            permissions = request.user.user_permissions.all()
            if permissions.exists():
                for group in permissions:
                    if group.codename in allowed_rights:
                        return func(request, *args, **kwargs)

            return redirect("login")

        return wrapper

    return decorator
