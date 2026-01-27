"""Models for Project Impact Tracking.

This module contains models for tracking social and economic impacts
including jobs, poverty eradication, local subcontracts, local spend, and ROI.
"""

from decimal import Decimal

from django.db import models

from app.Account.models import Account
from app.core.Utilities.models import BaseModel


class ProjectImpact(BaseModel):
    """
    Track social and economic impact metrics for a project.

    Covers Jobs, Poverty Eradication, Local Subcontracts, Local Spend and ROI.
    """

    class Demographic(models.TextChoices):
        """Demographic categories for impact tracking."""

        YOUTH = "YOUTH", "Youth"
        WOMEN = "WOMEN", "Women"
        DISABLED = "DISABLED", "People with Disabilities"
        MILITARY_VETERAN = "MILITARY_VETERAN", "Military Veteran"
        GENERAL = "GENERAL", "General"

    class Locality(models.TextChoices):
        """Locality levels for impact tracking."""

        LOCAL = "LOCAL", "Local"
        MUNICIPALITY = "MUNICIPALITY", "Municipality"
        PROVINCE = "PROVINCE", "Province"
        NATIONAL = "NATIONAL", "National"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="impacts",
        help_text="Project this impact record belongs to",
    )

    # Jobs Impact
    jobs_created = models.PositiveIntegerField(
        default=0,
        help_text="Number of jobs created",
    )
    jobs_retained = models.PositiveIntegerField(
        default=0,
        help_text="Number of jobs retained",
    )
    job_demographic = models.CharField(
        max_length=20,
        choices=Demographic.choices,
        default=Demographic.GENERAL,
        help_text="Primary demographic for jobs",
    )

    # Poverty Eradication
    poverty_beneficiaries = models.PositiveIntegerField(
        default=0,
        help_text="Number of poverty eradication beneficiaries",
    )
    poverty_spend = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Amount spent on poverty eradication initiatives",
    )

    # Local Subcontracts
    local_subcontract_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of local subcontracts awarded",
    )
    local_subcontract_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total value of local subcontracts",
    )

    # Local Spend
    local_spend_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Amount spent locally",
    )
    local_spend_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Percentage of total spend that is local",
    )

    # Locality tracking
    locality = models.CharField(
        max_length=20,
        choices=Locality.choices,
        default=Locality.LOCAL,
        help_text="Locality level for this impact record",
    )

    # Demographics tracking
    demographic = models.CharField(
        max_length=20,
        choices=Demographic.choices,
        default=Demographic.GENERAL,
        help_text="Primary demographic for this impact record",
    )

    # ROI (Return on Investment)
    investment_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total investment amount",
    )
    return_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total return amount",
    )

    # Period tracking
    period_start = models.DateField(
        null=True,
        blank=True,
        help_text="Start date of the impact period",
    )
    period_end = models.DateField(
        null=True,
        blank=True,
        help_text="End date of the impact period",
    )

    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional notes about this impact record",
    )
    created_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_impacts",
        help_text="User who created this record",
    )

    class Meta:
        verbose_name = "Project Impact"
        verbose_name_plural = "Project Impacts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "locality"]),
            models.Index(fields=["project", "demographic"]),
        ]

    def __str__(self) -> str:
        return f"{self.project.name} - {self.get_locality_display()} Impact"  # type: ignore

    @property
    def total_jobs(self) -> int:
        """Total jobs (created + retained)."""
        return self.jobs_created + self.jobs_retained

    @property
    def roi_percentage(self) -> Decimal | None:
        """Calculate ROI percentage."""
        if self.investment_amount and self.investment_amount > 0:
            return (
                (self.return_amount - self.investment_amount)
                / self.investment_amount
                * 100
            )
        return None
