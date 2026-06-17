"""Forms for Project app."""

from typing import cast

from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelChoiceField

from app.Account.models import Account
from app.core.Utilities.widgets import SearchableSelectWidget
from app.Project.company.company_forms import (
    CompanyForm,
    PrivacyModelMultipleChoiceField,
)
from app.Project.models import (
    AdministrativeCompliance,
    Company,
    ContractualCompliance,
    FinalAccountCompliance,
    PlannedValue,
    Project,
    Risk,
    Signatories,
)


class ProjectContractorForm(forms.ModelForm):
    """Form for updating the project contractor."""

    class Meta:
        model = Project
        fields = ["contractor"]
        widgets = {
            "contractor": SearchableSelectWidget(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                },
                create_url=True,
                resource_type="contractor",
            ),
        }
        labels = {
            "contractor": "Contractor",
        }
        help_texts = {
            "contractor": "Select the contractor company for this project",
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop("project", None)
        user: Account | None = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user:
            if user.has_demo_permission:
                Company.ensure_demo_companies(user=user)

            projects = user.get_projects

            # Filter to show contractor companies that are either associated with the user's projects or account
            from django.db.models import Q

            condition = Q(contractor_projects__in=projects) | Q(users=user)
            if user.has_demo_permission:
                condition |= Q(
                    registration_number__in=[
                        "DEMO-CONTRACTOR-1",
                        f"DEMO-CONTRACTOR-1-{user.pk}",
                    ]
                )

            queryset = (
                Company.objects.filter(
                    condition,
                    type=Company.Type.CONTRACTOR,
                )
                .distinct()
                .order_by("name")
            )

            # Type: ModelChoiceField has queryset attribute
            contractor_field = self.fields["contractor"]
            if hasattr(contractor_field, "queryset"):
                cast(ModelChoiceField, contractor_field).queryset = queryset.distinct()
        else:
            # Fallback for all contractor companies if user is not provided
            contractor_field = self.fields["contractor"]
            if hasattr(contractor_field, "queryset"):
                cast(
                    ModelChoiceField, contractor_field
                ).queryset = Company.objects.filter(
                    type=Company.Type.CONTRACTOR
                ).order_by("name")


class ProjectLeadConsultantForm(forms.Form):
    """Form for allocating a lead consultant to a project."""

    lead_consultant = forms.ModelChoiceField(
        queryset=Company.objects.none(),
        widget=SearchableSelectWidget(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
            },
            create_url=True,
            resource_type="lead_consultant",
        ),
        label="Lead Consultant",
        help_text="Select the lead consultant company for this project",
    )

    type = forms.ChoiceField(
        choices=[
            (Company.Type.LEAD_CONSULTANT, "Lead Consultant"),
            (Company.Type.CONSULTANT, "Consultant"),
        ],
        widget=forms.Select(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
            }
        ),
        label="Consultant Type",
        help_text="Specify whether this company should be assigned as a Lead Consultant or a regular Consultant",
        initial=Company.Type.LEAD_CONSULTANT,
    )

    def __init__(self, *args, **kwargs):
        kwargs.pop("project", None)
        user: Account | None = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user:
            if user.has_demo_permission:
                Company.ensure_demo_companies(user=user)

            projects = user.get_projects

            from django.db.models import Q

            condition = Q(consultant_projects__in=projects) | Q(users=user)
            if user.has_demo_permission:
                condition |= Q(
                    registration_number__in=[
                        "DEMO-CONSULTANT-1",
                        f"DEMO-CONSULTANT-1-{user.pk}",
                    ]
                )

            queryset = (
                Company.objects.filter(
                    condition,
                    type__in=[Company.Type.LEAD_CONSULTANT, Company.Type.CONSULTANT],
                )
                .distinct()
                .order_by("name")
            )
        else:
            queryset = Company.objects.filter(
                type__in=[Company.Type.LEAD_CONSULTANT, Company.Type.CONSULTANT]
            ).order_by("name")

        lead_consultant_field = self.fields["lead_consultant"]
        if hasattr(lead_consultant_field, "queryset"):
            cast(ModelChoiceField, lead_consultant_field).queryset = queryset.distinct()


