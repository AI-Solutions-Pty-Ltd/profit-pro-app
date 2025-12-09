from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import redirect


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
