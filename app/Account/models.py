"""Account models."""

from typing import TYPE_CHECKING, Any, Optional

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from app.core.Utilities.models import BaseModel

if TYPE_CHECKING:
    from app.Project.models import Portfolio, Project


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(
        self, email: str, password: str | None, **extra_fields: dict[str, Any]
    ):
        if not email:
            raise ValueError("Users require an email field")
        normalized_email = self.normalize_email(email)
        user = self.model(email=normalized_email, **extra_fields)
        user.set_password(password)  # type: ignore
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

    username = None  # type: ignore # override username field from AbstractUser, we are not using username as unique field, but email override email field from AbstractUser to make it required
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

    objects = UserManager()  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    if TYPE_CHECKING:
        projects: QuerySet[Project]
        portfolios: QuerySet[Portfolio]
        contractor_projects: QuerySet[Project]
        qs_projects: QuerySet[Project]
        lead_consultant_projects: QuerySet[Project]
        client_rep_projects: QuerySet[Project]

    def __str__(self):
        return self.email

    @property
    def portfolio(self) -> Optional["Portfolio"]:
        return self.portfolios.first()
