"""Forms for Planning & Procurement app."""

from django import forms

from app.Planning.models import (
    DesignCategory,
    DesignCategoryFile,
    DesignDiscipline,
    DesignDisciplineFile,
    DesignGroup,
    DesignGroupFile,
    DesignSubCategory,
    DesignSubCategoryFile,
    TenderDocument,
    TenderDocumentFile,
    WorkPackage,
)


class WorkPackageForm(forms.ModelForm):
    """Form for creating and editing work packages."""

    class Meta:
        model = WorkPackage
        fields = [
            "package_number",
            "name",
            "description",
            "applied_to_advert_start_date",
            "applied_to_advert_end_date",
            "applied_to_advert_completed",
            "site_inspection_start_date",
            "site_inspection_end_date",
            "site_inspection_completed",
            "tender_close_start_date",
            "tender_close_end_date",
            "tender_close_completed",
            "tender_evaluation_start_date",
            "tender_evaluation_end_date",
            "tender_evaluation_completed",
            "award_start_date",
            "award_end_date",
            "award_completed",
            "contract_signing_start_date",
            "contract_signing_end_date",
            "contract_signing_completed",
            "mobilization_start_date",
            "mobilization_end_date",
            "mobilization_completed",
            "package_budget",
            "budget_structure_file",
        ]
        widgets = {
            "package_number": forms.TextInput(attrs={"class": "form-input"}),
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "applied_to_advert_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "applied_to_advert_end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "applied_to_advert_completed": forms.CheckboxInput(
                attrs={"class": "form-checkbox"}
            ),
            "site_inspection_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "site_inspection_end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "site_inspection_completed": forms.CheckboxInput(
                attrs={"class": "form-checkbox"}
            ),
            "tender_close_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "tender_close_end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "tender_close_completed": forms.CheckboxInput(
                attrs={"class": "form-checkbox"}
            ),
            "tender_evaluation_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "tender_evaluation_end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "tender_evaluation_completed": forms.CheckboxInput(
                attrs={"class": "form-checkbox"}
            ),
            "award_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "award_end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "award_completed": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
            "contract_signing_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "contract_signing_end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "contract_signing_completed": forms.CheckboxInput(
                attrs={"class": "form-checkbox"}
            ),
            "mobilization_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "mobilization_end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "mobilization_completed": forms.CheckboxInput(
                attrs={"class": "form-checkbox"}
            ),
            "package_budget": forms.NumberInput(
                attrs={"class": "form-input", "step": 0.01}
            ),
            "budget_structure_file": forms.FileInput(attrs={"class": "form-input"}),
        }


class TenderDocumentForm(forms.ModelForm):
    """Form for editing tender documents."""

    class Meta:
        model = TenderDocument
        fields = [
            "name",
            "planned_date",
            "actual_date",
            "required_quantity",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "required_quantity": forms.NumberInput(
                attrs={"class": "form-input", "min": 1, "step": 1}
            ),
            "planned_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "actual_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
        }


class TenderDocumentFileForm(forms.ModelForm):
    """Form for uploading files to a tender document."""

    class Meta:
        model = TenderDocumentFile
        fields = ["file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].widget.attrs.update({"class": "form-input"})


class DesignCategoryForm(forms.ModelForm):
    """Form for creating/editing design categories (L1)."""

    class Meta:
        model = DesignCategory
        fields = ["category", "stage", "required_quantity"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "stage": forms.Select(attrs={"class": "form-select"}),
            "required_quantity": forms.NumberInput(
                attrs={"class": "form-input", "min": 1}
            ),
        }


class DesignCategoryFileForm(forms.ModelForm):
    """Form for uploading files to a design category."""

    class Meta:
        model = DesignCategoryFile
        fields = ["file", "description"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-input"}),
        }


class DesignSubCategoryForm(forms.ModelForm):
    """Form for creating/editing design subcategories (L2)."""

    class Meta:
        model = DesignSubCategory
        fields = ["sub_category", "stage", "required_quantity"]
        widgets = {
            "sub_category": forms.Select(attrs={"class": "form-select"}),
            "stage": forms.Select(attrs={"class": "form-select"}),
            "required_quantity": forms.NumberInput(
                attrs={"class": "form-input", "min": 1}
            ),
        }


class DesignSubCategoryFileForm(forms.ModelForm):
    """Form for uploading files to a design subcategory."""

    class Meta:
        model = DesignSubCategoryFile
        fields = ["file", "description"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-input"}),
        }


class DesignGroupForm(forms.ModelForm):
    """Form for creating/editing design groups (L3)."""

    class Meta:
        model = DesignGroup
        fields = ["group", "stage", "required_quantity"]
        widgets = {
            "group": forms.Select(attrs={"class": "form-select"}),
            "stage": forms.Select(attrs={"class": "form-select"}),
            "required_quantity": forms.NumberInput(
                attrs={"class": "form-input", "min": 1}
            ),
        }


class DesignGroupFileForm(forms.ModelForm):
    """Form for uploading files to a design group."""

    class Meta:
        model = DesignGroupFile
        fields = ["file", "description"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-input"}),
        }


class DesignDisciplineForm(forms.ModelForm):
    """Form for creating/editing design disciplines (L4)."""

    class Meta:
        model = DesignDiscipline
        fields = ["discipline", "stage", "required_quantity"]
        widgets = {
            "discipline": forms.Select(attrs={"class": "form-select"}),
            "stage": forms.Select(attrs={"class": "form-select"}),
            "required_quantity": forms.NumberInput(
                attrs={"class": "form-input", "min": 1}
            ),
        }


class DesignDisciplineFileForm(forms.ModelForm):
    """Form for uploading files to a design discipline."""

    class Meta:
        model = DesignDisciplineFile
        fields = ["file", "description"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-input"}),
        }
