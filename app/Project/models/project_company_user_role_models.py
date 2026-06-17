from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

from app.core.Utilities.models import BaseModel

if TYPE_CHECKING:
    pass


class StakeholderRole(models.TextChoices):
    ADMIN = "Admin", _("Admin")
    SUPERVISOR = "Supervisor", _("Supervisor")
    CAPTURER = "Capturer", _("Capturer")


class ProjectCompanyUserRole(BaseModel):
    """Model mapping a user, a project, a stakeholder company, and a specific stakeholder role."""

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="project_company_user_roles",
        help_text="The project associated with this stakeholder role",
    )
    company = models.ForeignKey(
        "Project.Company",
        on_delete=models.CASCADE,
        related_name="project_company_user_roles",
        help_text="The stakeholder company associated with this role",
    )
    user = models.ForeignKey(
        "Account.Account",
        on_delete=models.CASCADE,
        related_name="project_company_user_roles",
        help_text="The user assigned to this role",
    )
    role = models.CharField(
        max_length=50,
        choices=StakeholderRole.choices,
        default=StakeholderRole.CAPTURER,
        help_text="Stakeholder role (Admin, Supervisor, Capturer)",
    )

    class Meta:
        verbose_name = _("Project Company User Role")
        verbose_name_plural = _("Project Company User Roles")
        constraints = [
            models.UniqueConstraint(
                fields=["project", "company", "user"],
                name="unique_project_company_user_role",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.company.name} - {self.role} ({self.project.name})"
