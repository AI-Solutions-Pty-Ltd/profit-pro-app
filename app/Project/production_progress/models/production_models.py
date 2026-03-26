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
    duration = models.IntegerField(default=0, help_text="Duration in days")

    class Meta:
        verbose_name = "Production Plan"
        verbose_name_plural = "Production Plans"
        ordering = ["start_date"]

    def __str__(self):
        return f"{self.project.name} - {self.activity}"

    def save(self, *args, **kwargs):
        if self.start_date and self.finish_date:
            self.duration = (self.finish_date - self.start_date).days
        else:
            self.duration = 0
        super().save(*args, **kwargs)

    @property
    def total_labour_cost(self):
        return self.resources.filter(resource_type='LABOUR').aggregate(total=models.Sum('total_cost'))['total'] or 0

    @property
    def total_plant_cost(self):
        return self.resources.filter(resource_type='PLANT').aggregate(total=models.Sum('total_cost'))['total'] or 0

    @property
    def total_other_cost(self):
        return self.resources.filter(resource_type='RESOURCE').aggregate(total=models.Sum('total_cost'))['total'] or 0


class ProductionResource(BaseModel):
    RESOURCE_TYPES = [
        ('LABOUR', 'Labour'),
        ('PLANT', 'Plant/Equipment'),
        ('RESOURCE', 'Other Resource'),
    ]
    
    production_plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, related_name="resources")
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    name = models.CharField(max_length=255, help_text="e.g., Skilled, Bobcat, Diesel")
    number = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    days = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    rate = models.DecimalField(max_digits=15, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    class Meta:
        verbose_name = "Production Resource"
        verbose_name_plural = "Production Resources"

    def __str__(self):
        return f"{self.resource_type} - {self.name} ({self.production_plan.activity})"

    def save(self, *args, **kwargs):
        self.total_cost = (self.number or 0) * (self.days or 0) * (self.rate or 0)
        super().save(*args, **kwargs)