class ProjectConsultantForm(forms.Form):
    """Form for allocating a regular consultant to a project."""

    consultant = forms.ModelChoiceField(
        queryset=Company.objects.none(),
        widget=SearchableSelectWidget(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
            },
            create_url=True,
            resource_type="consultant",
        ),
        label="Consultant",
        help_text="Select the consultant company for this project",
    )

    type = forms.ChoiceField(
        choices=[
            (Company.Type.LEAD_CONSULTANT, "Lead Consultant"),
            (Company.Type.CONSULTANT, "Consultant"),
        ],
        widget=forms.Select(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
            }
        ),
        label="Consultant Type",
        help_text="Specify whether this company should be assigned as a Lead Consultant or a regular Consultant",
        initial=Company.Type.CONSULTANT,
    )

    def __init__(self, *args, **kwargs):
        kwargs.pop("project", None)
        user: Account | None = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user:
            if user.has_demo_permission:
                Company.ensure_demo_companies(user=user)

            projects = user.get_projects

            from django.db.models import Q

            condition = Q(consultant_projects__in=projects) | Q(users=user)

            queryset = (
                Company.objects.filter(
                    condition,
                    type__in=[Company.Type.LEAD_CONSULTANT, Company.Type.CONSULTANT],
                )
                .distinct()
                .order_by("name")
            )
        else:
            queryset = Company.objects.filter(
                type__in=[Company.Type.LEAD_CONSULTANT, Company.Type.CONSULTANT]
            ).order_by("name")

        consultant_field = self.fields["consultant"]
        if hasattr(consultant_field, "queryset"):
            cast(ModelChoiceField, consultant_field).queryset = queryset.distinct()


class ClientCreateUpdateForm(forms.ModelForm):
    """Form for creating and updating clients."""

    class Meta:
        model = Company
        fields = ["name", "consultants"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter client name",
                }
            ),
            "consultants": forms.SelectMultiple(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
        }
        labels = {
            "name": "Client Name",
            "consultants": "Consultants",
        }
        help_texts = {
            "consultants": "Optional - Select a consultant for this client",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter consultants to only show users with type CONSULTANT
        consultant_users = Account.objects.filter(groups__name="consultant")
        cast(ModelChoiceField, self.fields["consultants"]).queryset = consultant_users
        self.fields["consultants"].required = False


class ClientUserInviteForm(forms.Form):
    """Form for inviting a user to a client."""

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "user@example.com",
            }
        ),
        label="Email Address",
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "John",
            }
        ),
        label="First Name",
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "Doe",
            }
        ),
        label="Last Name (Optional)",
    )
    primary_contact = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "+27123456789",
            }
        ),
        label="Phone Number",
    )


class SignatoryForm(forms.ModelForm):
    """Form for updating signatory sequence number."""

    class Meta:
        model = Signatories
        fields = ["sequence_number", "role", "user"]
        widgets = {
            "sequence_number": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "1",
                    "min": "1",
                }
            ),
            "role": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "user": SearchableSelectWidget(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                },
                create_url=True,
                resource_type="signatory_user",
            ),
        }
        labels = {
            "sequence_number": "Sequence Number",
            "role": "Role",
            "user": "User",
        }


class SignatoryInviteForm(forms.Form):
    """Form for inviting a user as a signatory."""

    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "Enter email address",
            }
        ),
    )
    first_name = forms.CharField(
        max_length=150,
        label="First Name",
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "Enter first name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Last Name",
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "Enter last name",
            }
        ),
    )
    primary_contact = forms.CharField(
        max_length=20,
        label="Phone Number",
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "+27 XX XXX XXXX",
            }
        ),
    )
    sequence_number = forms.IntegerField(
        min_value=1,
        label="Sequence Number",
        widget=forms.NumberInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "1",
                "min": "1",
            }
        ),
    )
    role = forms.CharField(
        max_length=50,
        label="Role",
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "Enter role",
            }
        ),
    )


class PlannedValueForm(forms.ModelForm):
    """Form for individual planned value entry."""

    class Meta:
        model = PlannedValue
        fields = ["value", "forecast_value"]
        widgets = {
            "value": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "forecast_value": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                }
            ),
        }
        labels = {
            "value": "Planned Value",
            "forecast_value": "Forecast Value",
        }


class CashflowForecastForm(forms.ModelForm):
    """Form for editing cashflow forecast values and work completed percentage."""

    class Meta:
        model = PlannedValue
        fields = ["forecast_value", "work_completed_percent"]
        widgets = {
            "forecast_value": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "work_completed_percent": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
        }
        labels = {
            "forecast_value": "Cashflow Forecast",
            "work_completed_percent": "% Work Completed",
        }


