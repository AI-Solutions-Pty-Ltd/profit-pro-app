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
    class UnitMeasurement(models.TextChoices):
        meters = "m", "Meters"
        square_meters = "m2", "Square Meters"
        cubic_meters = "m3", "Cubic Meters"
        cubic_meters_per_kilometer = "m3.km", "Cubic Meters per Kilometer"
        grams = "g", "Grams"
        kilograms = "kg", "Kilograms"
        liters = "l", "Liters"
        tons = "t", "Tons"
        percentage = "%", "Percentage"
        quantity = "q", "Quantity"

    package = models.ForeignKey(
        Package, on_delete=models.CASCADE, related_name="line_items"
    )
    row_index = models.IntegerField()

    # headings / etc
    item_number = models.CharField(max_length=100)
    payment_reference = models.CharField(max_length=100)
    description = models.TextField()

    # for work line items
    is_work = models.BooleanField(default=False)
    unit_measurement = models.CharField(max_length=10, choices=UnitMeasurement.choices)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    budgeted_quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    addendum = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Line Item"
        verbose_name_plural = "Line Items"
        ordering = ["row_index"]

    def __str__(self):
        return self.item_number
