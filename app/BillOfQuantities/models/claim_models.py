"""Claims are estimated payment certificates (total only)

Used to compare against the actual payment certificate which can be used for evidence / trend reports
"""

from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.models import Project

if TYPE_CHECKING:
    from typing import Self


class Claim(BaseModel):
    """Used to compare against the actual payment certificate which can be used for evidence / trend reports"""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="claims"
    )
    period = models.DateField()
    estimated_claim = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(
        blank=True, default="", help_text="Additional notes or comments"
    )

    # Type annotations for Django's auto-created fields
    project_id: int

    class Meta:
        verbose_name = "Claim"
        verbose_name_plural = "Claims"
        ordering = ["-period"]

    def clean(self: "Self") -> None:

        super().clean()

        # Skip project setup check if project is not yet set (during form validation)
        if self.project_id and not self.project.setup:
            raise ValidationError(
                {
                    "project": "Project is not setup. Please setup the project before creating a claim"
                }
            )

        if self.project_id and self.period:
            if Claim.objects.filter(project=self.project, period=self.period).exclude(
                pk=self.pk
            ):
                raise ValidationError(
                    {"period": "Claim for this project and period already exists"}
                )

            if self.period < self.project.start_date:
                raise ValidationError(
                    {
                        "period": f"Period cannot be before project start date ({self.project.start_date})"
                    }
                )

            if self.period > self.project.end_date:
                raise ValidationError(
                    {
                        "period": f"Period cannot be after project end date ({self.project.end_date})"
                    }
                )

        if self.estimated_claim is not None and self.estimated_claim <= 0:
            raise ValidationError(
                {"estimated_claim": "Estimated claim must be greater than 0."}
            )

    def save(self, *args, **kwargs):
        self.period = self.period.replace(day=1)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.project} - {self.period.strftime('%B %Y')}: R{self.estimated_claim}"
        )
