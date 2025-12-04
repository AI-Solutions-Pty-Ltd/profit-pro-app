from typing import TYPE_CHECKING

from django.db import models
from django.db.models import QuerySet

from app.Account.models import Account
from app.core.Utilities.models import BaseModel

if TYPE_CHECKING:
    from app.Project.models.projects_models import Project


class Client(BaseModel):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="client"
    )
    consultant = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultant",
    )
    description = models.TextField()
    if TYPE_CHECKING:
        projects: QuerySet["Project"]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ["-created_at"]
