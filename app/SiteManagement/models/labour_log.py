"""Labour Log model for tracking workers."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class LabourLog(BaseModel):
    """Track labour and workers on site."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="labour_logs",
        help_text="Project this labour log belongs to",
    )
    date = models.DateField(help_text="Date of work")
    person_name = models.CharField(max_length=255, help_text="Person's name")
    id_number = models.CharField(max_length=100, help_text="ID number")
    trade = models.CharField(max_length=100, help_text="Trade/specialty")
    hours_worked = models.DecimalField(
        max_digits=6, decimal_places=2, help_text="Hours worked"
    )
    task_activity = models.CharField(
        max_length=255, help_text="Task/Activity performed"
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def __str__(self):
        return f"{self.person_name} - {self.trade} - {self.date}"

    class Meta:
        verbose_name = "Labour Log"
        verbose_name_plural = "Labour Logs"
        ordering = ["-date", "-created_at"]
