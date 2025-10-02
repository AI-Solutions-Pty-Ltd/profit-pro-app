from django.db import models
from django.urls import reverse

from app.Account.models import Account
from app.core.Utilities.models import BaseModel


class Project(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["-name"]

    def get_absolute_url(self):
        return reverse("project:project-detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_list_url():
        return reverse("project:project-list")

    @staticmethod
    def get_create_url():
        return reverse("project:project-create")

    def get_update_url(self):
        return reverse("project:project-update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse("project:project-delete", kwargs={"pk": self.pk})

    def get_structure_create_url(self):
        return reverse("structure:structure-create", kwargs={"project_pk": self.pk})

    def get_structure_upload_url(self):
        return reverse("structure:structure-upload", kwargs={"project_pk": self.pk})
