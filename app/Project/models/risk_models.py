"""Models for Project Risk Management."""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from app.Account.models import Account
from app.core.Utilities.models import BaseModel


class Risk(BaseModel):
    """
    Risk management model for tracking project risks.

    Tracks time and cost impacts with probability assessments
    to calculate estimated risk exposure.
    """

    class RiskCategory(models.TextChoices):
        """Categories identifying the source of the risk."""

        CONSULTANT = "CONSULTANT", "Consultant"
        CLIENT = "CLIENT", "Client"
        CONTRACTOR = "CONTRACTOR", "Contractor"
        COMMUNITY = "COMMUNITY", "Community"
        LABOUR = "LABOUR", "Labour"
        OTHER = "OTHER", "Other"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="risks",
        help_text="Project this risk belongs to",
    )
    risk_number = models.PositiveIntegerField(
        editable=False,
        help_text="Auto-generated risk number within the project",
    )
    risk_name = models.CharField(
        max_length=255,
        help_text="Short name/title for the risk",
    )
    description = models.TextField(
        help_text="Detailed description of the risk",
    )
    category = models.CharField(
        max_length=20,
        choices=RiskCategory.choices,
        default=RiskCategory.OTHER,
        help_text="Category identifying the source of the risk",
    )
    # Time Impact
    time_impact_start = models.DateField(
        null=True,
        blank=True,
        help_text="Start date of potential time impact",
    )
    time_impact_end = models.DateField(
        null=True,
        blank=True,
        help_text="End date of potential time impact",
    )
    # Cost Impact
    cost_impact = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Potential cost impact in currency",
    )
    # Probability
    probability = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Probability of risk occurring (0-100%)",
    )
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the risk is active or resolved",
    )
    resolved_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when the risk was resolved",
    )
    resolved_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_risks",
        help_text="User who resolved this risk",
    )
    created_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_risks",
        help_text="User who created this risk",
    )

    class Meta:
        verbose_name = "Risk"
        verbose_name_plural = "Risks"
        ordering = ["-created_at"]
        unique_together = ["project", "risk_number"]
        indexes = [
            models.Index(fields=["project", "is_active"]),
            models.Index(fields=["project", "risk_number"]),
        ]

    def __str__(self) -> str:
        return f"R{self.risk_number:03d} - {self.risk_name}"

    def save(self, *args, **kwargs):
        """Auto-generate risk number on creation."""
        if not self.risk_number:
            # Get the max risk number for this project
            max_number = Risk.objects.filter(project=self.project).aggregate(
                max_num=models.Max("risk_number")
            )["max_num"]
            self.risk_number = (max_number or 0) + 1
        super().save(*args, **kwargs)

    @property
    def time_impact_days(self) -> int | None:
        """Calculate the number of days of time impact."""
        if self.time_impact_start and self.time_impact_end:
            delta = self.time_impact_end - self.time_impact_start
            return delta.days
        return None

    @property
    def estimated_cost_impact(self) -> Decimal:
        """Calculate estimated cost impact (cost × probability)."""
        if self.cost_impact and self.probability:
            return (self.cost_impact * self.probability) / Decimal("100")
        return Decimal("0.00")

    @property
    def estimated_time_impact_days(self) -> Decimal | None:
        """Calculate estimated time impact in days (days × probability)."""
        days = self.time_impact_days
        if days is not None and self.probability:
            return (Decimal(str(days)) * self.probability) / Decimal("100")
        return None

    @property
    def is_current(self) -> bool:
        """Check if the risk's time impact period includes today."""
        today = timezone.now().date()
        if self.time_impact_start and self.time_impact_end:
            return self.time_impact_start <= today <= self.time_impact_end
        return False

    def resolve(self, user: Account) -> None:
        """Mark the risk as resolved."""
        self.is_active = False
        self.resolved_date = timezone.now().date()
        self.resolved_by = user
        self.save(update_fields=["is_active", "resolved_date", "resolved_by"])

    def reactivate(self) -> None:
        """Reactivate a resolved risk."""
        self.is_active = True
        self.resolved_date = None
        self.resolved_by = None
        self.save(update_fields=["is_active", "resolved_date", "resolved_by"])
