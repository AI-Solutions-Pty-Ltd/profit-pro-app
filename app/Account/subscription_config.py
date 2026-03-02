"""Subscription configuration and limits."""

from dataclasses import dataclass
from typing import Any

from django.db import models


@dataclass
class SubscriptionLimits:
    """Limits configuration for a subscription tier."""

    max_projects: int
    max_users_per_project: int
    parent: str | None = None


class Subscription(models.TextChoices):
    FREE_TIER = "FREE_TIER", "Free Tier"
    BUSINESS_MANAGEMENT = "BUSINESS_MANAGEMENT", "Business Management Module"
    PAYMENTS_AND_INVOICES = "PAYMENTS_AND_INVOICES", "Payments and Invoices"
    PROFIT_AND_LOSS = "PROFIT_AND_LOSS", "Profit and Loss"
    SITE_MANAGEMENT = "SITE_MANAGEMENT", "Site Management"
    PROJECT_ESTIMATOR = "PROJECT_ESTIMATOR", "Project Estimator"
    ADMINISTRATION = "ADMINISTRATION", "Administration"


class SubscriptionConfig:
    """Configuration for each subscription tier."""

    LIMITS: dict[Subscription, SubscriptionLimits] = {
        Subscription.FREE_TIER: SubscriptionLimits(
            max_projects=1,
            max_users_per_project=3,
        ),
        Subscription.BUSINESS_MANAGEMENT: SubscriptionLimits(
            max_projects=5,
            max_users_per_project=10,
        ),
        Subscription.PAYMENTS_AND_INVOICES: SubscriptionLimits(
            parent=Subscription.BUSINESS_MANAGEMENT,
            max_projects=5,
            max_users_per_project=10,
        ),
        Subscription.PROFIT_AND_LOSS: SubscriptionLimits(
            parent=Subscription.BUSINESS_MANAGEMENT,
            max_projects=10,
            max_users_per_project=20,
        ),
        Subscription.SITE_MANAGEMENT: SubscriptionLimits(
            parent=Subscription.BUSINESS_MANAGEMENT,
            max_projects=20,
            max_users_per_project=50,
        ),
        Subscription.PROJECT_ESTIMATOR: SubscriptionLimits(
            parent=Subscription.BUSINESS_MANAGEMENT,
            max_projects=50,
            max_users_per_project=100,
        ),
        Subscription.ADMINISTRATION: SubscriptionLimits(
            parent=Subscription.BUSINESS_MANAGEMENT,
            max_projects=50,
            max_users_per_project=100,
        ),
    }

    @classmethod
    def get_limit(cls, tier: Subscription, limit_name: str) -> Any:
        """Get a specific limit for a subscription tier."""
        limits = cls.LIMITS.get(
            tier, SubscriptionLimits(max_projects=0, max_users_per_project=0)
        )
        return getattr(limits, limit_name, 0)

    @classmethod
    def get_all_limits(cls, tier: Subscription) -> dict[str, Any]:
        """Get all limits for a subscription tier."""
        limits = cls.LIMITS.get(tier)
        if limits is None:
            return {}
        return {
            "max_projects": limits.max_projects,
            "max_users_per_project": limits.max_users_per_project,
        }

    @classmethod
    def has_feature(cls, tier: Subscription, feature: str) -> bool:
        """Check if a subscription tier has a specific feature."""
        # Features have been removed for now
        return False
