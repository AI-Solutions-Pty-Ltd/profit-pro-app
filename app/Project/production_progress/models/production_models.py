from django.db import models
from django.utils import timezone
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
        # ('RESOURCE', 'Other Resource'),
    ]
    
    production_plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, related_name="resources")
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    skill_type = models.ForeignKey(
        "SiteManagement.SkillType", on_delete=models.SET_NULL, null=True, blank=True, related_name="production_resources"
    )
    plant_type = models.ForeignKey(
        "SiteManagement.PlantType", on_delete=models.SET_NULL, null=True, blank=True, related_name="production_resources"
    )
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
        if self.skill_type:
            self.name = self.skill_type.name
            self.rate = self.skill_type.hourly_rate
        elif self.plant_type:
            self.name = self.plant_type.name
            self.rate = self.plant_type.hourly_rate
            
        self.total_cost = (self.number or 0) * (self.days or 0) * (self.rate or 0)
        super().save(*args, **kwargs)

class DailyActivityReport(BaseModel):
    """Daily container for all activities performed on a specific date."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="daily_reports")
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, help_text="Optional site-wide remarks")

    class Meta:
        verbose_name = "Daily Activity Report"
        verbose_name_plural = "Daily Activity Reports"
        ordering = ["-date", "-created_at"]
        unique_together = ["project", "date"]

    def __str__(self):
        return f"{self.project.name} - {self.date}"


class DailyActivityEntry(BaseModel):
    """Specific activity performed during a daily report."""
    report = models.ForeignKey(DailyActivityReport, on_delete=models.CASCADE, related_name="entries")
    production_plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, related_name="daily_entries")
    quantity = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Daily Activity Entry"
        verbose_name_plural = "Daily Activity Entries"

    def __str__(self):
        return f"{self.production_plan.activity} on {self.report.date}"

    @property
    def day_number(self):
        """Calculates D1, D2 etc relative to the plan start date."""
        if self.report.date and self.production_plan.start_date:
            delta = (self.report.date - self.production_plan.start_date).days
            return f"D{delta + 1}"
        return "D?"

    @property
    def total_labour_cost(self):
        return sum(usage.total_cost for usage in self.labour_usage.all())

    @property
    def total_plant_cost(self):
        return sum(usage.total_cost for usage in self.plant_usage.all())

    @property
    def man_hours(self):
        return sum(usage.man_hours for usage in self.labour_usage.all())

    @property
    def total_cost(self):
        return self.total_labour_cost + self.total_plant_cost

    @property
    def work_productivity(self):
        mh = self.man_hours
        if mh > 0:
            return self.quantity / mh
        return 0

    @property
    def cost_per_item(self):
        if self.quantity > 0:
            return self.total_cost / self.quantity
        return 0


class DailyLabourUsage(BaseModel):
    """Tracks labour usage for a specific activity entry."""
    entry = models.ForeignKey(DailyActivityEntry, on_delete=models.CASCADE, related_name="labour_usage")
    resource = models.ForeignKey(ProductionResource, on_delete=models.CASCADE, limit_choices_to={'resource_type': 'LABOUR'})
    number = models.IntegerField(default=1)
    hours = models.DecimalField(max_digits=5, decimal_places=2, default=8)

    class Meta:
        verbose_name = "Daily Labour Usage"
        verbose_name_plural = "Daily Labour Usages"

    @property
    def total_cost(self):
        return (self.number or 0) * (self.hours or 0) * (self.resource.rate or 0)

    @property
    def man_hours(self):
        return (self.number or 0) * (self.hours or 0)


class DailyPlantUsage(BaseModel):
    """Tracks plant usage for a specific activity entry."""
    entry = models.ForeignKey(DailyActivityEntry, on_delete=models.CASCADE, related_name="plant_usage")
    resource = models.ForeignKey(ProductionResource, on_delete=models.CASCADE, limit_choices_to={'resource_type': 'PLANT'})
    number = models.IntegerField(default=1)
    hours = models.DecimalField(max_digits=5, decimal_places=2, default=8)

    class Meta:
        verbose_name = "Daily Plant Usage"
        verbose_name_plural = "Daily Plant Usages"

    @property
    def total_cost(self):
        return (self.number or 0) * (self.hours or 0) * (self.resource.rate or 0)
