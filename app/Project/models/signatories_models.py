from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models.projects_models import Project


class Signatories(BaseModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="signatories"
    )
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    email = models.EmailField(
        max_length=255, help_text="Email address for sending payment certificates"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Signatory"
        verbose_name_plural = "Signatories"
        ordering = ["-created_at"]
