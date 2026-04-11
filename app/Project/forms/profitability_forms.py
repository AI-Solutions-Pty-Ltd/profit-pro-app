from crispy_forms.helper import FormHelper
from django import forms

from app.core.Utilities.widgets import SearchableSelectWidget
from app.Project.models import (
    JournalEntry,
    LabourCostTracker,
    MaterialCostTracker,
    OverheadCostTracker,
    PlantCostTracker,
    SubcontractorCostTracker,
)


class ProfitabilityBaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"


class JournalEntryForm(ProfitabilityBaseForm):
    class Meta:
        model = JournalEntry
        fields = ["date", "category", "description", "amount", "transaction_type"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }


class LabourCostTrackerForm(ProfitabilityBaseForm):
    class Meta:
        model = LabourCostTracker
        fields = [
            "labour_entity",
            "date",
            "id_number",
            "amount_of_days",
            "salary",
            "task_activity",
            "remarks",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "salary": forms.TextInput(attrs={"readonly": "readonly"}),
            "id_number": forms.TextInput(attrs={"readonly": "readonly"}),
            "labour_entity": SearchableSelectWidget(
                create_url=True, resource_type="labour_entity"
            ),
        }
        labels = {
            "amount_of_days": "Quantity (Days)",
            "salary": "Daily Rate",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.project:
            entities = self.project.labourentity_entities.all()
            self.fields["labour_entity"].queryset = entities
            # Build choice data for autofill (rate and id_number)
            self.fields["labour_entity"].widget.choice_data = {
                str(e.id): {"data-rate": str(e.rate), "data-id_number": e.id_number}
                for e in entities
            }


class SubcontractorCostTrackerForm(ProfitabilityBaseForm):
    class Meta:
        model = SubcontractorCostTracker
        fields = [
            "subcontractor_entity",
            "date",
            "reference_no",
            "amount_of_days",
            "rate",
            "task",
            "hours_worked",
            "remarks",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "rate": forms.TextInput(attrs={"readonly": "readonly"}),
            "reference_no": forms.TextInput(attrs={"readonly": "readonly"}),
            "subcontractor_entity": SearchableSelectWidget(
                create_url=True, resource_type="subcontractor_entity"
            ),
        }
        labels = {
            "amount_of_days": "Quantity (Days)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.project:
            entities = self.project.subcontractorentity_entities.all()
            self.fields["subcontractor_entity"].queryset = entities
            # Build choice data for autofill (rate and reference_no)
            self.fields["subcontractor_entity"].widget.choice_data = {
                str(e.id): {
                    "data-rate": str(e.rate),
                    "data-reference_no": e.reference_no,
                }
                for e in entities
            }


class OverheadCostTrackerForm(ProfitabilityBaseForm):
    class Meta:
        model = OverheadCostTracker
        fields = ["overhead_entity", "date", "amount_of_days", "rate", "remarks"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "rate": forms.TextInput(attrs={"readonly": "readonly"}),
            "overhead_entity": SearchableSelectWidget(
                create_url=True, resource_type="overhead_entity"
            ),
        }
        labels = {
            "amount_of_days": "Quantity (Days)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.project:
            entities = self.project.overheadentity_entities.all()
            self.fields["overhead_entity"].queryset = entities
            # Build choice data for autofill
            self.fields["overhead_entity"].widget.choice_data = {
                str(e.id): {"data-rate": str(e.rate)} for e in entities
            }


class MaterialCostTrackerForm(ProfitabilityBaseForm):
    class Meta:
        model = MaterialCostTracker
        fields = [
            "material_entity",
            "date",
            "quantity",
            "rate",
            "intended_usage",
            "comments",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "rate": forms.TextInput(attrs={"readonly": "readonly"}),
            "material_entity": SearchableSelectWidget(
                create_url=True, resource_type="material_entity"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.project:
            entities = self.project.materialentity_entities.all()
            self.fields["material_entity"].queryset = entities
            # Build choice data for autofill
            self.fields["material_entity"].widget.choice_data = {
                str(e.id): {"data-rate": str(e.rate)} for e in entities
            }




class PlantCostTrackerForm(ProfitabilityBaseForm):
    class Meta:
        model = PlantCostTracker
        fields = [
            "plant_entity",
            "date",
            "usage_hours",
            "hourly_rate",
            "breakdown_status",
            "maintenance_done",
            "remarks",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "hourly_rate": forms.TextInput(attrs={"readonly": "readonly"}),
            "plant_entity": SearchableSelectWidget(
                create_url=True, resource_type="plant_entity"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.project:
            entities = self.project.plantentity_entities.all()
            self.fields["plant_entity"].queryset = entities
            # Build choice data for autofill
            self.fields["plant_entity"].widget.choice_data = {
                str(e.id): {"data-rate": str(e.rate)} for e in entities
            }

