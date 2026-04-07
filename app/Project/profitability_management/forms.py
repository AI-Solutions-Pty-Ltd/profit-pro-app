from django import forms
from .models.profitability_models import LabourCostLog, OverheadCostLog, SubcontractorCostLog

COMMON_WIDGET_ATTRS = {
    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm transition-all duration-200",
}

class SubcontractorCostLogForm(forms.ModelForm):
    class Meta:
        model = SubcontractorCostLog
        fields = ["subcontractor_name", "reference_no", "days", "rate"]
        widgets = {
            "subcontractor_name": forms.TextInput(attrs={**COMMON_WIDGET_ATTRS, "placeholder": "Subcontractor Name"}),
            "reference_no": forms.TextInput(attrs={**COMMON_WIDGET_ATTRS, "placeholder": "Reference NO"}),
            "days": forms.NumberInput(attrs={**COMMON_WIDGET_ATTRS, "step": "0.01"}),
            "rate": forms.NumberInput(attrs={**COMMON_WIDGET_ATTRS, "step": "0.01"}),
        }

class LabourCostLogForm(forms.ModelForm):
    class Meta:
        model = LabourCostLog
        fields = ["worker_name", "worker_id", "days", "salary_rate"]
        widgets = {
            "worker_name": forms.TextInput(attrs={**COMMON_WIDGET_ATTRS, "placeholder": "Labour/Worker Name"}),
            "worker_id": forms.TextInput(attrs={**COMMON_WIDGET_ATTRS, "placeholder": "ID Reference"}),
            "days": forms.NumberInput(attrs={**COMMON_WIDGET_ATTRS, "step": "0.01"}),
            "salary_rate": forms.NumberInput(attrs={**COMMON_WIDGET_ATTRS, "step": "0.01"}),
        }

class OverheadCostLogForm(forms.ModelForm):
    class Meta:
        model = OverheadCostLog
        fields = ["description", "days", "rate"]
        widgets = {
            "description": forms.TextInput(attrs={**COMMON_WIDGET_ATTRS, "placeholder": "Overheads (e.g., Site Office)"}),
            "days": forms.NumberInput(attrs={**COMMON_WIDGET_ATTRS, "step": "0.01"}),
            "rate": forms.NumberInput(attrs={**COMMON_WIDGET_ATTRS, "step": "0.01"}),
        }
