from crispy_forms.helper import FormHelper
from django import forms
from django.forms import ModelChoiceField

from app.core.Utilities.widgets import SearchableSelectWidget
from app.Project.models import (
    JournalEntry,
    LabourCostTracker,
    MaterialCostTracker,
    OverheadCostTracker,
    PlantCostTracker,
    ProfitabilityBaseline,
    SubcontractorCostTracker,
)


class ProfitabilityBaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
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
            field = self.fields["labour_entity"]
            assert isinstance(field, ModelChoiceField)
            field.queryset = entities
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
            field = self.fields["subcontractor_entity"]
            assert isinstance(field, ModelChoiceField)
            field.queryset = entities
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
            field = self.fields["overhead_entity"]
            assert isinstance(field, ModelChoiceField)
            field.queryset = entities
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
            field = self.fields["material_entity"]
            assert isinstance(field, ModelChoiceField)
            field.queryset = entities
            # Build choice data for autofill
            self.fields["material_entity"].widget.choice_data = {
                str(e.id): {"data-rate": str(e.rate)} for e in entities
            }


class MaterialCostTrackerBulkHeaderForm(forms.Form):
    """Header form for shared material tracking data (invoice/receipt)."""

    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        help_text="Date of receipt",
    )
    invoice_number = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Invoice #", "class": "form-control"}
        ),
    )
    supplier = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Supplier Name", "class": "form-control"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class MaterialCostTrackerBulkItemForm(forms.ModelForm):
    """Line item form for material cost entries."""

    class Meta:
        model = MaterialCostTracker
        fields = [
            "material_entity",
            "quantity",
            "rate",
            "intended_usage",
            "comments",
        ]
        widgets = {
            "material_entity": SearchableSelectWidget(
                create_url=True,
                resource_type="material_entity",
                attrs={"class": "form-control select2-input"},
            ),
            "quantity": forms.NumberInput(
                attrs={"placeholder": "Qty", "step": "0.01", "class": "form-control"}
            ),
            "rate": forms.NumberInput(
                attrs={"placeholder": "Rate", "step": "0.01", "class": "form-control"}
            ),
            "intended_usage": forms.TextInput(
                attrs={"placeholder": "Usage", "class": "form-control"}
            ),
            "comments": forms.TextInput(
                attrs={"placeholder": "Comments", "class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        if self.project:
            self.fields[
                "material_entity"
            ].queryset = self.project.materialentity_entities.all()
            # Add rate data for auto-fill in JS
            entities = self.project.materialentity_entities.all()
            self.fields["material_entity"].widget.choice_data = {
                str(e.id): {"data-rate": str(e.rate)} for e in entities
            }

        # Apply basic styling
        for _name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "")
            if "form-control" not in field.widget.attrs["class"]:
                field.widget.attrs["class"] += " form-control"


MaterialCostTrackerItemFormSet = forms.modelformset_factory(
    MaterialCostTracker,
    form=MaterialCostTrackerBulkItemForm,
    extra=0,
    can_delete=True,
)


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
            field = self.fields["plant_entity"]
            assert isinstance(field, ModelChoiceField)
            field.queryset = entities
            # Build choice data for autofill
            self.fields["plant_entity"].widget.choice_data = {
                str(e.id): {"data-rate": str(e.rate)} for e in entities
            }


class ProfitabilityBaselineForm(ProfitabilityBaseForm):
    class Meta:
        model = ProfitabilityBaseline
        fields = [
            "cost_of_sales_percent",
            "operating_expenses_percent",
            "net_profit_percent",
        ]
        labels = {
            "cost_of_sales_percent": "Cost of Sales (%)",
            "operating_expenses_percent": "Operating Expenses (%)",
            "net_profit_percent": "Net Profit (%)",
        }

    def clean(self):
        cleaned_data = super().clean()
        cos = cleaned_data.get("cost_of_sales_percent") or 0
        opex = cleaned_data.get("operating_expenses_percent") or 0
        profit = cleaned_data.get("net_profit_percent") or 0

        total = cos + opex + profit
        if total != 100:
            raise forms.ValidationError(
                f"Percentages must sum to 100%. Current total: {total}%"
            )
        return cleaned_data
