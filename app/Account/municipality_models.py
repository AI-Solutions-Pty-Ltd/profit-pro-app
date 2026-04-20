"""Municipality models."""

from django.db import models

from app.core.Utilities.models import BaseModel


class Municipality(BaseModel):
    province = models.CharField(max_length=255)
    municipality_name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)
    district = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Municipality"
        verbose_name_plural = "Municipalities"
        ordering = ["province", "municipality_name"]
        unique_together = ["province", "municipality_name", "code"]

    def __str__(self):
        return f"{self.municipality_name} ({self.code})"
