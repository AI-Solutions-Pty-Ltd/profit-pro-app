"""Account models."""

from typing import TYPE_CHECKING, Any, Optional

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from app.core.Utilities.models import BaseModel

if TYPE_CHECKING:
    from app.Project.models import Portfolio, Project
    from app.Project.models.project_roles import ProjectRole, Role


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

    username = None  # override username field from AbstractUser, we are not using username as unique field, but email override email field from AbstractUser to make it required
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

    objects: UserManager = UserManager()

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

    def __str__(self):
        return self.email

    @property
    def portfolio(self) -> Optional["Portfolio"]:
        return self.portfolios.first()

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
        from app.Project.models.project_roles import Role

        if self.is_superuser:
            return True

        user_project_roles = project.project_roles.filter(user=self)
        if user_project_roles.filter(role__in=[Role.ADMIN, *roles]).exists():
            return True
        return False

    @property
    def get_projects(self: "Account") -> QuerySet["Project"]:
        if self.is_superuser:
            # Import here to avoid circular import
            from app.Project.models import Project

            return Project.objects.all()
        project_roles = self.project_roles.all()
        # Get projects through project_roles relationship
        projects = []
        for pr in project_roles:
            projects.append(pr.project)
        # Return unique projects
        project_ids = [p.id for p in projects]
        if project_ids:
            # Import here to avoid circular import
            from app.Project.models import Project

            return Project.objects.filter(id__in=project_ids).distinct()
        # Return empty queryset if no projects
        from app.Project.models import Project

        return Project.objects.none()

    @property
    def detail_url(self: "Account") -> str:
        return reverse("users:account:user_detail")

    @property
    def edit_url(self: "Account") -> str:
        return reverse("users:account:user_edit")
