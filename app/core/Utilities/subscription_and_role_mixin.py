"""Combined subscription and project role permission mixin."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from app.Account.models import Account
from app.Account.subscription_config import Subscription
from app.Project.models import Project, Role


class SubscriptionAndRoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that checks both subscription tier and project role permissions.

    This mixin ensures that:
    1. User has the required subscription tier (or parent tier)
    2. User has the required project role

    Usage:
        class MyView(SubscriptionAndRoleRequiredMixin, BreadcrumbMixin, ListView):
            required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
            roles = [Role.CONTRACT_BOQ]
            project_slug = "project_pk"
    """

    required_tiers: list[Subscription] | None = None
    roles: list[Role] = []
    project_slug: str | None = None

    def test_func(self) -> bool:
        """Check both subscription and project role permissions."""
        user: Account = self.request.user  # type: ignore

        # First check subscription
        if not user.has_subscription_tier(self.required_tiers):
            return False

        # Superuser bypasses role checks
        if user.is_superuser:
            return True

        # Then check project role
        if not self.roles:
            raise ValueError("Role must be specified.")
        if not self.project_slug:
            raise ValueError("Project slug must be specified.")

        project = self.get_project()
        return user.has_project_role(project, self.roles)

    def get_project(self) -> Project:
        """Get the project from URL kwargs."""
        kwargs = self.kwargs  # type: ignore
        if not kwargs[self.project_slug]:
            raise ValueError("Project slug must be specified.")
        if not hasattr(self, "project"):
            from django.shortcuts import get_object_or_404

            self.project = get_object_or_404(Project, pk=kwargs[self.project_slug])
        return self.project

    def handle_no_permission(self):
        """Redirect with appropriate error message."""
        if not self.request.user.is_authenticated:  # type: ignore
            return super().handle_no_permission()

        user: Account = self.request.user  # type: ignore

        # Check if it's a subscription issue or role issue
        if not user.has_subscription_tier(self.required_tiers):
            messages.error(
                self.request,  # type: ignore
                "Your current subscription does not include access to this feature. "
                f"A '{self.required_tiers}' subscription is required.",
            )
        else:
            # It's a role issue
            messages.error(
                self.request,  # type: ignore
                f"Page restricted to {self.roles}.",
            )

        return redirect("home")

    def get_context_data(self, **kwargs):
        """Add current project to context for template URL building."""
        context = super().get_context_data(**kwargs)  # type: ignore
        context["project"] = self.get_project()
        return context
