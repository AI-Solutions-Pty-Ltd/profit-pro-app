"""Snag List model for tracking issues and defects."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class SnagList(BaseModel):
    """Track site issues and defects."""

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="snag_lists",
        help_text="Project this snag belongs to",
    )
    date_raised = models.DateField(help_text="Date issue was raised")
    location = models.CharField(max_length=255, help_text="Location of issue")
    issue_description = models.TextField(help_text="Description of the issue")
    raised_by = models.CharField(
        max_length=255, help_text="Person who raised the issue"
    )
    assigned_to = models.CharField(
        max_length=255, blank=True, help_text="Person assigned to fix"
    )
    deadline = models.DateField(
        blank=True, null=True, help_text="Deadline for resolution"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        help_text="Current status",
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def __str__(self):
        return f"{self.location} - {self.issue_description[:50]}"

    class Meta:
        verbose_name = "Snag List"
        verbose_name_plural = "Snag Lists"
        ordering = ["-date_raised", "-created_at"]
