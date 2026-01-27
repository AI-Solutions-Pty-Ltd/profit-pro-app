from typing import TYPE_CHECKING

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from app.core.Utilities.models import BaseModel

if TYPE_CHECKING:
    from app.Account.models import Account


class Role(models.TextChoices):
    # Admin can access anything, is created automatically on project create
    ADMIN = "Admin", "Admin"
    # User has most rights, but not all
    USER = "User", "User"

    # client roles
    CLIENT = "Client", "Client"
    CONSULTANT = "Consultant", "Consultant"

    # Portfolio Manager view project dashboard and data
    PORTFOLIO_MANAGER = "Portfolio Manager", "Portfolio Manager"
    # Portfolio User view project dashboard and data - TODO not sure if needed
    PORTFOLIO_USER = "Portfolio User", "Portfolio User"

    # per module rights
    # CONTRACTS MANAGEMENT
    CONTRACT_BOQ = "Contractor BOQ", "Contractor BOQ"
    ADDITIONAL_LINE_ITEMS = "Additional Line Items", "Additional Line Items"
    CONTRACT_VARIATIONS = "Contract Variations", "Contract Variations"
    CORRESPONDENCE = "Correspondence", "Correspondence"
    CONTRACT_DOCUMENTS = "Contract Documents", "Contract Documents"
    STAGE_GATE_APPROVALS = "Stage Gate Approvals", "Stage Gate Approvals"
    OTHER_DOCUMENTS = "Other Documents", "Other Documents"

    # FORECASTS
    FORECAST_HUB = "Forecast Hub", "Forecast Hub"
    COST_FORECASTS = "Cost Forecasts", "Cost Forecasts"
    TIME_FORECASTS = "Time Forecasts", "Time Forecasts"
    CASHFLOW_FORECASTS = "Cashflow Forecasts", "Cashflow Forecasts"
    EARNED_VALUES = "Earned Values", "Earned Values"
    RISK_MANAGEMENT = "Risk Management", "Risk Management"

    # PAYMENT CERTIFICATES
    PAYMENT_CERTIFICATES = "Payment Certificates", "Payment Certificates"
    ADVANCE_PAYMENTS = "Advance Payments", "Advance Payments"
    RETENTION = "Retention", "Retention"
    MATERIALS_ON_SITE = "Materials On Site", "Materials On Site"
    ESCALATION = "Escalation", "Escalation"
    SPECIAL_ITEMS = "Special Items", "Special Items"

    # OTHER
    # COMPLIANCE
    COMPLIANCE = "Compliance", "Compliance"

    # CONTRACTORS
    EXPENDITURE_MANAGEMENT = "Expenditure Management", "Expenditure Management"
    MATERIALS_MANAGEMENT = "Materials Management", "Materials Management"


CLAIMS_AND_CERTIFICATES_MODULE = [
    Role.ADMIN,
    Role.USER,
    Role.CONTRACT_BOQ,
    Role.PAYMENT_CERTIFICATES,
    Role.RETENTION,
    Role.CASHFLOW_FORECASTS,
    Role.COST_FORECASTS,
    Role.ADDITIONAL_LINE_ITEMS,
    Role.FORECAST_HUB,
]


class ProjectRole(BaseModel):
    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="project_roles",
    )
    role = models.CharField(max_length=255, choices=Role.choices)
    user = models.ForeignKey(
        "Account.Account",
        on_delete=models.CASCADE,
        related_name="project_roles",
        help_text="User who has this project role",
        null=True,
        blank=True,
    )

    if TYPE_CHECKING:
        users: models.QuerySet["Account"]

    class Meta:
        verbose_name = _("Project Role")
        verbose_name_plural = _("Project Roles")

    def __str__(self):
        return self.role

    def get_absolute_url(self):
        return reverse("_detail", kwargs={"pk": self.pk})
