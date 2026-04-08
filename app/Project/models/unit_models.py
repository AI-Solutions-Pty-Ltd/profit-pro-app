from django.db import models

from app.core.Utilities.models import BaseModel


class UnitOfMeasure(BaseModel):
    """
    Centralized model for Units of Measure.
    Supports conversion logic between units in the same category.
    """

    class Category(models.TextChoices):
        WEIGHT = "WEIGHT", "Weight/Mass"
        VOLUME = "VOLUME", "Volume"
        LENGTH = "LENGTH", "Length"
        AREA = "AREA", "Area"
        TIME = "TIME", "Time"
        COUNT = "COUNT", "Count/Quantity"
        OTHER = "OTHER", "Other"

    name = models.CharField(
        max_length=100, help_text="Full name of the unit (e.g., Kilogram)"
    )
    short_name = models.CharField(max_length=20, help_text="Abbreviation (e.g., kg)")
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
        help_text="The type of measurement this unit represents",
    )

    # Conversion logic
    # 1 [This Unit] = [conversion_factor] [reference_unit]
    # Example: 1 km = 1000 m (if m is the reference unit)
    conversion_factor = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        default=1.0,
        help_text="Multiplier to convert this unit to the reference unit",
    )
    reference_unit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_units",
        help_text="The base unit this unit is relative to. If null, this is the base unit.",
    )

    class Meta:
        verbose_name = "Unit of Measure"
        verbose_name_plural = "Units of Measure"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.short_name})"

    def convert_to_reference(self, value):
        """Convert a value in this unit to the reference unit."""
        return value * self.conversion_factor

    def convert_from_reference(self, value):
        """Convert a value from the reference unit to this unit."""
        if self.conversion_factor == 0:
            return 0
        return value / self.conversion_factor
