"""Forms for Project app."""

from django import forms

from app.Account.models import Account
from app.Project.models import (
    Client,
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
                account=user,
                status__in=[Project.Status.ACTIVE, Project.Status.FINAL_ACCOUNT_ISSUED],
            )
            self.fields["projects"].queryset = user_projects.order_by("name")
            # Get unique lead consultants from user's projects
            consultant_ids = (
                user_projects.exclude(lead_consultant__isnull=True)
                .values_list("lead_consultant", flat=True)
                .distinct()
            )
            self.fields["consultant"].queryset = Account.objects.filter(
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
            "category",
            "start_date",
            "end_date",
            "contract_number",
            "contract_clause",
            "status",
            "contractor",
            "quantity_surveyor",
            "lead_consultant",
            "client_representative",
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
            "category": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "contractor": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "quantity_surveyor": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "lead_consultant": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "client_representative": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
        }
        labels = {
            "name": "Project Name",
            "description": "Description",
            "start_date": "Start Date",
            "end_date": "End Date",
            "contract_number": "Payment Certificate Contract Number",
            "contract_clause": "Payment Certificate Contract Clause",
            "contractor": "Contractor",
            "quantity_surveyor": "Quantity Surveyor",
            "lead_consultant": "Lead Consultant",
            "client_representative": "Client Representative",
        }
        help_texts = {
            "contractor": "Select the contractor responsible for the project",
            "quantity_surveyor": "Select the Quantity Surveyor for the project",
            "lead_consultant": "Select the Lead Consultant (e.g., Principal Agent)",
            "client_representative": "Select the Client Representative",
            "category": "Select the project category",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make team role fields optional
        self.fields["contractor"].required = False
        self.fields["quantity_surveyor"].required = False
        self.fields["lead_consultant"].required = False
        self.fields["client_representative"].required = False

        # Filter querysets by user groups
        self.fields["contractor"].queryset = Account.objects.filter(  # type: ignore
            groups__name="contractor"
        ).distinct()
        self.fields["quantity_surveyor"].queryset = Account.objects.filter(  # type: ignore
            groups__name__in=["consultant", "contractor"]
        ).distinct()
        self.fields["lead_consultant"].queryset = Account.objects.filter(  # type: ignore
            groups__name="consultant"
        ).distinct()
        self.fields["client_representative"].queryset = Account.objects.filter(  # type: ignore
            groups__name="client"
        ).distinct()

    def clean(self):
        """Validate that end_date is after start_date."""
        cleaned_data = super().clean() or {}
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date must be after start date.")

        return cleaned_data


class ClientForm(forms.ModelForm):
    """Form for creating and updating clients."""

    class Meta:
        model = Client
        fields = ["name", "description", "consultant"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter client name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter client description",
                    "rows": 3,
                }
            ),
            "consultant": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
        }
        labels = {
            "name": "Client Name",
            "description": "Description",
            "consultant": "Consultant",
        }
        help_texts = {
            "consultant": "Optional - Select a consultant for this client",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter consultants to only show users with type CONSULTANT
        consultant_users = Account.objects.filter(groups__name="consultant")
        self.fields["consultant"].queryset = consultant_users  # type: ignore
        self.fields["consultant"].required = False


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
