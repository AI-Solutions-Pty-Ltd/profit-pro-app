"""Account models."""

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Optional

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q, QuerySet
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from app.Account.subscription_config import Subscription, SubscriptionConfig
from app.core.Utilities.models import BaseModel


class Municipality(BaseModel):
    province = models.CharField(max_length=255)
    municipality_name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)
    district = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Municipality"
        verbose_name_plural = "Municipalities"
        ordering = ["province", "municipality_name"]
        unique_together = ["province", "municipality_name", "code"]

    def __str__(self):
        return f"{self.municipality_name} ({self.code})"


if TYPE_CHECKING:
    from app.Project.models import Company, Portfolio, Project, ProjectRole, Role


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(
        self, email: str, password: str | None, **extra_fields: dict[str, Any]
    ):
        if not email:
            raise ValueError("Users require an email field")
        normalized_email = self.normalize_email(email)
        user = self.model(email=normalized_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class Suburb(BaseModel):
    suburb = models.CharField(max_length=255, unique=True)
    postcode = models.CharField(
        max_length=4,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^.{4}$",
                message="The Post Code Number must be 4 characters in length.",
            )
        ],
    )

    def __str__(self):
        return self.suburb

    class Meta:
        ordering = ["suburb"]


class Town(BaseModel):
    town = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.town

    class Meta:
        ordering = ["town"]


