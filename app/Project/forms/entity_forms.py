"""Forms for Project Entity Management."""

from django import forms
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from django.utils import timezone

from app.Project.models.entity_definitions import (
    LabourEntity,
    MaterialEntity,
    OverheadEntity,
    PlantEntity,
    SubcontractorEntity,
)
from app.core.Utilities.widgets import SearchableSelectWidget

COMMON_WIDGET_ATTRS = {
    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm transition duration-150 ease-in-out",
}


class BaseEntityForm(forms.ModelForm):
    """Base form for project entities with shared styling and hidden project field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply common styling to all fields
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                existing_class = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = (
                    f"{existing_class} {COMMON_WIDGET_ATTRS['class']}".strip()
                )


class LabourEntityForm(BaseEntityForm):
    class Meta:
        model = LabourEntity
        fields = [
            "person_name",
            "id_number",
            "trade",
            "skill_type",
            "date_joined",
            "expense_code",
            "unit_of_measure",
            "rate",
            "description",
        ]
        widgets = {
            "date_joined": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "skill_type": SearchableSelectWidget(create_url=True, resource_type="skill_type"),
            "unit_of_measure": SearchableSelectWidget(
                create_url=True, resource_type="unit_of_measure"
            ),
        }
        labels = {
            "person_name": "Full Name",
            "id_number": "ID / Passport Number",
            "date_joined": "Joining Date",
            "expense_code": "Expense Classification",
        }
        error_messages = {
            "person_name": {"required": "Please enter the worker's full name."},
            "rate": {"min_value": "Rate must be greater than zero."},
        }

    def clean_rate(self):
        rate = self.cleaned_data.get("rate")
        if rate is not None and rate <= 0:
            raise ValidationError("Rate must be a positive value greater than zero.")
        return rate

    def clean_date_joined(self):
        date_joined = self.cleaned_data.get("date_joined")
        if date_joined and date_joined > timezone.now().date():
            raise ValidationError("Joining date cannot be in the future.")
        return date_joined


class MaterialEntityForm(BaseEntityForm):
    class Meta:
        model = MaterialEntity
        fields = [
            "name",
            "supplier",
            "items_received",
            "invoice_number",
            "invoice_attachment",
            "quantity",
            "expense_code",
            "unit_of_measure",
            "rate",
            "date_received",
            "description",
        ]
        widgets = {
            "date_received": forms.DateInput(attrs={"type": "date"}),
            "items_received": forms.Textarea(attrs={"rows": 2}),
            "description": forms.Textarea(attrs={"rows": 2}),
            "unit_of_measure": SearchableSelectWidget(
                create_url=True, resource_type="unit_of_measure"
            ),
        }
        labels = {
            "items_received": "Items / Specifications",
            "date_received": "Receipt Date",
            "expense_code": "Expense Classification",
        }

    def clean_rate(self):
        rate = self.cleaned_data.get("rate")
        if rate is not None and rate <= 0:
            raise ValidationError("Rate must be a positive value.")
        return rate

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity")
        if qty is not None and qty <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        return qty

    def clean_date_received(self):
        date_received = self.cleaned_data.get("date_received")
        if date_received and date_received > timezone.now().date():
            raise ValidationError("Receipt date cannot be in the future.")
        return date_received


class MaterialHeaderForm(forms.ModelForm):
    """Form for shared material information."""

    class Meta:
        model = MaterialEntity
        fields = ["supplier", "invoice_number", "date_received", "invoice_attachment"]
        widgets = {
            "supplier": forms.TextInput(attrs=COMMON_WIDGET_ATTRS),
            "invoice_number": forms.TextInput(attrs=COMMON_WIDGET_ATTRS),
            "date_received": forms.DateInput(
                attrs={**COMMON_WIDGET_ATTRS, "type": "date"}
            ),
            "invoice_attachment": forms.FileInput(attrs=COMMON_WIDGET_ATTRS),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure header fields are required for bulk creation
        self.fields["supplier"].required = True
        self.fields["invoice_number"].required = True
        self.fields["date_received"].required = True

        # Apply common styling to all fields
        for field in self.fields.values():
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (
                f"{existing_class} {COMMON_WIDGET_ATTRS['class']}".strip()
            )

    def clean_date_received(self):
        date_received = self.cleaned_data.get("date_received")
        if date_received and date_received > timezone.now().date():
            raise ValidationError("Receipt date cannot be in the future.")
        return date_received


class MaterialItemForm(forms.ModelForm):
    """Form for individual material items in bulk create."""

    class Meta:
        model = MaterialEntity
        fields = ["name", "unit_of_measure", "quantity", "rate", "description"]
        labels = {
            "name": "Item Name",
            "unit_of_measure": "Unit",
            "quantity": "Quantity",
            "rate": "Rate (per unit)",
            "description": "Additional Description",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Item Name",
                    "class": "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "unit_of_measure": SearchableSelectWidget(
                create_url=True,
                resource_type="unit_of_measure",
                attrs={
                    "class": "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                },
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "placeholder": "Qty",
                    "step": "0.01",
                    "class": "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "rate": forms.NumberInput(
                attrs={
                    "placeholder": "Rate",
                    "step": "0.01",
                    "class": "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "placeholder": "Optional description",
                    "class": "block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
        }

    def clean_rate(self):
        rate = self.cleaned_data.get("rate")
        if rate is not None and rate <= 0:
            raise ValidationError("Rate must be positive.")
        return rate

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity")
        if qty is not None and qty <= 0:
            raise ValidationError("Qty must be greater than zero.")
        return qty

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


MaterialItemFormSet = modelformset_factory(
    MaterialEntity,
    form=MaterialItemForm,
    extra=0,
    can_delete=True,
)


class PlantEntityForm(BaseEntityForm):
    class Meta:
        model = PlantEntity
        fields = [
            "name",
            "plant_type",
            "specific_info",
            "supplier",
            "breakdown_status",
            "date",
            "expense_code",
            "unit_of_measure",
            "rate",
            "description",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "specific_info": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "plant_type": SearchableSelectWidget(create_url=True, resource_type="plant_type"),
            "breakdown_status": SearchableSelectWidget(),
            "unit_of_measure": SearchableSelectWidget(
                create_url=True, resource_type="unit_of_measure"
            ),
        }
        labels = {
            "specific_info": "Specific Info (S/N, etc.)",
            "breakdown_status": "Operational Status",
            "expense_code": "Expense Classification",
        }

    def clean_rate(self):
        rate = self.cleaned_data.get("rate")
        if rate is not None and rate <= 0:
            raise ValidationError("Usage rate must be greater than zero.")
        return rate

    def clean_date(self):
        date = self.cleaned_data.get("date")
        if date and date > timezone.now().date():
            raise ValidationError("Record date cannot be in the future.")
        return date


class SubcontractorEntityForm(BaseEntityForm):
    class Meta:
        model = SubcontractorEntity
        fields = [
            "name",
            "trade",
            "scope",
            "start_date",
            "planned_finish_date",
            "actual_finish_date",
            "expense_code",
            "unit_of_measure",
            "rate",
            "description",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "planned_finish_date": forms.DateInput(attrs={"type": "date"}),
            "actual_finish_date": forms.DateInput(attrs={"type": "date"}),
            "scope": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "unit_of_measure": SearchableSelectWidget(
                create_url=True, resource_type="unit_of_measure"
            ),
        }
        labels = {
            "scope": "Scope of Work",
            "start_date": "Contract Start Date",
            "planned_finish_date": "Planned Finish",
            "actual_finish_date": "Actual Finish",
            "expense_code": "Expense Classification",
        }

    def clean_rate(self):
        rate = self.cleaned_data.get("rate")
        if rate is not None and rate <= 0:
            raise ValidationError("Contract rate must be greater than zero.")
        return rate

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data is None:
            return cleaned_data
        start_date = cleaned_data.get("start_date")
        planned_finish = cleaned_data.get("planned_finish_date")
        actual_finish = cleaned_data.get("actual_finish_date")

        if start_date:
            if planned_finish and planned_finish < start_date:
                self.add_error(
                    "planned_finish_date", "Planned finish cannot be before start date."
                )
            if actual_finish and actual_finish < start_date:
                self.add_error(
                    "actual_finish_date", "Actual finish cannot be before start date."
                )

        return cleaned_data


class OverheadEntityForm(BaseEntityForm):
    class Meta:
        model = OverheadEntity
        fields = [
            "name",
            "category",
            "expense_code",
            "unit_of_measure",
            "rate",
            "description",
        ]
        labels = {
            "expense_code": "Expense Classification",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "unit_of_measure": SearchableSelectWidget(
                create_url=True, resource_type="unit_of_measure"
            ),
        }

    def clean_rate(self):
        rate = self.cleaned_data.get("rate")
        if rate is not None and rate <= 0:
            raise ValidationError("Overhead rate must be a positive value.")
        return rate
