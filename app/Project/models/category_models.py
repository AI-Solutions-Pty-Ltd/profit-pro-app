"""Project Category model for categorizing projects."""

from django.db import models

from app.core.Utilities.models import BaseModel


class ProjectCategory(BaseModel):
    """Category for classifying projects.

    Examples: Education, Health, Roads, Water & Sanitation, Social Development,
    Electricity, Housing, etc.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name (e.g., Education, Health, Roads)",
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the category",
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Project Category"
        verbose_name_plural = "Project Categories"
        ordering = ["name"]
