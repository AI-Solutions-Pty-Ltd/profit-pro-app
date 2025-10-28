from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


class UserHasGroupGenericMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Generic mixin for user group permissions."""

    permissions = []

    def test_func(self):
        if not self.permissions or not self.request.user.is_superuser:
            raise ValueError("Permissions must be specified.")
        return self.request.user.groups.filter(name__in=self.permissions).exists()

    def handle_no_permission(self):
        """Redirect to home with error message if user lacks permission."""
        messages.error(
            self.request,
            f"Page restricted to {', '.join(self.permissions)}.",
        )
        return redirect("home")
