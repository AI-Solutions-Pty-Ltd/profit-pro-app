from django import forms
from .models.profitability_models import LabourCostLog, OverheadCostLog, SubcontractorCostLog

class SubcontractorCostLogForm(forms.ModelForm):
    class Meta:
        model = SubcontractorCostLog
        fields = ["subcontractor_name", "reference_no", "days", "rate"]
        widgets = {
            "subcontractor_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Subcontractor Name"}),
            "reference_no": forms.TextInput(attrs={"class": "form-control", "placeholder": "Reference NO"}),
            "days": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

class LabourCostLogForm(forms.ModelForm):
    class Meta:
        model = LabourCostLog
        fields = ["worker_name", "worker_id", "days", "salary_rate"]
        widgets = {
            "worker_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Labour/Worker Name"}),
            "worker_id": forms.TextInput(attrs={"class": "form-control", "placeholder": "ID Reference"}),
            "days": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "salary_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

class OverheadCostLogForm(forms.ModelForm):
    class Meta:
        model = OverheadCostLog
        fields = ["description", "days", "rate"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Overheads (e.g., Site Office)"}),
            "days": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
