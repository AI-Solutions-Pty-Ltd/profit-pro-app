from django.db import models
from django.urls import reverse

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class Structure(BaseModel):
    """Structure model representing buildings/structures within a project."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="structures"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Structure"
        verbose_name_plural = "Structures"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.project.name})"

    def get_absolute_url(self):
        return reverse(
            "structure:structure-detail",
            kwargs={"pk": self.pk},
        )

    def get_update_url(self):
        return reverse(
            "structure:structure-update",
            kwargs={"pk": self.pk},
        )

    def get_delete_url(self):
        return reverse(
            "structure:structure-delete",
            kwargs={"pk": self.pk},
        )
