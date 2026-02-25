"""Safety Observation model for tracking safety issues."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class SafetyObservation(BaseModel):
    """Track safety observations and corrective actions."""

    class Category(models.TextChoices):
        UNSAFE_ACT = "UNSAFE_ACT", "Unsafe Act"
        UNSAFE_CONDITION = "UNSAFE_CONDITION", "Unsafe Condition"
        NEAR_MISS = "NEAR_MISS", "Near Miss"
        GOOD_PRACTICE = "GOOD_PRACTICE", "Good Practice"
        HAZARD = "HAZARD", "Hazard"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="safety_observations",
        help_text="Project this safety observation belongs to",
    )
    date = models.DateField(help_text="Date of observation")
    observation = models.TextField(help_text="Safety observation details")
    location = models.CharField(max_length=255, help_text="Location of observation")
    raised_by = models.CharField(
        max_length=255, help_text="Person who raised observation"
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        help_text="Category of observation",
    )
    corrective_action = models.TextField(
        blank=True, help_text="Corrective action taken"
    )
    closed_out = models.BooleanField(
        default=False, help_text="Whether observation has been closed out"
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def __str__(self):
        return f"{self.category} - {self.location} - {self.date}"

    class Meta:
        verbose_name = "Safety Observation"
        verbose_name_plural = "Safety Observations"
        ordering = ["-date", "-created_at"]
