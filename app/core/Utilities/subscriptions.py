"""Subscription permission mixin for view-level subscription gating."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from app.Account.models import Account
from app.Account.subscription_config import Subscription


class SubscriptionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that restricts access to views based on the user's subscription tier.

    Note: Add BreadcrumbMixin separately on the view — it cannot be included here
    because BreadcrumbMixin(View) breaks UserPassesTestMixin.dispatch in the MRO.

    Usage:
        class MyView(SubscriptionRequiredMixin, BreadcrumbMixin, ListView):
            required_tier = [Account.Subscription.SITE_MANAGEMENT]
    """

    required_tiers: list[Subscription] | None = None

    def test_func(self) -> bool:
        user: Account = self.request.user  # type: ignore[assignment]
        return user.has_subscription_tier(self.required_tiers)

    def handle_no_permission(self):
        messages.error(
            self.request,  # type: ignore[arg-type]
            "Your current subscription does not include access to this feature. "
            f"A '{self.required_tiers}' subscription is required.",
        )
        return redirect("home")
