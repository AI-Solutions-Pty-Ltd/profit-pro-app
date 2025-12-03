from django.db import models

from app.Account.models import Account
from app.core.Utilities.models import BaseModel
from app.Project.models.projects_models import Project


class Signatories(BaseModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="signatories"
    )
    user = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="signatories",
    )
    role = models.CharField(max_length=50)
    sequence_number = models.PositiveIntegerField()

    def __str__(self: "Signatories") -> str:
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}"
        return "User Removed / Not Set"

    class Meta:
        verbose_name = "Signatory"
        verbose_name_plural = "Signatories"
        ordering = ["sequence_number"]
        indexes = [
            models.Index(fields=["project", "sequence_number"]),
        ]
