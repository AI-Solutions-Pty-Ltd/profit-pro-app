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


class Bill(BaseModel):
    structure = models.ForeignKey(
        Structure, on_delete=models.CASCADE, related_name="bills"
    )
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Bill"
        verbose_name_plural = "Bills"

    def __str__(self):
        return self.name


class Package(BaseModel):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="packages")
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Package"
        verbose_name_plural = "Packages"

    def __str__(self):
        return self.name


class LineItem(BaseModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="line_items"
    )
    structure = models.ForeignKey(
        Structure, on_delete=models.CASCADE, related_name="line_items"
    )
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="line_items")
    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        related_name="line_items",
        null=True,
        blank=True,
    )
    row_index = models.IntegerField()

    # headings / etc
    item_number = models.CharField(max_length=100, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    # for work line items
    is_work = models.BooleanField(default=False)
    unit_measurement = models.CharField(max_length=10, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    budgeted_quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)

    # for addendum line items
    addendum = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Line Item"
        verbose_name_plural = "Line Items"
        ordering = ["row_index"]

    def __str__(self):
        return self.item_number
