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

_DATE_INPUT = {"type": "date", "class": "form-input"}
_TEXT_INPUT = {"class": "form-input"}
_CHECKBOX = {"class": "form-checkbox"}


class WorkPackageForm(forms.ModelForm):
    """Form for creating and editing procurement packages (tracking dates, contract details, budget)."""

    class Meta:
        model = WorkPackage
        fields = [
            "package_number",
            "name",
            "description",
            "contract_type",
            "procurement_strategy",
            "conditions_of_contract",
            "overall_start_date",
            "overall_end_date",
            "documentation_start_date",
            "documentation_end_date",
            "tender_process_start_date",
            "tender_process_end_date",
            "execution_start_date",
            "execution_end_date",
            "package_budget",
            "budget_structure_file",
        ]
        widgets = {
            "package_number": forms.TextInput(attrs=_TEXT_INPUT),
            "name": forms.TextInput(attrs=_TEXT_INPUT),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "contract_type": forms.Select(attrs={"class": "form-select"}),
            "procurement_strategy": forms.Select(attrs={"class": "form-select"}),
            "conditions_of_contract": forms.Select(attrs={"class": "form-select"}),
            "overall_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "overall_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "documentation_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "documentation_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "tender_process_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "tender_process_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "execution_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "execution_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "package_budget": forms.NumberInput(
                attrs={"class": "form-input", "step": 0.01}
            ),
            "budget_structure_file": forms.FileInput(attrs=_TEXT_INPUT),
        }


class WorkPackageProcessForm(forms.ModelForm):
    """Form for editing work package process tracking dates and budget."""

    class Meta:
        model = WorkPackage
        fields = [
            "package_number",
            "name",
            "description",
            "contract_type",
            "procurement_strategy",
            "conditions_of_contract",
            "overall_start_date",
            "overall_end_date",
            "documentation_start_date",
            "documentation_end_date",
            "tender_process_start_date",
            "tender_process_end_date",
            "execution_start_date",
            "execution_end_date",
            "package_budget",
            "budget_structure_file",
        ]
        widgets = {
            "package_number": forms.TextInput(attrs=_TEXT_INPUT),
            "name": forms.TextInput(attrs=_TEXT_INPUT),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "contract_type": forms.Select(attrs={"class": "form-select"}),
            "procurement_strategy": forms.Select(attrs={"class": "form-select"}),
            "conditions_of_contract": forms.Select(attrs={"class": "form-select"}),
            "overall_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "overall_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "documentation_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "documentation_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "tender_process_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "tender_process_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "execution_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "execution_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "package_budget": forms.NumberInput(
                attrs={"class": "form-input", "step": 0.01}
            ),
            "budget_structure_file": forms.FileInput(attrs=_TEXT_INPUT),
        }


class TenderProcessForm(forms.ModelForm):
    """Form for editing tender process milestone dates and completion flags."""

    class Meta:
        model = WorkPackage
        fields = [
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
        ]
        widgets = {
            "applied_to_advert_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "applied_to_advert_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "applied_to_advert_completed": forms.CheckboxInput(attrs=_CHECKBOX),
            "site_inspection_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "site_inspection_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "site_inspection_completed": forms.CheckboxInput(attrs=_CHECKBOX),
            "tender_close_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "tender_close_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "tender_close_completed": forms.CheckboxInput(attrs=_CHECKBOX),
            "tender_evaluation_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "tender_evaluation_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "tender_evaluation_completed": forms.CheckboxInput(attrs=_CHECKBOX),
            "award_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "award_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "award_completed": forms.CheckboxInput(attrs=_CHECKBOX),
            "contract_signing_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "contract_signing_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "contract_signing_completed": forms.CheckboxInput(attrs=_CHECKBOX),
            "mobilization_start_date": forms.DateInput(attrs=_DATE_INPUT),
            "mobilization_end_date": forms.DateInput(attrs=_DATE_INPUT),
            "mobilization_completed": forms.CheckboxInput(attrs=_CHECKBOX),
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
