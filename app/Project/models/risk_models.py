"""Models for Project Risk Management."""

from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from app.Account.models import Account
from app.core.Utilities.models import BaseModel


class RiskStatus(models.TextChoices):
    """Status choices for risks."""

    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


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
    reference_number = models.CharField(
        max_length=50,
        editable=False,
        help_text="Auto-generated reference number",
    )
    risk_number = models.PositiveIntegerField(
        editable=False,
        help_text="Auto-generated risk number within the project",
    )
    date = models.DateField(
        auto_now_add=True,
        help_text="Date this risk was raised",
    )
    description = models.TextField(
        help_text="Description of risk",
    )
    raised_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="raised_risks",
        help_text="User who raised this risk",
    )
    # Time Impact (days)
    time_impact_days = models.PositiveIntegerField(
        default=0,
        help_text="Potential time impact in days",
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
        help_text="Probability of impact occurring (0-100%)",
    )
    mitigation_action = models.TextField(
        blank=True,
        help_text="Actions to mitigate this risk",
    )
    # Status
    status = models.CharField(
        max_length=10,
        choices=RiskStatus.choices,
        default=RiskStatus.OPEN,
        help_text="Current status of this risk",
    )
    date_closed = models.DateField(
        null=True,
        blank=True,
        editable=False,
        help_text="Date this risk was closed (auto-set)",
    )
    # Legacy / kept for backward compat
    is_active = models.BooleanField(
        default=True,
        editable=False,
        help_text="Whether the risk is active (derived from status)",
    )
    resolved_date = models.DateField(
        null=True,
        blank=True,
        editable=False,
        help_text="Date when the risk was resolved",
    )
    resolved_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="resolved_risks",
        help_text="User who resolved this risk",
    )
    created_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="created_risks",
        help_text="User who created this risk",
    )

    class Meta:
        verbose_name = "Risk"
        verbose_name_plural = "Risks"
        ordering = ["-created_at"]
        unique_together = ["project", "risk_number"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "risk_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.description[:50]}"

    def save(self, *args, **kwargs):
        """Auto-generate reference number and handle status timestamps."""
        if not self.risk_number:
            max_number = Risk.all_objects.filter(project=self.project).aggregate(
                max_num=models.Max("risk_number")
            )["max_num"]
            self.risk_number = (max_number or 0) + 1

        if not self.reference_number:
            self.reference_number = f"RR-{self.project.pk:04d}-{self.risk_number:04d}"

        if self.status == RiskStatus.CLOSED:
            self.is_active = False
            if not self.date_closed:
                self.date_closed = timezone.now().date()
        else:
            self.is_active = True
            self.date_closed = None

        super().save(*args, **kwargs)

    @property
    def estimated_cost_impact(self) -> Decimal:
        """Calculate estimated cost impact (cost × probability)."""
        if self.cost_impact and self.probability:
            return (self.cost_impact * self.probability) / Decimal("100")
        return Decimal("0.00")

    @property
    def estimated_time_impact_days(self) -> Decimal | None:
        """Calculate estimated time impact in days (days × probability)."""
        if self.time_impact_days and self.probability:
            return (Decimal(str(self.time_impact_days)) * self.probability) / Decimal(
                "100"
            )
        return None
