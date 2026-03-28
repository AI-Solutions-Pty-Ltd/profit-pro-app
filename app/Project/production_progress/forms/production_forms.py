from django import forms
from ..models.production_models import (
    DailyProduction, 
    ProductionPlan, 
    ProductionResource,
    DailyActivityReport,
    DailyActivityEntry,
    DailyLabourUsage,
    DailyPlantUsage
)
from django.forms import inlineformset_factory



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
                "placeholder": "10000.00",
                "format": "{:.2f}"
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
        fields = ["production_plan", "resource_type", "skill_type", "plant_type", "name", "number", "days", "rate"]
        widgets = {
            "production_plan": forms.Select(attrs={"class": "form-select"}),
            "resource_type": forms.Select(attrs={"class": "form-select", "onchange": "toggleResourceTypes()"}),
            "skill_type": forms.Select(attrs={"class": "form-select", "onchange": "updateFromSkillType()"}),
            "plant_type": forms.Select(attrs={"class": "form-select", "onchange": "updateFromPlantType()"}),
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Selection auto-fills this field", "readonly": "readonly"}),
            "number": forms.NumberInput(attrs={"class": "form-input", "placeholder": "1", "min": "1", "step": "1"}),
            "days": forms.NumberInput(attrs={"class": "form-input", "placeholder": "1", "min": "1", "step": "1"}),
            "rate": forms.NumberInput(attrs={"class": "form-input", "placeholder": "0.00", "min": "0.00", "step": "0.10", "readonly": "readonly"}),
        }

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id', None)
        disabled_fields = kwargs.pop('disabled_fields', [])
        super().__init__(*args, **kwargs)
        if project_id:
            self.fields['production_plan'].queryset = ProductionPlan.objects.filter(project_id=project_id)
            self.fields['skill_type'].queryset = self.fields['skill_type'].queryset.filter(project_id=project_id)
            self.fields['plant_type'].queryset = self.fields['plant_type'].queryset.filter(project_id=project_id)
        for field_name in disabled_fields:
            if field_name in self.fields:
                self.fields[field_name].disabled = True

class DailyActivityReportForm(forms.ModelForm):
    class Meta:
        model = DailyActivityReport
        fields = ["date"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
        }


class DailyActivityEntryForm(forms.ModelForm):
    class Meta:
        model = DailyActivityEntry
        fields = ["production_plan", "quantity"]
        widgets = {
            "production_plan": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={
                "class": "form-input", 
                "placeholder": "0.00", 
                "step": "1", 
                "min": "0"
            }),
        }

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id', None)
        super().__init__(*args, **kwargs)
        if project_id:
            self.fields['production_plan'].queryset = ProductionPlan.objects.filter(project_id=project_id)


class DailyLabourUsageForm(forms.ModelForm):
    class Meta:
        model = DailyLabourUsage
        fields = ["resource", "number", "hours"]
        widgets = {
            "resource": forms.Select(attrs={"class": "form-select"}),
            "number": forms.NumberInput(attrs={"class": "form-input", "min": "0"}),
            "hours": forms.NumberInput(attrs={"class": "form-input", "step": "0.1", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        activity_id = kwargs.pop('activity_id', None)
        super().__init__(*args, **kwargs)
        if activity_id:
            # Filter resources by the selected production plan
            self.fields['resource'].queryset = ProductionResource.objects.filter(
                production_plan_id=activity_id, 
                resource_type='LABOUR'
            )


class DailyPlantUsageForm(forms.ModelForm):
    class Meta:
        model = DailyPlantUsage
        fields = ["resource", "number", "hours"]
        widgets = {
            "resource": forms.Select(attrs={"class": "form-select"}),
            "number": forms.NumberInput(attrs={"class": "form-input", "min": "0"}),
            "hours": forms.NumberInput(attrs={"class": "form-input", "step": "0.1", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        activity_id = kwargs.pop('activity_id', None)
        super().__init__(*args, **kwargs)
        if activity_id:
            self.fields['resource'].queryset = ProductionResource.objects.filter(
                production_plan_id=activity_id, 
                resource_type='PLANT'
            )


DailyLabourUsageFormSet = inlineformset_factory(
    DailyActivityEntry, DailyLabourUsage, form=DailyLabourUsageForm, extra=3, can_delete=True
)

DailyPlantUsageFormSet = inlineformset_factory(
    DailyActivityEntry, DailyPlantUsage, form=DailyPlantUsageForm, extra=3, can_delete=True
)