class Account(AbstractUser, BaseModel):
    username = None  # override username field from AbstractUser, we are not using username as unique field, but email override email field from AbstractUser to make it required

    class Type(models.TextChoices):
        CONTRACTOR = "Contractor", "Contractor"
        CLIENT = "Client", "Client"
        CONSULTANT = "Consultant", "Consultant"

    class IdentificationType(models.TextChoices):
        SOUTH_AFRICA_ID = "South African ID", "South African ID"
        PASSPORT = "Passport", "Passport"
        COMPANY = "Company", "Company"

    class NotificationType(models.TextChoices):
        EMAIL = "Email", "Email"
        SMS = "SMS", "SMS"
        BOTH = "Both", "Both"

    subscription = models.CharField(
        max_length=50,
        choices=Subscription.choices,
        help_text="Subscription tier",
        default=Subscription.DEMO_TIER,
    )
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(
        _("first name"), max_length=150, blank=False
    )  # override first_name field from AbstractUser to make it required
    last_name = models.CharField(
        _("last name"), max_length=150, blank=False
    )  # override last_name field from AbstractUser to make it required

    type = models.CharField(
        max_length=50,
        choices=Type.choices,
        blank=True,
        default=Type.CONTRACTOR,
    )

    primary_contact = PhoneNumberField(
        blank=False, null=False
    )  # phone number is mandatory
    alternative_contact = PhoneNumberField(blank=True, null=True)

    identification_type = models.CharField(
        max_length=50,
        choices=IdentificationType.choices,
        blank=True,
        default=IdentificationType.SOUTH_AFRICA_ID,
    )
    identification_number = models.CharField(max_length=15, blank=True)

    address = models.TextField(blank=True)
    notification_preferences = models.CharField(
        max_length=20, choices=NotificationType.choices, default=NotificationType.EMAIL
    )

    # Email verification fields
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    subscription_expires_at = models.DateTimeField(
        null=True, blank=True, help_text="Expiry date for demo/trial subscriptions"
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    if TYPE_CHECKING:
        projects: QuerySet[Project]
        portfolios: QuerySet[Portfolio]
        contractor_projects: QuerySet[Project]
        qs_projects: QuerySet[Project]
        lead_consultant_projects: QuerySet[Project]
        client_rep_projects: QuerySet[Project]
        project_roles: QuerySet[ProjectRole]
        companies: QuerySet[Company]

    def __str__(self):
        return self.email

    @property
    def portfolio(self) -> Optional["Portfolio"]:
        return self.portfolios.first()

    @property
    def contractor_company(self):
        """Return the user's first CONTRACTOR-type company, or None."""
        from app.Project.models import Company

        return self.companies.filter(type=Company.Type.CONTRACTOR).first()

    def has_project_role(
        self: "Account", project: "Project", roles: list["Role"]
    ) -> bool:
        """
        Permission check if user has a specific role in a project.

        Args:
            project: The project to check
            role: The role to check (from Role choices)

        Returns:
            True if user has the role, False otherwise
        """
        from app.Account.subscription_config import Subscription
        from app.Project.models import Role

        if self.is_superuser or (
            self.subscription == Subscription.DEMO_TIER
            and not self.is_subscription_expired
        ):
            return True

        user_project_roles = project.project_roles.filter(user=self)
        if user_project_roles.filter(role__in=[Role.ADMIN, *roles]).exists():
            return True
        return False

    def has_subscription_tier(
        self: "Account", required_tiers: Iterable[Subscription | str] | None
    ) -> bool:
        """Check whether account satisfies any required subscription tier.

        Supports parent-tier inheritance, superuser bypass, and FREE_TIER bypass.
        """
        if not required_tiers:
            return True

        normalized_required_tiers = {
            str(tier).strip() for tier in required_tiers if str(tier).strip()
        }
        if not normalized_required_tiers:
            return True

        if self.is_superuser or self.subscription == Subscription.ADMINISTRATION:
            return True

        if self.subscription == Subscription.DEMO_TIER:
            if self.is_subscription_expired:
                return False
            # Demo tier bypasses requirement checks if not expired
            return True

        if str(Subscription.FREE_TIER) in normalized_required_tiers:
            return True

        current_tier = str(self.subscription)
        available_tiers: set[str] = set()
        parent_lookup = {
            str(tier): str(limits.parent) if limits.parent else None
            for tier, limits in SubscriptionConfig.LIMITS.items()
        }
        while current_tier and current_tier not in available_tiers:
            available_tiers.add(current_tier)
            current_tier = parent_lookup.get(current_tier)

        return bool(available_tiers & normalized_required_tiers)

    @property
    def get_projects(self: "Account") -> QuerySet["Project"]:
        from app.Project.models import Project

        if self.is_superuser:
            return Project.objects.all()
        return Project.objects.filter(
            Q(users=self) | Q(project_roles__user=self) | Q(is_demo=True)
        ).distinct()

    @property
    def get_clients(self: "Account") -> QuerySet["Company"]:
        from app.Project.models import Company

        if self.is_superuser:
            return Company.objects.filter(type=Company.Type.CLIENT)
        else:
            return Company.objects.filter(type=Company.Type.CLIENT, users=self)

    @property
    def get_contractors(self: "Account") -> QuerySet["Company"]:
        from app.Project.models import Company

        if self.is_superuser:
            return Company.objects.filter(type=Company.Type.CONTRACTOR)
        else:
            return Company.objects.filter(type=Company.Type.CONTRACTOR, users=self)

    @property
    def detail_url(self: "Account") -> str:
        return reverse("users:account:user_detail")

    @property
    def edit_url(self: "Account") -> str:
        return reverse("users:account:user_edit")

    # Subscription limit methods
    def get_subscription_limit(self, limit_name: str) -> int:
        """Get a specific limit for the user's subscription tier."""
        # Convert string subscription to Subscription enum
        try:
            subscription_tier = Subscription(self.subscription)
        except ValueError:
            subscription_tier = Subscription.FREE_TIER
        return SubscriptionConfig.get_limit(subscription_tier, limit_name)

    def can_create_project(self) -> bool:
        """Check if user can create more projects based on their subscription."""
        if self.is_superuser:
            return True

        max_projects = self.get_subscription_limit("max_projects")
        current_projects = self.get_projects.filter(is_demo=False).count()
        return current_projects < max_projects

    def can_add_user_to_project(self, project) -> bool:
        """Check if user can add more users to a project."""
        if self.is_superuser:
            return True

        max_users = self.get_subscription_limit("max_users_per_project")
        current_users = project.users.count()
        return current_users < max_users

    def has_subscription_feature(self, feature: str) -> bool:
        """Check if user's subscription includes a specific feature."""
        if self.is_superuser:
            return True
        # Convert string subscription to Subscription enum
        try:
            subscription_tier = Subscription(self.subscription)
        except ValueError:
            subscription_tier = Subscription.FREE_TIER
        return SubscriptionConfig.has_feature(subscription_tier, feature)

    @property
    def subscription_limits(self) -> dict:
        """Get all limits for the user's subscription tier."""
        # Convert string subscription to Subscription enum
        try:
            subscription_tier = Subscription(self.subscription)
        except ValueError:
            subscription_tier = Subscription.FREE_TIER
        return SubscriptionConfig.get_all_limits(subscription_tier)

    @property
    def is_subscription_expired(self) -> bool:
        """Check if the current subscription has expired."""
        if not self.subscription_expires_at:
            return False
        return timezone.now() > self.subscription_expires_at

    @property
    def demo_time_left_str(self) -> str:
        """Return a human-readable string of time left for demo."""
        if not self.subscription_expires_at:
            return "No expiry set"

        if self.is_subscription_expired:
            return "Expired"

        delta = self.subscription_expires_at - timezone.now()
        days = delta.days
        hours = delta.seconds // 3600

        if days > 0:
            return f"{days} day{'s' if days > 1 else ''} remaining"
        elif hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''} remaining"
        else:
            return "Expires very soon"
