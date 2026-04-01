from django import forms

from .models.profitability_models import LabourCostLog, OverheadCostLog, SubcontractorCostLog

COMMON_WIDGET_ATTRS = {
    "class": "mt-1 block w-full rounded-xl border-gray-200 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-3 transition-shadow duration-200 bg-gray-50/50 hover:bg-white",
}

class SubcontractorCostLogForm(forms.ModelForm):
    class Meta:
        model = SubcontractorCostLog
        fields = ["subcontractor_name", "reference_no", "days", "rate"]
        widgets = {
            "subcontractor_name": forms.TextInput(attrs={**COMMON_WIDGET_ATTRS, "placeholder": "Subcontractor Name"}),
            "reference_no": forms.TextInput(attrs={**COMMON_WIDGET_ATTRS, "placeholder": "Reference NO (e.g. INV-001)"}),
            "days": forms.NumberInput(attrs={**COMMON_WIDGET_ATTRS, "step": "0.01", "placeholder": "0.00"}),
            "rate": forms.NumberInput(attrs={**COMMON_WIDGET_ATTRS, "step": "0.01", "placeholder": "0.00"}),
        }

class LabourCostLogForm(forms.ModelForm):
    class Meta:
        model = LabourCostLog
        fields = ["worker_name", "worker_id", "days", "salary_rate"]
        widgets = {
            "worker_name": forms.TextInput(attrs={**COMMON_WIDGET_ATTRS, "placeholder": "Labour/Worker Name"}),
            "worker_id": forms.TextInput(attrs={**COMMON_WIDGET_ATTRS, "placeholder": "ID Reference (EDP #)"}),
            "days": forms.NumberInput(attrs={**COMMON_WIDGET_ATTRS, "step": "0.01", "placeholder": "0.00"}),
            "salary_rate": forms.NumberInput(attrs={**COMMON_WIDGET_ATTRS, "step": "0.01", "placeholder": "0.00"}),
        }

class OverheadCostLogForm(forms.ModelForm):
    class Meta:
        model = OverheadCostLog
        fields = ["description", "days", "rate"]
        widgets = {
            "description": forms.TextInput(attrs={**COMMON_WIDGET_ATTRS, "placeholder": "e.g. Site Office Rent"}),
            "days": forms.NumberInput(attrs={**COMMON_WIDGET_ATTRS, "step": "0.01", "placeholder": "0.00"}),
            "rate": forms.NumberInput(attrs={**COMMON_WIDGET_ATTRS, "step": "0.01", "placeholder": "0.00"}),
        }
