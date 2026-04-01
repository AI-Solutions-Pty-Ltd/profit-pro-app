from django.db import models
from django.core.validators import MinValueValidator
from app.core.Utilities.models import BaseModel
from app.Project.models import Project

class SubcontractorCostLog(BaseModel):
    """Tracks subcontractor costs per project."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="subcontractor_costs")
    subcontractor_name = models.CharField(max_length=255)
    reference_no = models.CharField(max_length=100, blank=True, default="")
    days = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount of days", validators=[MinValueValidator(0)])
    rate = models.DecimalField(max_digits=15, decimal_places=2, help_text="Daily rate", validators=[MinValueValidator(0)])
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    class Meta:
        verbose_name = "Subcontractor Cost Log"
        verbose_name_plural = "Subcontractor Cost Logs"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        self.total_cost = (self.days or 0) * (self.rate or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subcontractor_name} - {self.project.name}"

class LabourCostLog(BaseModel):
    """Tracks additional/indirect labour costs per project."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="labour_cost_logs")
    worker_name = models.CharField(max_length=255)
    worker_id = models.CharField(max_length=50, blank=True, default="", help_text="Employee ID")
    days = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount of days", validators=[MinValueValidator(0)])
    salary_rate = models.DecimalField(max_digits=15, decimal_places=2, help_text="Salary/Rate", validators=[MinValueValidator(0)])
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    class Meta:
        verbose_name = "Labour Cost Log"
        verbose_name_plural = "Labour Cost Logs"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        self.total_cost = (self.days or 0) * (self.salary_rate or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.worker_name} - {self.project.name}"

class OverheadCostLog(BaseModel):
    """Tracks indirect/overhead costs per project."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="overhead_costs")
    description = models.CharField(max_length=255)
    days = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount of days", validators=[MinValueValidator(0)])
    rate = models.DecimalField(max_digits=15, decimal_places=2, help_text="Rate", validators=[MinValueValidator(0)])
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    class Meta:
        verbose_name = "Overhead Cost Log"
        verbose_name_plural = "Overhead Cost Logs"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        self.total_cost = (self.days or 0) * (self.rate or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} - {self.project.name}"
