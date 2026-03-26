from django import forms
from ..models.production_models import DailyProduction, ProductionPlan, ProductionResource


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
        fields = ["activity", "start_date", "finish_date", "duration", "quantity", "unit"]
        widgets = {
            "activity": forms.TextInput(attrs={
                "id": "activity",
                "placeholder": "Enter Activity (e.g., Bricks)"
                
            }),
            "start_date": forms.DateInput(attrs={
                "id": "start_date",
                "type": "date",
                "onchange": "calculateDuration()",
                "style": "color-scheme: light;"
            }),
            "finish_date": forms.DateInput(attrs={
                "id": "finish_date",
                "type": "date",
                "onchange": "calculateDuration()",
                "style": "color-scheme: light;"
            }),
            "duration": forms.NumberInput(attrs={
                "id": "duration",
                "readonly": "readonly",
                "tabindex": "-1"
            }),
            "quantity": forms.NumberInput(attrs={
                "id": "quantity",
                "step": "1",
                "placeholder": "10000"
            }),
            "unit": forms.TextInput(attrs={
                "id": "unit",
                "placeholder": "Unit e.g. bricks"
            }),
        }


class ProductionResourceForm(forms.ModelForm):
    """Form for adding resources to a production plan."""
    
    class Meta:
        model = ProductionResource
        fields = ["production_plan", "resource_type", "name", "number", "days", "rate"]
        widgets = {
            "production_plan": forms.Select(attrs={"class": "form-select"}),
            "resource_type": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. Skilled Labour, Bobcat"}),
            "number": forms.NumberInput(attrs={"class": "form-input", "placeholder": "1"}),
            "days": forms.NumberInput(attrs={"class": "form-input", "placeholder": "1"}),
            "rate": forms.NumberInput(attrs={"class": "form-input", "placeholder": "0.00"}),
        }

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id', None)
        super().__init__(*args, **kwargs)
        if project_id:
            self.fields['production_plan'].queryset = ProductionPlan.objects.filter(project_id=project_id)
