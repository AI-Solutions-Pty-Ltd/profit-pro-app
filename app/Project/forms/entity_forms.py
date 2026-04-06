"""Forms for Project Entity Management."""

from django import forms

from app.Project.models.entity_definitions import (
    LabourEntity,
    MaterialEntity,
    OverheadEntity,
    PlantEntity,
    SubcontractorEntity,
)

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
            "unit",
            "rate",
            "description",
        ]
        widgets = {
            "date_joined": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "person_name": "Full Name",
            "id_number": "ID / Passport Number",
            "date_joined": "Joining Date",
        }


class MaterialEntityForm(BaseEntityForm):
    class Meta:
        model = MaterialEntity
        fields = [
            "name",
            "supplier",
            "items_received",
            "invoice_number",
            "quantity",
            "unit",
            "rate",
            "date_received",
            "description",
        ]
        widgets = {
            "date_received": forms.DateInput(attrs={"type": "date"}),
            "items_received": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "items_received": "Items / Specifications",
            "date_received": "Receipt Date",
        }


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
            "unit",
            "rate",
            "description",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "specific_info": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "specific_info": "Specific Info (S/N, etc.)",
            "breakdown_status": "Operational Status",
        }


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
            "unit",
            "rate",
            "description",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "planned_finish_date": forms.DateInput(attrs={"type": "date"}),
            "actual_finish_date": forms.DateInput(attrs={"type": "date"}),
            "scope": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "scope": "Scope of Work",
            "start_date": "Contract Start Date",
            "planned_finish_date": "Planned Finish",
            "actual_finish_date": "Actual Finish",
        }


class OverheadEntityForm(BaseEntityForm):
    class Meta:
        model = OverheadEntity
        fields = [
            "name",
            "category",
            "unit",
            "rate",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
