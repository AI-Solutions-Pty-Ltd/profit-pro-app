"""Labour Log model for tracking workers."""

from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project


class LabourLog(BaseModel):
    """Track labour and workers on site."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="labour_logs",
        help_text="Project this labour log belongs to",
    )
    labour_entity = models.ForeignKey(
        "Project.LabourEntity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="labour_logs",
        help_text="Link to master labour definition",
    )
    date = models.DateField(help_text="Date of work")
    person_name = models.CharField(
        max_length=255, blank=True, help_text="Person's name"
    )
    id_number = models.CharField(max_length=100, blank=True, help_text="ID number")
    trade = models.CharField(max_length=100, blank=True, help_text="Trade/specialty")
    skill_type = models.ForeignKey(
        "SkillType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="labour_logs",
        help_text="Skill type of the worker",
    )
    hours_worked = models.DecimalField(
        max_digits=6, decimal_places=2, help_text="Hours worked"
    )
    task_activity = models.CharField(
        max_length=255, help_text="Task/Activity performed"
    )
    remarks = models.TextField(blank=True, help_text="Additional remarks")

    def save(self, *args, **kwargs):
        """Synchronize fields from master entity if linked."""
        if self.labour_entity:
            if not self.person_name:
                self.person_name = self.labour_entity.person_name
            if not self.id_number:
                self.id_number = self.labour_entity.id_number
            if not self.trade:
                self.trade = self.labour_entity.trade
            if not self.skill_type:
                self.skill_type = self.labour_entity.skill_type
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.person_name} - {self.trade} - {self.date}"

    class Meta:
        verbose_name = "Labour Log"
        verbose_name_plural = "Labour Logs"
        ordering = ["-date", "-created_at"]
