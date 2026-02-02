"""Forms for Project app."""

from django import forms

from app.Account.models import Account
from app.Project.models import (
    AdministrativeCompliance,
    Company,
    ContractualCompliance,
    FinalAccountCompliance,
    Milestone,
    PlannedValue,
    Project,
    ProjectCategory,
    ProjectDocument,
    Risk,
    Signatories,
)


class FilterForm(forms.Form):
    """Form for filtering projects."""

    search = forms.CharField(required=False)
    category = forms.ModelChoiceField(
        queryset=ProjectCategory.objects.all(),
        required=False,
        empty_label="All Categories",
    )
    status = forms.ChoiceField(
        choices=[("ALL", "All Statuses")] + list(Project.Status.choices),
        required=False,
        initial="ALL",
    )
    active_projects = forms.BooleanField(required=False)
    projects = forms.ModelChoiceField(
        queryset=Project.objects.none(),
        required=False,
    )
    consultant = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        required=False,
        empty_label="All Consultants",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["active_projects"].label = "Active Projects"
        self.fields["search"].widget = forms.TextInput(
            attrs={
                "class": "block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors",
                "placeholder": "Search projects...",
            }
        )
        self.fields["category"].widget = forms.Select(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 text-sm focus:ring-indigo-500 focus:border-indigo-500 transition-colors",
            }
        )
        self.fields["status"].widget = forms.Select(
            attrs={
                "class": "block w-full rounded-lg border-gray-300 text-sm focus:ring-indigo-500 focus:border-indigo-500 transition-colors",
            }
        )
        # Set projects and consultant querysets based on user
        if user:
            user_projects = Project.objects.filter(
                users=user,
                status__in=[Project.Status.ACTIVE, Project.Status.FINAL_ACCOUNT_ISSUED],
            )
            self.fields["projects"].queryset = user_projects.order_by("name")  # type: ignore
            # Get unique lead consultants from user's projects
            consultant_ids = (
                user_projects.filter(lead_consultants__isnull=False)
                .values_list("lead_consultants", flat=True)
                .distinct()
            )
            self.fields["consultant"].queryset = Account.objects.filter(  # type: ignore
                pk__in=consultant_ids
            ).order_by("first_name", "last_name")


class ProjectCategoryForm(forms.ModelForm):
    """Form for creating and updating project categories."""

    class Meta:
        model = ProjectCategory
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter category name (e.g., Education, Health)",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Optional description of this category",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "name": "Category Name",
            "description": "Description (Optional)",
        }


class ProjectForm(forms.ModelForm):
    """Form for creating and updating projects."""

    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "logo",
            "category",
            "start_date",
            "end_date",
            "contract_number",
            "contract_clause",
            "status",
            "vat",
            "payment_terms",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter project name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter project description",
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
            "contract_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter contract number",
                }
            ),
            "contract_clause": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter contract clause",
                    "rows": 3,
                }
            ),
            "logo": forms.FileInput(
                attrs={
                    "class": "mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100",
                    "accept": ".jpg,.jpeg,.png,.gif,.svg",
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "vat": forms.CheckboxInput(
                attrs={
                    "class": "w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500",
                }
            ),
            "payment_terms": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
        }
        labels = {
            "name": "Project Name",
            "description": "Description",
            "logo": "Project Logo",
            "start_date": "Start Date",
            "end_date": "End Date",
            "contract_number": "Payment Certificate Contract Number",
            "contract_clause": "Payment Certificate Contract Clause",
            "bank_name": "Bank Name",
            "bank_account_name": "Account Name",
            "bank_account_number": "Account Number",
            "bank_branch_code": "Branch Code",
            "bank_swift_code": "SWIFT Code",
            "vat_number": "VAT/Tax Number",
            "payment_terms": "Payment Terms",
        }
        help_texts = {
            "logo": "Upload a logo for invoices and documents (JPG, PNG, GIF, SVG). Recommended size: 900x600px",
            "category": "Select the project category",
        }

    def clean(self):
        """Validate that end_date is after start_date."""
        cleaned_data = super().clean() or {}
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date must be after start date.")

        return cleaned_data


class ProjectContractorForm(forms.ModelForm):
    """Form for updating the project contractor."""

    class Meta:
        model = Project
        fields = ["contractor"]
        widgets = {
            "contractor": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
        }
        labels = {
            "contractor": "Contractor",
        }
        help_texts = {
            "contractor": "Select the contractor company for this project",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to only show contractor companies
        self.fields["contractor"].queryset = Company.objects.filter(  # type: ignore
            type="CONTRACTOR"
        ).order_by("name")


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
        self.fields["consultants"].queryset = consultant_users  # type: ignore
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
            "user": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
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


class MilestoneForm(forms.ModelForm):
    """Form for creating and updating milestones."""

    class Meta:
        model = Milestone
        fields = [
            "name",
            "planned_date",
            "forecast_date",
            "reason_for_change",
            "sequence",
            "is_completed",
            "actual_date",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter milestone name",
                }
            ),
            "planned_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "forecast_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "reason_for_change": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter reason for change in forecast date",
                    "rows": 3,
                }
            ),
            "sequence": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "min": "0",
                }
            ),
            "is_completed": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded",
                }
            ),
            "actual_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
        }
        labels = {
            "name": "Milestone Name",
            "planned_date": "Planned Date (Baseline)",
            "forecast_date": "Forecast Date",
            "reason_for_change": "Reason for Change",
            "sequence": "Order/Sequence",
            "is_completed": "Completed",
            "actual_date": "Actual Completion Date",
        }
        help_texts = {
            "planned_date": "Original planned completion date",
            "forecast_date": "Current forecast completion date (leave blank if same as planned)",
            "reason_for_change": "Explain why the forecast date differs from the planned date",
            "sequence": "Order in which milestones should appear (0 = first)",
        }

    def clean(self):
        """Validate milestone dates."""
        cleaned_data = super().clean() or {}
        planned_date = cleaned_data.get("planned_date")
        forecast_date = cleaned_data.get("forecast_date")
        is_completed = cleaned_data.get("is_completed")
        actual_date = cleaned_data.get("actual_date")
        reason_for_change = cleaned_data.get("reason_for_change")

        # Require reason if forecast differs from planned
        if forecast_date and planned_date and forecast_date != planned_date:
            if not reason_for_change:
                self.add_error(
                    "reason_for_change",
                    "Reason is required when forecast date differs from planned date.",
                )

        # Require actual date if completed
        if is_completed and not actual_date:
            self.add_error(
                "actual_date",
                "Actual completion date is required when milestone is marked as completed.",
            )

        return cleaned_data


