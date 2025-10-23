from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.urls import reverse

from app.Account.models import Account
from app.core.Utilities.models import BaseModel


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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ["-created_at"]


class Project(BaseModel):
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    contract_number = models.CharField(max_length=255, blank=True)
    contract_clause = models.CharField(max_length=255, blank=True)
    vat = models.BooleanField(default=False)

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )

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
    def get_total_contract_value(self):
        line_items = self.line_items.all()
        total_contract_value = line_items.aggregate(total=Sum("total_price"))[
            "total"
        ] or Decimal(0)
        return total_contract_value

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

    @property
    def get_line_items(self):
        return self.line_items.select_related(
            "structure", "bill", "package"
        ).prefetch_related("actual_transactions")


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
