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
            "package_number",
            "name",
            "description",
            "package_start_date",
            "package_finish_date",
            "design_start_date",
            "design_finish_date",
            "documentation_start_date",
            "documentation_finish_date",
            "tender_start_date",
            "tender_finish_date",
            "execution_start_date",
            "execution_finish_date",
            "package_budget",
            "budget_structure_file",
        ]
        widgets = {
            "package_number": forms.TextInput(attrs={"class": "form-input"}),
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "package_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "package_finish_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "design_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "design_finish_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "documentation_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "documentation_finish_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "tender_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "tender_finish_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "execution_start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "execution_finish_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
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
