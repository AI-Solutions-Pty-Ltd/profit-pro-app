from django.db import models
from app.core.Utilities.models import BaseModel
from app.Project.models import Project

class DailyProduction(BaseModel):
    """Tracks notes for a project."""
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="daily_productions")
    notes = models.TextField(blank=True, help_text="Optional remarks/notes")

    class Meta:
        verbose_name = "Daily Production"
        verbose_name_plural = "Daily Productions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project.name} - Note ({self.pk})"


class ProductionPlan(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="production_plans")
    activity = models.CharField(max_length=255)
    start_date = models.DateField()
    finish_date = models.DateField()
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Production Plan"
        verbose_name_plural = "Production Plans"
        ordering = ["start_date"]

    def __str__(self):
        return f"{self.project.name} - {self.activity}"

    @property
    def duration(self):
        if self.start_date and self.finish_date:
            return (self.finish_date - self.start_date).days
        return 0
