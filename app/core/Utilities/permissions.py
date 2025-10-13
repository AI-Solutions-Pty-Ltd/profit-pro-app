from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class UserHasGroupGenericMixin(UserPassesTestMixin):
    """Generic mixin for user group permissions."""

    permissions = []

    def test_func(self):
        if not self.permissions:
            raise ValueError("Permissions must be specified.")
        return self.request.user.groups.filter(name__in=self.permissions).exists()

    def handle_no_permission(self):
        """Redirect to home with error message if user lacks permission."""
        messages.error(
            self.request,
            "You do not have permission to access this page. Only consultants can approve payment certificates.",
        )
        return redirect("home")
