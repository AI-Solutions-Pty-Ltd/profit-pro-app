import os
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from app.core.Utilities.image_resize import ImageResize
from app.core.Utilities.models import BaseModel

Account = get_user_model()

if TYPE_CHECKING:
    from app.Project.models import Project


def company_logo_upload_path(instance, filename):
    """Dynamic upload path for company logos based on company type and ID."""
    # Ensure instance has an ID
    base_filename = os.path.basename(filename)
    return f"{instance.type.lower()}_logos/{instance.pk}/{base_filename}"


class Company(BaseModel):
    class Type(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        CONTRACTOR = "CONTRACTOR", "Contractor"

    type = models.CharField(max_length=255, choices=Type.choices)
    logo = models.ImageField(
        upload_to=company_logo_upload_path,
        blank=True,
        null=True,
        help_text="Company logo (recommended size: 200x200px)",
    )
    name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=255)
    tax_number = models.CharField(max_length=255, blank=True)
    vat_registered = models.BooleanField(default=False)
    vat_number = models.CharField(max_length=255, blank=True)

    # Banking Details
    bank_name = models.CharField(
        max_length=255, blank=True, help_text="Bank name for payments"
    )
    bank_account_name = models.CharField(
        max_length=255, blank=True, help_text="Account holder name"
    )
    bank_account_number = models.CharField(
        max_length=50, blank=True, help_text="Bank account number"
    )
    bank_branch_code = models.CharField(
        max_length=20, blank=True, help_text="Bank branch code"
    )
    bank_swift_code = models.CharField(
        max_length=20, blank=True, help_text="SWIFT/BIC code for international payments"
    )
    users = models.ManyToManyField(
        Account,
        blank=True,
        related_name="companies",
    )
    consultants = models.ManyToManyField(
        Account,
        blank=True,
        related_name="consultants",
    )

    if TYPE_CHECKING:
        contractor_projects: models.QuerySet["Project"]
        client_projects: models.QuerySet["Project"]

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the instance."""
        if self.pk:
            old_instance = Company.objects.get(pk=self.pk)
            if old_instance.logo != self.logo:
                # Logo field has changed
                self.logo = ImageResize().resize_image(self.logo)

        if not self.pk:
            logo = ImageResize().resize_image(self.logo)
            super().save(*args, **kwargs)  # set pk, save without logo
            self.logo = logo
        return super().save(*args, **kwargs)


@receiver(post_save, sender=Company)
def resize_company_logo(sender, instance, created, **kwargs):
    """Resize company logo after save if it was updated."""
    # Check if logo exists and needs resizing
    if instance.logo and not getattr(instance, "_logo_resized", False):
        # Mark as resized to avoid infinite loop
        instance._logo_resized = True
        instance._logo_being_updated = True

        # Resize the logo
        resized_logo = ImageResize().resize_image(instance.logo)

        # Save the resized logo without triggering signal again
        Company.objects.filter(pk=instance.pk).update(logo=resized_logo)
