"""Skill Type model for labour logs."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class SkillType(BaseModel):
    """Categorize labour skills and associated hourly rates."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="skill_types",
        help_text="Project this skill type belongs to",
    )
    name = models.CharField(max_length=100, help_text="Skill type name (e.g., Skilled, Semi-Skilled, General)")
    hourly_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Hourly rate for this skill type",
    )

    def __str__(self):
        return f"{self.name} ({self.hourly_rate}/hr)"

    class Meta:
        verbose_name = "Skill Type"
        verbose_name_plural = "Skill Types"
        ordering = ["name"]
        unique_together = ["project", "name"]
