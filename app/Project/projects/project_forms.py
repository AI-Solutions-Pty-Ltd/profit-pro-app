"""Forms for Project app."""

from django import forms
from django.db.models import QuerySet

from app.Account.models import Account
from app.Project.models import (
    Company,
    Project,
    ProjectCategory,
    ProjectDiscipline,
    ProjectSubCategory,
)


class BasicProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "project_category",
            "project_sub_category",
            "project_discipline",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter project name",
                }
            ),
        }


class ProjectForm(forms.ModelForm):
    """Form for creating and updating projects."""

    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "logo",
            "project_category",
            "project_sub_category",
            "project_discipline",
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
                    "placeholder": "Enter project name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Enter project description (optional)",
                    "rows": 3,
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "contract_number": forms.TextInput(
                attrs={
                    "placeholder": "Enter contract number",
                }
            ),
            "contract_clause": forms.Textarea(
                attrs={
                    "placeholder": "Enter contract clause",
                    "rows": 3,
                }
            ),
            "logo": forms.FileInput(
                attrs={
                    "accept": ".jpg,.jpeg,.png,.gif,.svg",
                }
            ),
            "category": forms.Select(),
            "vat": forms.CheckboxInput(),
            "payment_terms": forms.Select(),
        }
        labels = {
            "name": "Project Name",
            "logo": "Project Logo",
            "contract_number": "Payment Certificate Contract Number",
            "contract_clause": "Payment Certificate Contract Clause",
            "bank_account_name": "Account Name",
            "bank_account_number": "Account Number",
            "bank_branch_code": "Branch Code",
            "bank_swift_code": "SWIFT Code",
            "vat_number": "VAT/Tax Number",
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


class ProjectFilterForm(forms.Form):
    """Form for filtering projects."""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search projects...",
            }
        ),
    )
    project_category = forms.ModelChoiceField(
        queryset=ProjectCategory.objects.all(),
        required=False,
        label="Categories",
        empty_label="All Categories",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )
    project_subcategory = forms.ModelChoiceField(
        queryset=ProjectSubCategory.objects.all(),
        required=False,
        label="Subcategories",
        empty_label="All Subcategories",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )
    project_discipline = forms.ModelChoiceField(
        queryset=ProjectDiscipline.objects.all(),
        required=False,
        label="Disciplines",
        empty_label="All Disciplines",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )
    status = forms.ChoiceField(
        choices=[("ALL", "All Statuses")] + list(Project.Status.choices),
        required=False,
        initial="ALL",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )
    active_projects = forms.BooleanField(
        required=False,
        label="Active Projects",
    )
    projects = forms.ModelChoiceField(
        queryset=Project.objects.none(),
        required=False,
        label="Go to Project",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )
    consultant = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        required=False,
        empty_label="All Consultants",
        label="Consultants",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )
    client = forms.ModelChoiceField(
        queryset=Company.objects.none(),
        required=False,
        empty_label="All Clients",
        label="Clients",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )
    contractor = forms.ModelChoiceField(
        queryset=Company.objects.none(),
        required=False,
        empty_label="All Contractors",
        label="Contractors",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )

    def __init__(
        self,
        *args,
        user: Account | None = None,
        projects_queryset: QuerySet[Project] | None = None,
        consultant_queryset: QuerySet[Account] | None = None,
        client_queryset: QuerySet[Company] | None = None,
        contractor_queryset: QuerySet[Company] | None = None,
        category_queryset: QuerySet[ProjectCategory] | None = None,
        subcategory_queryset: QuerySet[ProjectSubCategory] | None = None,
        discipline_queryset: QuerySet[ProjectDiscipline] | None = None,
        **kwargs,
    ):
        """Initialize filter form with user-specific querysets."""
        super().__init__(*args, **kwargs)

        # Set custom querysets if provided
        if projects_queryset is not None:
            self.fields["projects"].queryset = projects_queryset  # type: ignore
        if consultant_queryset is not None:
            self.fields["consultant"].queryset = consultant_queryset  # type: ignore
        if client_queryset is not None:
            self.fields["client"].queryset = client_queryset  # type: ignore
        if contractor_queryset is not None:
            self.fields["contractor"].queryset = contractor_queryset  # type: ignore
        if category_queryset is not None:
            self.fields["project_category"].queryset = category_queryset  # type: ignore
        if subcategory_queryset is not None:
            self.fields["project_subcategory"].queryset = subcategory_queryset  # type: ignore
        if discipline_queryset is not None:
            self.fields["project_discipline"].queryset = discipline_queryset  # type: ignore
