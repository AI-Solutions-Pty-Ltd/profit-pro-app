"""Models for Order Amendments (Contract Variations).

This module contains models for tracking contract order amendments,
including variation amounts, categories, and approval status.
"""

from django.db import models

from app.core.Utilities.models import BaseModel


class OrderAmendment(BaseModel):
    """
    Register of contract order amendments per project.

    Used to track variations to the original contract value,
    including scope changes, design changes, delay costs, etc.
    """

    class Category(models.TextChoices):
        """Category choices for amendments."""

        SCOPE_CHANGE = "scope_change", "Scope Change"
        DESIGN_CHANGE = "design_change", "Design Change"
        RATE_ADJUSTMENT = "rate_adjustment", "Rate Adjustment"
        QUANTITY_VARIANCE = "quantity_variance", "Quantity Variance"
        DELAY_COSTS = "delay_costs", "Delay Costs"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        """Status choices for amendments."""

        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="order_amendments",
        help_text="Project this amendment belongs to",
    )
    amendment_number = models.CharField(
        max_length=50,
        help_text="Amendment number (e.g., 1, 2, A, B)",
    )
    name = models.CharField(
        max_length=200,
        help_text="Short name for the amendment",
    )
    description = models.TextField(
        help_text="Detailed description of the amendment",
    )
    justification = models.TextField(
        blank=True,
        help_text="Justification for the amendment",
    )
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.OTHER,
        help_text="Category of the amendment",
    )
    variation_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Variation amount in project currency (positive or negative)",
    )
    date_approved = models.DateField(
        null=True,
        blank=True,
        help_text="Date the amendment was approved",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Current status of the amendment",
    )
    approved_by = models.ForeignKey(
        "Account.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_amendments",
        help_text="Person who approved the amendment",
    )

    class Meta:
        """Meta options for OrderAmendment model."""

        ordering = ["amendment_number"]
        verbose_name = "Order Amendment"
        verbose_name_plural = "Order Amendments"
        unique_together = ["project", "amendment_number"]

    def __str__(self):
        return f"Amendment {self.amendment_number} - {self.name} ({self.project.name})"

    @property
    def is_positive_variation(self):
        """Check if the variation is positive (increase)."""
        return self.variation_amount > 0

    @property
    def get_category_display_name(self):
        """Get the human-readable category name."""
        return self.Category(self.category).label
