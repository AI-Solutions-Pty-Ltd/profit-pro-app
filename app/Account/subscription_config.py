"""Subscription configuration and limits."""

from typing import Any

from django.db import models


class Subscription(models.TextChoices):
    FREE_TIER = "FREE_TIER", "Free Tier"
    PAYMENTS_AND_INVOICES = "PAYMENTS_AND_INVOICES", "Payments and Invoices"
    PROFIT_AND_LOSS = "PROFIT_AND_LOSS", "Profit and Loss"
    SITE_MANAGEMENT = "SITE_MANAGEMENT", "Site Management"
    PROJECT_ESTIMATOR = "PROJECT_ESTIMATOR", "Project Estimator"


class SubscriptionConfig:
    """Configuration for each subscription tier."""

    LIMITS: dict[str, dict[str, Any]] = {
        Subscription.FREE_TIER: {
            "max_projects": 1,
            "max_users_per_project": 3,
            "max_storage_mb": 100,
            "features": ["basic_project_management"],
        },
        Subscription.PAYMENTS_AND_INVOICES: {
            "max_projects": 5,
            "max_users_per_project": 10,
            "max_storage_mb": 500,
            "features": ["basic_project_management", "payments", "invoicing"],
        },
        Subscription.PROFIT_AND_LOSS: {
            "max_projects": 10,
            "max_users_per_project": 20,
            "max_storage_mb": 1000,
            "features": ["basic_project_management", "profit_loss_tracking"],
        },
        Subscription.SITE_MANAGEMENT: {
            "max_projects": 20,
            "max_users_per_project": 50,
            "max_storage_mb": 2000,
            "features": ["basic_project_management", "site_management"],
        },
        Subscription.PROJECT_ESTIMATOR: {
            "max_projects": 50,
            "max_users_per_project": 100,
            "max_storage_mb": 5000,
            "features": ["basic_project_management", "project_estimation"],
        },
    }

    @classmethod
    def get_limit(cls, tier: str, limit_name: str) -> Any:
        """Get a specific limit for a subscription tier."""
        return cls.LIMITS.get(tier, {}).get(limit_name, 0)

    @classmethod
    def get_all_limits(cls, tier: str) -> dict[str, Any]:
        """Get all limits for a subscription tier."""
        return cls.LIMITS.get(tier, {})

    @classmethod
    def has_feature(cls, tier: str, feature: str) -> bool:
        """Check if a subscription tier has a specific feature."""
        features = cls.LIMITS.get(tier, {}).get("features", [])
        return feature in features
