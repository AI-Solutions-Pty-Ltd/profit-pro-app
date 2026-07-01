import os
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import QuerySet
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
        LEAD_CONSULTANT = "LEAD_CONSULTANT", "Lead Consultant"
        CONSULTANT = "CONSULTANT", "Consultant"

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
    created_by = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_companies",
        help_text="User who created this company",
    )
    consultants = models.ManyToManyField(
        Account,
        blank=True,
        related_name="consultants",
    )
    disciplines = models.ManyToManyField(
        "Project.ProjectDiscipline",
        blank=True,
        related_name="companies",
        help_text="Disciplines of expertise for this company (if consultant)",
    )

    if TYPE_CHECKING:
        contractor_projects: QuerySet["Project"]
        client_projects: QuerySet["Project"]

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the instance."""
        if not self.logo:
            return super().save(*args, **kwargs)
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

    @classmethod
    def ensure_demo_companies(cls, user=None) -> list["Company"]:
        """Search for target demo companies and create them if they do not exist.

        If user is provided, prefixes the company names with the user's first name,
        and appends the user's pk to the registration numbers.

        Returns:
            list[Company]: The list of three ensured demo companies.
        """
        demo_companies = []
        if user:
            prefix = f"{user.first_name}'s " if user.first_name else "Demo "
            suffix = f"-{user.pk}"
            targets = [
                (cls.Type.CLIENT, f"{prefix}Demo Client", f"DEMO-CLIENT{suffix}"),
                (
                    cls.Type.CONTRACTOR,
                    f"{prefix}Demo Contractor 1",
                    f"DEMO-CONTRACTOR-1{suffix}",
                ),
                (
                    cls.Type.LEAD_CONSULTANT,
                    f"{prefix}Demo Consultant 1",
                    f"DEMO-CONSULTANT-1{suffix}",
                ),
            ]
        else:
            targets = [
                (cls.Type.CLIENT, "Demo Client", "DEMO-CLIENT"),
                (cls.Type.CONTRACTOR, "Demo Contractor 1", "DEMO-CONTRACTOR-1"),
                (cls.Type.LEAD_CONSULTANT, "Demo Consultant 1", "DEMO-CONSULTANT-1"),
            ]

        for comp_type, name, reg_num in targets:
            company, created = cls.objects.get_or_create(
                type=comp_type,
                registration_number=reg_num,
                defaults={"name": name, "created_by": user},
            )
            if not created:
                if company.name != name or (user and company.created_by != user):
                    company.name = name
                    if user:
                        company.created_by = user
                    company.save()

            if user:
                company.users.add(user)

            demo_companies.append(company)
        return demo_companies

    @classmethod
    def clean_demo_companies(cls, user) -> int:
        """Find and hard-delete all scoped demo companies for the given user.

        This safely triggers Django's on_delete=models.SET_NULL on associated Projects,
        clearing the user's project's client, contractor, and lead_consultant fields.

        Args:
            user (Account): The user whose demo companies to clean.

        Returns:
            int: The number of companies deleted.
        """
        if not user or not user.pk:
            return 0

        # Scoped demo companies registration numbers start with "DEMO-" and end with "-{user.pk}"
        # We query including soft-deleted ones (all_objects manager) to ensure complete purge
        targets = cls.all_objects.filter(
            registration_number__startswith="DEMO-",
            registration_number__endswith=f"-{user.pk}",
        )
        count = targets.count()
        targets.delete()
        return count


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