class RiskForm(forms.ModelForm):
    """Form for creating and updating project risks."""

    class Meta:
        model = Risk
        fields = [
            "description",
            "time_impact_days",
            "cost_impact",
            "probability",
            "mitigation_action",
            "status",
        ]
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Describe the risk in detail",
                    "rows": 3,
                }
            ),
            "time_impact_days": forms.NumberInput(
                attrs={
                    "placeholder": "0",
                    "min": "0",
                }
            ),
            "cost_impact": forms.NumberInput(
                attrs={
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            ),
            "probability": forms.NumberInput(
                attrs={
                    "placeholder": "0-100",
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                }
            ),
            "mitigation_action": forms.Textarea(
                attrs={
                    "placeholder": "Describe the actions to mitigate this risk",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "description": "Description of Risk",
            "time_impact_days": "Time Impact (Days)",
            "cost_impact": "Cost Impact (Amount)",
            "probability": "Probability of Impact (%)",
            "mitigation_action": "Mitigation Action",
            "status": "Status",
        }
        help_texts = {
            "time_impact_days": "Potential time impact in days",
            "cost_impact": "Potential cost impact in currency",
            "probability": "Probability of risk occurring (0-100%)",
        }


class ContractualComplianceForm(forms.ModelForm):
    """Form for creating and updating contractual compliance items."""

    class Meta:
        model = ContractualCompliance
        fields = [
            "obligation_description",
            "contract_reference",
            "responsible_party",
            "due_date",
            "frequency",
            "expiry_date",
            "status",
            "notes",
        ]
        widgets = {
            "obligation_description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Describe the contractual obligation",
                    "rows": 3,
                }
            ),
            "contract_reference": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "e.g., Clause 5.2.1",
                }
            ),
            "responsible_party": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "frequency": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "expiry_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "status": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Additional notes",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "obligation_description": "Obligation Description",
            "contract_reference": "Contract Reference",
            "responsible_party": "Responsible Party",
            "due_date": "Due Date",
            "frequency": "Frequency",
            "expiry_date": "Expiry Date",
            "status": "Status",
            "notes": "Notes",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cast(
            ModelChoiceField, self.fields["responsible_party"]
        ).queryset = Account.objects.filter(
            groups__name__in=["contractor", "consultant"]
        ).distinct()
        self.fields["responsible_party"].required = False


class AdministrativeComplianceForm(forms.ModelForm):
    """Form for creating and updating administrative compliance items."""

    class Meta:
        model = AdministrativeCompliance
        fields = [
            "item_type",
            "reference_number",
            "description",
            "responsible_party",
            "submission_due_date",
            "submission_date",
            "approval_due_date",
            "approval_date",
            "status",
            "notes",
        ]
        widgets = {
            "item_type": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "reference_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "e.g., CERT-001",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Describe the item",
                    "rows": 3,
                }
            ),
            "responsible_party": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "submission_due_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "submission_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "approval_due_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "approval_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "status": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Additional notes",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "item_type": "Item Type",
            "reference_number": "Reference Number",
            "description": "Description",
            "responsible_party": "Responsible Party",
            "submission_due_date": "Submission Due Date",
            "submission_date": "Actual Submission Date",
            "approval_due_date": "Approval Due Date",
            "approval_date": "Actual Approval Date",
            "status": "Status",
            "notes": "Notes",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cast(
            ModelChoiceField, self.fields["responsible_party"]
        ).queryset = Account.objects.filter(
            groups__name__in=["contractor", "consultant", "client"]
        ).distinct()
        self.fields["responsible_party"].required = False


