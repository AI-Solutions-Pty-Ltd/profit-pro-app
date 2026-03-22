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
    WorkPackage,
)


class WorkPackageForm(forms.ModelForm):
    """Form for creating and editing work packages."""

    class Meta:
        model = WorkPackage
        fields = [
            "name",
            "description",
            "advert_start_date",
            "advert_end_date",
            "site_inspection_percentage",
            "site_inspection_complete",
            "tender_close_percentage",
            "tender_close_complete",
            "tender_evaluation_percentage",
            "tender_evaluation_complete",
            "award_signing_percentage",
            "award_signing_complete",
            "mobilization_percentage",
            "mobilization_complete",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "advert_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "advert_end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "site_inspection_percentage": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "max": 100, "step": 0.01}
            ),
            "tender_close_percentage": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "max": 100, "step": 0.01}
            ),
            "tender_evaluation_percentage": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "max": 100, "step": 0.01}
            ),
            "award_signing_percentage": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "max": 100, "step": 0.01}
            ),
            "mobilization_percentage": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "max": 100, "step": 0.01}
            ),
        }


class TenderDocumentForm(forms.ModelForm):
    """Form for editing tender documents."""

    class Meta:
        model = TenderDocument
        fields = ["name", "file", "percentage_completed", "planned_date", "actual_date"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "percentage_completed": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "max": 100, "step": 0.01}
            ),
            "planned_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "actual_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
        }


class DesignCategoryForm(forms.ModelForm):
    """Form for creating/editing design categories (L1)."""

    class Meta:
        model = DesignCategory
        fields = ["category", "stage"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "stage": forms.Select(attrs={"class": "form-select"}),
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
        fields = ["sub_category", "stage"]
        widgets = {
            "sub_category": forms.Select(attrs={"class": "form-select"}),
            "stage": forms.Select(attrs={"class": "form-select"}),
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
        fields = ["group", "stage"]
        widgets = {
            "group": forms.Select(attrs={"class": "form-select"}),
            "stage": forms.Select(attrs={"class": "form-select"}),
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
        fields = ["discipline", "stage"]
        widgets = {
            "discipline": forms.Select(attrs={"class": "form-select"}),
            "stage": forms.Select(attrs={"class": "form-select"}),
        }


class DesignDisciplineFileForm(forms.ModelForm):
    """Form for uploading files to a design discipline."""

    class Meta:
        model = DesignDisciplineFile
        fields = ["file", "description"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-input"}),
        }
