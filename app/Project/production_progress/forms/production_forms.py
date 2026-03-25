from django import forms
from ..models.production_models import DailyProduction, ProductionPlan


class DailyProductionForm(forms.ModelForm):
    """Form for logging daily notes."""
    
    class Meta:
        model = DailyProduction
        fields = [
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"class": "form-textarea", "rows": 5, "placeholder": "Enter notes here..."}),
        }


class ProductionPlanForm(forms.ModelForm):
    """Form for production planning items."""

    class Meta:
        model = ProductionPlan
        fields = ["activity", "start_date", "finish_date", "quantity", "unit"]

