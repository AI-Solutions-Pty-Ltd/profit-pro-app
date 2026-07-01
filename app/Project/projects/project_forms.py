"""Forms for Project app."""

from typing import Any, cast

from django import forms
from django.db.models import QuerySet

from app.Account.models import Account, Municipality, Province
from app.Project.models import (
    Company,
    Project,
    ProjectCategory,
    ProjectDiscipline,
    ProjectStage,
)


class BasicProjectCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        area_field = cast(forms.ModelChoiceField, self.fields["area"])
        cast(Any, area_field).label_from_instance = lambda obj: (
            f"{obj.province} - {obj.municipality_name}"
        )

    class Meta:
        model = Project
        fields = [
            "name",
            "project_category",
            "area",
            "project_stage",
            # "project_discipline",
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        area_field = cast(forms.ModelChoiceField, self.fields["area"])
        cast(Any, area_field).label_from_instance = lambda obj: (
            f"{obj.province} - {obj.municipality_name}"
        )

    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "logo",
            "project_category",
            "area",
            "project_stage",
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
            "project_category": "Sector",
            "area": "Municipality",
            "project_stage": "Project Stage",
            "project_discipline": "Discipline",
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
            "project_category": "Select the project sector",
            "area": "Select the project area (Municipality)",
            "project_stage": "Select the project stage",
            "project_discipline": "Select the project discipline",
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
        label="Sectors",
        empty_label="All Sectors",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        required=False,
        label="Provinces",
        empty_label="All Provinces",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )
    area = forms.ModelChoiceField(
        queryset=Municipality.objects.all(),
        required=False,
        label="Municipalities",
        empty_label="All Municipalities",
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
    project_stage = forms.ModelChoiceField(
        queryset=ProjectStage.objects.all(),
        required=False,
        label="Project Stages",
        empty_label="All Project Stages",
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
        province_queryset: QuerySet[Province] | None = None,
        area_queryset: QuerySet[Municipality] | None = None,
        discipline_queryset: QuerySet[ProjectDiscipline] | None = None,
        stage_queryset: QuerySet[ProjectStage] | None = None,
        **kwargs,
    ):
        """Initialize filter form with user-specific querysets."""
        if user and getattr(user, "has_demo_permission", False):
            Company.ensure_demo_companies(user=user)

        # Filter area queryset by selected province if specified in args[0]
        form_data = args[0] if args else {}
        selected_province_id = form_data.get("province") if form_data else None
        if selected_province_id:
            if area_queryset is not None:
                area_queryset = area_queryset.filter(province_id=selected_province_id)
            else:
                area_queryset = Municipality.objects.filter(
                    province_id=selected_province_id
                )

        super().__init__(*args, **kwargs)

        # Set custom querysets if provided
        if province_queryset is not None:
            self.fields["province"].queryset = province_queryset  # type: ignore
        else:
            self.fields["province"].queryset = Province.objects.all().order_by("name")  # type: ignore

        if projects_queryset is not None:
            self.fields["projects"].queryset = projects_queryset  # type: ignore
        if consultant_queryset is not None:
            self.fields["consultant"].queryset = consultant_queryset  # type: ignore
        if client_queryset is not None:
            if user and not user.is_superuser:
                client_queryset = client_queryset.filter(created_by=user)
            if user and getattr(user, "has_demo_permission", False):
                demo_clients = Company.objects.filter(
                    type=Company.Type.CLIENT,
                    registration_number__in=[f"DEMO-CLIENT-{user.pk}"],
                )
                if client_queryset.query.distinct:
                    demo_clients = demo_clients.distinct()
                client_queryset = (
                    (client_queryset | demo_clients).distinct().order_by("name")
                )
            self.fields["client"].queryset = client_queryset  # type: ignore
        if contractor_queryset is not None:
            if user and getattr(user, "has_demo_permission", False):
                demo_contractors = Company.objects.filter(
                    type=Company.Type.CONTRACTOR,
                    registration_number__in=[
                        "DEMO-CONTRACTOR-1",
                        f"DEMO-CONTRACTOR-1-{user.pk}",
                    ],
                )
                if contractor_queryset.query.distinct:
                    demo_contractors = demo_contractors.distinct()
                contractor_queryset = (
                    (contractor_queryset | demo_contractors).distinct().order_by("name")
                )
            self.fields["contractor"].queryset = contractor_queryset  # type: ignore
        if category_queryset is not None:
            self.fields["project_category"].queryset = category_queryset  # type: ignore
        if area_queryset is not None:
            self.fields["area"].queryset = area_queryset  # type: ignore
        if discipline_queryset is not None:
            self.fields["project_discipline"].queryset = discipline_queryset  # type: ignore
        if stage_queryset is not None:
            self.fields["project_stage"].queryset = stage_queryset  # type: ignore

        area_field = cast(forms.ModelChoiceField, self.fields["area"])
        cast(Any, area_field).label_from_instance = lambda obj: obj.municipality_name
