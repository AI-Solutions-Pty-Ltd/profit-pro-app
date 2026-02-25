"""Photo Log model for tracking site photography."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class PhotoLog(BaseModel):
    """Track site photos and documentation."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="photo_logs",
        help_text="Project this photo log belongs to",
    )
    date = models.DateField(help_text="Date photo was taken")
    photo_reference = models.CharField(
        max_length=255, help_text="Photo reference or file name"
    )
    photo = models.ImageField(
        upload_to="site_photos/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text="Photo file",
    )
    description = models.TextField(help_text="Description of photo")
    location = models.CharField(
        max_length=255, help_text="Location where photo was taken"
    )
    taken_by = models.CharField(max_length=255, help_text="Person who took the photo")
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def __str__(self):
        return f"{self.photo_reference} - {self.date}"

    class Meta:
        verbose_name = "Photo Log"
        verbose_name_plural = "Photo Logs"
        ordering = ["-date", "-created_at"]
