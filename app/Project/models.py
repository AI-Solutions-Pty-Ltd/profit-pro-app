from django.db import models
from django.urls import reverse

from app.Account.models import Account
from app.core.Utilities.models import BaseModel


class Client(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()


class Project(BaseModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()

    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)

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

    def get_structure_upload_url(self):
        return reverse(
            "bill_of_quantities:structure-upload", kwargs={"project_pk": self.pk}
        )

    @property
    def get_active_payment_certificate(self):
        from app.BillOfQuantities.models import PaymentCertificate

        try:
            return self.payment_certificates.get(
                status__in=[
                    PaymentCertificate.Status.DRAFT,
                    PaymentCertificate.Status.SUBMITTED,
                    PaymentCertificate.Status.REJECTED,
                ]
            )
        except Exception:
            return None