class FinalAccountComplianceForm(forms.ModelForm):
    """Form for creating and updating final account compliance items."""

    class Meta:
        model = FinalAccountCompliance
        fields = [
            "document_type",
            "description",
            "responsible_party",
            "test_date",
            "submission_date",
            "approval_date",
            "status",
            "file",
            "notes",
        ]
        widgets = {
            "document_type": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Describe the document",
                    "rows": 3,
                }
            ),
            "responsible_party": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "test_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "submission_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "approval_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "status": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "file": forms.FileInput(
                attrs={
                    "class": "mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100",
                    "accept": ".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.zip",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Additional notes",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "document_type": "Document Type",
            "description": "Description",
            "responsible_party": "Responsible Party",
            "test_date": "Test/Inspection Date",
            "submission_date": "Submission Date",
            "approval_date": "Approval Date",
            "status": "Status",
            "file": "Attachment",
            "notes": "Notes",
        }
        help_texts = {
            "file": "Accepted formats: PDF, Word, Excel, Images, ZIP",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cast(
            ModelChoiceField, self.fields["responsible_party"]
        ).queryset = Account.objects.filter(
            groups__name__in=["contractor", "consultant"]
        ).distinct()
        self.fields["responsible_party"].required = False
        self.fields["file"].required = False


class ClientForm(forms.ModelForm):
    """Form for creating and editing companies."""

    users = PrivacyModelMultipleChoiceField(
        queryset=Account.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Client Users",
    )
    consultants = PrivacyModelMultipleChoiceField(
        queryset=Account.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Client Consultants",
    )

    class Meta:
        model = Company
        fields = [
            "logo",
            "name",
            "registration_number",
            "tax_number",
            "vat_registered",
            "vat_number",
            "users",
            "consultants",
        ]
        widgets = {
            "logo": forms.FileInput(
                attrs={
                    "class": "mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100",
                    "accept": "image/*",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter company name",
                }
            ),
            "registration_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter registration number",
                }
            ),
            "tax_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter tax number",
                }
            ),
            "vat_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter VAT number",
                }
            ),
        }

    def __init__(self, *args, contractor=False, client=False, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields.pop("users", None)
        else:
            self.fields["users"].queryset = Account.objects.exclude(
                first_name="", last_name=""
            ).order_by("first_name", "email")
        self.fields["consultants"].queryset = Account.objects.exclude(
            first_name="", last_name=""
        ).order_by("first_name", "email")

        # Apply masking to initial values when editing an existing instance
        if self.instance and self.instance.pk:
            sensitive_fields = [
                "registration_number",
                "tax_number",
                "vat_number",
            ]
            for field_name in sensitive_fields:
                raw_val = getattr(self.instance, field_name, "")
                if raw_val:
                    if len(raw_val) <= 4:
                        self.initial[field_name] = raw_val
                    else:
                        self.initial[field_name] = (
                            "•" * (len(raw_val) - 4) + raw_val[-4:]
                        )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data is None:
            return cleaned_data

        if (
            Company.objects.filter(name=cleaned_data["name"], type=Company.Type.CLIENT)
            .exclude(id=self.instance.id)
            .exists()
        ):
            raise forms.ValidationError("Client with this name already exists.")

    def clean_sensitive_field(self, field_name: str) -> str:
        submitted_val = self.cleaned_data.get(field_name, "")
        if submitted_val and "•" in submitted_val:
            return getattr(self.instance, field_name, "") if self.instance else ""
        return submitted_val

    def clean_registration_number(self):
        return self.clean_sensitive_field("registration_number")

    def clean_tax_number(self):
        return self.clean_sensitive_field("tax_number")

    def clean_vat_number(self):
        return self.clean_sensitive_field("vat_number")


class SignatoryLinkForm(forms.Form):
    """Form to link existing signatories to a project."""

    signatories: forms.ModelMultipleChoiceField = forms.ModelMultipleChoiceField(
        queryset=Account.objects.none(),
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "space-y-2",
            }
        ),
        required=False,
        help_text="Select existing users to add as signatories for this project.",
    )

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        if project:
            # Get all users who are signatories in any project
            from app.Project.models import Signatories

            all_signatory_user_ids = (
                Signatories.objects.filter(user__isnull=False)
                .values_list("user_id", flat=True)
                .distinct()
            )

            # Get users who are already signatories for this project
            existing_signatory_ids = project.signatories.filter(
                user__isnull=False
            ).values_list("user_id", flat=True)

            # Show users who are signatories elsewhere but not in this project
            signatories_field = self.fields["signatories"]
            assert isinstance(signatories_field, forms.ModelMultipleChoiceField)
            signatories_field.queryset = (
                Account.objects.filter(id__in=all_signatory_user_ids)
                .exclude(id__in=existing_signatory_ids)
                .order_by("first_name", "last_name")
            )


class ProjectUserCreateForm(forms.Form):
    """Form for creating a new project user."""

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "user@example.com",
            }
        )
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "John",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                "placeholder": "Doe (optional)",
            }
        ),
    )

    def clean_email(self):
        """Check if email already exists."""
        email = self.cleaned_data["email"]
        if Account.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "A user with this email address already exists in the system."
            )
        return email


class ClientQuickCreateForm(CompanyForm):
    """Quick create form for client companies."""

    def __init__(self, *args, **kwargs):
        kwargs["client"] = True
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.type = Company.Type.CLIENT
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ContractorQuickCreateForm(CompanyForm):
    """Quick create form for contractor companies."""

    def __init__(self, *args, **kwargs):
        kwargs["contractor"] = True
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.type = Company.Type.CONTRACTOR
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class LeadConsultantQuickCreateForm(CompanyForm):
    """Quick create form for lead consultant companies."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.type = Company.Type.LEAD_CONSULTANT
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ConsultantQuickCreateForm(CompanyForm):
    """Quick create form for regular consultant companies."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.type = Company.Type.CONSULTANT
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class UserQuickCreateForm(forms.ModelForm):
    """Quick create form for users."""

    class Meta:
        model = Account
        fields = ["email", "first_name", "last_name", "primary_contact"]
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "email@example.com",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "First Name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Last Name",
                }
            ),
            "primary_contact": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "+27...",
                }
            ),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Set a random password for invited users
        instance.set_password(Account.objects.make_random_password())
        if commit:
            instance.save()
        return instance
