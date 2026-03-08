from django.db import models

from app.core.Utilities.models import BaseModel


class Notice(BaseModel):
    """System notice shown to authenticated users."""

    text = models.TextField()

    def __str__(self) -> str:
        """Return a short display value for admin/list usage."""
        return self.text[:60]

    class Meta:
        verbose_name = "Notice"
        verbose_name_plural = "Notices"
        ordering = ["-created_at"]
