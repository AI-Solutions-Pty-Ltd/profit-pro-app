from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models.projects_models import Project


class PlannedValue(BaseModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="planned_values"
    )
    period = models.DateField()
    value = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.project}: {self.period}"

    def clean(self) -> None:
        """Normalize period to first day of month (mm-yyyy format)."""
        if self.period:
            self.period = self.period.replace(day=1)

    def save(self, **kwargs) -> None:
        self.clean()
        return super().save(**kwargs)

    class Meta:
        verbose_name = "Planned Value"
        verbose_name_plural = "Planned Values"
        ordering = ["period"]
        unique_together = [["project", "period"]]
