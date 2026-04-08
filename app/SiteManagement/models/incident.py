"""Incident / Near-Miss model for safety tracking."""

from django.db import models
from django.utils import timezone

from app.Account.models import Account
from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class IncidentStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class IncidentType(models.TextChoices):
    INCIDENT = "INCIDENT", "Incident"
    NEAR_MISS = "NEAR_MISS", "Near Miss"


class Incident(BaseModel):
    """Record safety incidents and near-misses on a project site."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="incidents",
        help_text="Project this incident belongs to",
    )
    reference_number = models.CharField(
        max_length=50,
        editable=False,
        blank=True,
        help_text="Auto-generated reference number",
    )
    incident_type = models.CharField(
        max_length=20,
        choices=IncidentType.choices,
        default=IncidentType.INCIDENT,
        help_text="Type of incident",
    )
    date = models.DateField(
        help_text="Date the incident occurred",
    )
    description = models.TextField(
        help_text="Detailed description of the incident",
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Location on site where the incident occurred",
    )
    root_cause = models.TextField(
        blank=True,
        help_text="Root cause analysis",
    )
    corrective_action = models.TextField(
        blank=True,
        help_text="Corrective action taken or planned",
    )
    corrective_action_date = models.DateField(
        null=True,
        blank=True,
        help_text="Target / actual date for corrective action completion",
    )
    reported_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_incidents",
        help_text="Person who reported the incident",
    )
    status = models.CharField(
        max_length=10,
        choices=IncidentStatus.choices,
        default=IncidentStatus.OPEN,
        help_text="Current status of this incident",
    )
    date_closed = models.DateField(
        null=True,
        blank=True,
        editable=False,
        help_text="Date this incident was closed (auto-set)",
    )

    class Meta:
        verbose_name = "Incident"
        verbose_name_plural = "Incidents"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "incident_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference_number} – {self.get_incident_type_display()} ({self.date})"  # type: ignore

    def save(self, *args, **kwargs) -> None:
        """Auto-generate reference number and handle status timestamps."""
        if not self.reference_number:
            count = Incident.all_objects.filter(project=self.project).count() + 1
            prefix = "INC" if self.incident_type == IncidentType.INCIDENT else "NM"
            self.reference_number = f"{prefix}-{self.project.pk:04d}-{count:04d}"

        if self.status == IncidentStatus.CLOSED and not self.date_closed:
            self.date_closed = timezone.now().date()
        elif self.status == IncidentStatus.OPEN:
            self.date_closed = None

        super().save(*args, **kwargs)
