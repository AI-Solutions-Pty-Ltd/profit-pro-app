"""Overhead Daily Log model for tracking project overheads."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class OverheadDailyLog(BaseModel):
    """Track daily overhead activities and costs."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="overhead_daily_logs",
        help_text="Project this overhead log belongs to",
    )
    overhead_entity = models.ForeignKey(
        "Project.OverheadEntity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="overhead_daily_logs",
        help_text="Link to master overhead definition",
    )
    date = models.DateField(help_text="Date of overhead activity")
    category = models.CharField(
        max_length=100, blank=True, editable=False, help_text="Overhead category"
    )
    description = models.CharField(
        max_length=255, blank=True, editable=False, help_text="Brief description"
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Quantity/Days tracked"
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def save(self, *args, **kwargs):
        """Synchronize fields from master entity if linked."""
        if self.overhead_entity:
            if not self.category:
                self.category = self.overhead_entity.category
            if not self.description:
                self.description = self.overhead_entity.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} - {self.date}"

    class Meta:
        verbose_name = "Overhead Daily Log"
        verbose_name_plural = "Overhead Daily Logs"
        ordering = ["-date", "-created_at"]