class ProjectDocumentForm(forms.ModelForm):
    """Form for uploading project documents."""

    class Meta:
        model = ProjectDocument
        fields = ["category", "title", "file", "notes"]
        widgets = {
            "category": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter document title",
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
                    "placeholder": "Optional notes about this document",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "category": "Document Category",
            "title": "Document Title",
            "file": "File",
            "notes": "Notes (Optional)",
        }
        help_texts = {
            "file": "Accepted formats: PDF, Word, Excel, Images, ZIP",
        }


class RiskForm(forms.ModelForm):
    """Form for creating and updating project risks."""

    class Meta:
        model = Risk
        fields = [
            "risk_name",
            "description",
            "time_impact_start",
            "time_impact_end",
            "cost_impact",
            "probability",
            "is_active",
        ]
        widgets = {
            "risk_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter risk name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Describe the risk in detail",
                    "rows": 3,
                }
            ),
            "time_impact_start": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "time_impact_end": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "cost_impact": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            ),
            "probability": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "0-100",
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500",
                }
            ),
        }
        labels = {
            "risk_name": "Risk Name",
            "description": "Risk Description",
            "time_impact_start": "Time Impact Start Date",
            "time_impact_end": "Time Impact End Date",
            "cost_impact": "Cost Impact",
            "probability": "Probability (%)",
            "is_active": "Active",
        }
        help_texts = {
            "time_impact_start": "Start date of potential time impact period",
            "time_impact_end": "End date of potential time impact period",
            "cost_impact": "Potential cost impact in currency",
            "probability": "Probability of risk occurring (0-100%)",
            "is_active": "Uncheck to mark risk as resolved",
        }

    def clean(self):
        """Validate risk dates."""
        cleaned_data = super().clean() or {}
        start_date = cleaned_data.get("time_impact_start")
        end_date = cleaned_data.get("time_impact_end")

        # Validate date range
        if start_date and end_date:
            if end_date < start_date:
                self.add_error(
                    "time_impact_end",
                    "End date must be after or equal to start date.",
                )

        return cleaned_data


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
        self.fields["responsible_party"].queryset = Account.objects.filter(  # type: ignore
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
        self.fields["responsible_party"].queryset = Account.objects.filter(  # type: ignore
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
        self.fields["responsible_party"].queryset = Account.objects.filter(  # type: ignore
            groups__name__in=["contractor", "consultant"]
        ).distinct()
        self.fields["responsible_party"].required = False
        self.fields["file"].required = False


class CompanyForm(forms.ModelForm):
    """Form for creating and editing companies."""

    class Meta:
        model = Company
        fields = [
            "logo",
            "name",
            "registration_number",
            "tax_number",
            "vat_registered",
            "vat_number",
            "bank_name",
            "bank_account_name",
            "bank_account_number",
            "bank_branch_code",
            "bank_swift_code",
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
            "bank_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter bank name",
                }
            ),
            "bank_account_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter account holder name",
                }
            ),
            "bank_account_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter account number",
                }
            ),
            "bank_branch_code": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter branch code",
                }
            ),
            "bank_swift_code": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter SWIFT/BIC code",
                }
            ),
            "users": forms.SelectMultiple(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "consultants": forms.SelectMultiple(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
        }

    def __init__(self, *args, contractor=False, client=False, **kwargs):
        super().__init__(*args, **kwargs)
        # For contractors, only show users field (not consultants)
        self.fields.pop("consultants", None)
        self.fields["users"].label = "Company Users"

    def save(self, commit=True):
        """Save the instance, discarding VAT number if VAT registered is not selected."""
        instance = super().save(commit=False)

        # If VAT registered is not checked, clear the VAT number
        if not instance.vat_registered:
            instance.vat_number = ""

        if commit:
            instance.save()

        return instance


class ClientForm(forms.ModelForm):
    """Form for creating and editing companies."""

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
            "users": forms.SelectMultiple(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "consultants": forms.SelectMultiple(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
        }

    def __init__(self, *args, contractor=False, client=False, **kwargs):
        super().__init__(*args, **kwargs)

        # For clients, show both users and consultants fields
        self.fields["users"].label = "Client Users"
        self.fields["consultants"].label = "Client Consultants"


class ProjectClientForm(forms.Form):
    """Form to select a client for a project."""

    client = forms.ModelChoiceField(
        queryset=Company.objects.filter(type=Company.Type.CLIENT),
        widget=forms.Select(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
            }
        ),
        required=False,
        help_text="Select a client company to associate with this project.",
    )

    def __init__(self, *args, **kwargs):
        # Pop instance before calling super() to avoid passing it to Form
        self.instance = kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)
        self.fields["client"].label = "Client Company"


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
