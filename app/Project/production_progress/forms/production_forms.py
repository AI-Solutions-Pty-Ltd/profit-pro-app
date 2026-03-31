from django import forms
from ..models.production_models import (
    DailyProduction,
    ProductionPlan,
    ProductionResource,
    DailyActivityReport,
    DailyActivityEntry,
    DailyLabourUsage,
    DailyPlantUsage,
)
from django.forms import inlineformset_factory, formset_factory


class DailyProductionForm(forms.ModelForm):
    """Form for logging daily notes."""

    class Meta:
        model = DailyProduction
        fields = [
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "rows": 5,
                    "placeholder": "Enter notes here...",
                }
            ),
        }


class ProductionPlanForm(forms.ModelForm):
    """Form for production planning items."""

    class Meta:
        model = ProductionPlan
        fields = [
            "activity",
            "start_date",
            "finish_date",
            "duration",
            "quantity",
            "unit",
        ]
        widgets = {
            "activity": forms.TextInput(
                attrs={"id": "activity", "placeholder": "Enter Activity (e.g., Bricks)"}
            ),
            "start_date": forms.DateInput(
                attrs={
                    "id": "start_date",
                    "type": "date",
                    "onchange": "calculateDuration()",
                    "style": "color-scheme: light;",
                }
            ),
            "finish_date": forms.DateInput(
                attrs={
                    "id": "finish_date",
                    "type": "date",
                    "onchange": "calculateDuration()",
                    "style": "color-scheme: light;",
                }
            ),
            "duration": forms.NumberInput(
                attrs={
                    "id": "duration",
                    "readonly": "readonly",
                    "tabindex": "-1",
                    "required": False,
                }
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "id": "quantity",
                    "step": "0.01",
                    "placeholder": "10000.00",
                    "format": "{:.2f}",
                }
            ),
            "unit": forms.TextInput(
                attrs={"id": "unit", "placeholder": "Unit e.g. bricks"}
            ),
        }


class ProductionResourceForm(forms.ModelForm):
    """Form for adding resources to a production plan."""

    class Meta:
        model = ProductionResource
        fields = [
            "production_plan",
            "resource_type",
            "skill_type",
            "plant_type",
            "name",
            "number",
            "days",
            "rate",
        ]
        widgets = {
            "production_plan": forms.Select(attrs={"class": "form-select"}),
            "resource_type": forms.Select(
                attrs={"class": "form-select", "onchange": "toggleResourceTypes()"}
            ),
            "skill_type": forms.Select(
                attrs={"class": "form-select", "onchange": "updateFromSkillType()"}
            ),
            "plant_type": forms.Select(
                attrs={"class": "form-select", "onchange": "updateFromPlantType()"}
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Selection auto-fills this field",
                    "readonly": "readonly",
                }
            ),
            "number": forms.NumberInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "1",
                    "min": "1",
                    "step": "1",
                }
            ),
            "days": forms.NumberInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "1",
                    "min": "1",
                    "step": "1",
                }
            ),
            "rate": forms.NumberInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "0.00",
                    "min": "0.00",
                    "step": "0.10",
                    "readonly": "readonly",
                }
            ),
        }

    name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Selection auto-fills name",
                "readonly": "readonly",
            }
        ),
    )
    rate = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "placeholder": "0.00",
                "min": "0.00",
                "step": "0.10",
                "readonly": "readonly",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id", None)
        disabled_fields = kwargs.pop("disabled_fields", [])
        super().__init__(*args, **kwargs)
        if project_id:
            self.fields["production_plan"].queryset = ProductionPlan.objects.filter(
                project_id=project_id
            )
            self.fields["skill_type"].queryset = self.fields[
                "skill_type"
            ].queryset.filter(project_id=project_id)
            self.fields["plant_type"].queryset = self.fields[
                "plant_type"
            ].queryset.filter(project_id=project_id)
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
            "production_plan": forms.Select(
                attrs={"class": "form-select", "readonly": True}
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "0.00",
                    "step": "1",
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id", None)
        super().__init__(*args, **kwargs)
        if project_id:
            self.fields["production_plan"].queryset = ProductionPlan.objects.filter(
                project_id=project_id
            )

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")
        return quantity


class DailyLabourUsageForm(forms.ModelForm):
    class Meta:
        model = DailyLabourUsage
        fields = ["resource", "number", "hours"]
        widgets = {
            "resource": forms.Select(attrs={"class": "form-select"}),
            "number": forms.NumberInput(attrs={"class": "form-input", "min": "0"}),
            "hours": forms.NumberInput(
                attrs={"class": "form-input", "step": "0.1", "min": "0"}
            ),
        }

    def __init__(self, *args, **kwargs):
        activity_id = kwargs.pop("activity_id", None)
        super().__init__(*args, **kwargs)
        if activity_id:
            # Filter resources by the selected production plan
            self.fields["resource"].queryset = ProductionResource.objects.filter(
                production_plan_id=activity_id, resource_type="LABOUR"
            )


class DailyPlantUsageForm(forms.ModelForm):
    activity = forms.ModelChoiceField(
        queryset=ProductionPlan.objects.none(), widget=forms.HiddenInput()
    )

    class Meta:
        model = DailyPlantUsage
        fields = ["entry", "resource", "number", "hours"]
        widgets = {
            "entry": forms.HiddenInput(),
            "resource": forms.Select(attrs={"class": "form-select"}),
            "number": forms.NumberInput(attrs={"class": "form-input", "min": "0"}),
            "hours": forms.NumberInput(
                attrs={"class": "form-input", "step": "0.1", "min": "0"}
            ),
        }

    def __init__(self, *args, **kwargs):
        activity_id = kwargs.pop("activity_id", None)
        super().__init__(*args, **kwargs)
        if activity_id:
            self.fields["resource"].queryset = ProductionResource.objects.filter(
                production_plan_id=activity_id, resource_type="PLANT"
            )
            self.fields["activity"].queryset = ProductionPlan.objects.filter(
                id=activity_id
            )


class AggregatedLabourForm(forms.Form):
    activity = forms.ModelChoiceField(
        queryset=ProductionPlan.objects.none(), widget=forms.HiddenInput()
    )
    quantity = forms.DecimalField(
        min_value=0,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "form-input", "placeholder": "0.00", "step": "0.01"}
        ),
    )
    skilled_number = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-input", "placeholder": "0"}),
    )
    semi_skilled_number = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-input", "placeholder": "0"}),
    )
    unskilled_number = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-input", "placeholder": "0"}),
    )
    total_hours = forms.DecimalField(
        min_value=0,
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "form-input", "placeholder": "0.00", "step": "0.1"}
        ),
    )

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id", None)
        super().__init__(*args, **kwargs)
        if project_id:
            self.fields["activity"].queryset = ProductionPlan.objects.filter(
                project_id=project_id
            )

    def clean(self):
        cleaned_data = super().clean()
        skilled = cleaned_data.get("skilled_number") or 0
        semi = cleaned_data.get("semi_skilled_number") or 0
        unskilled = cleaned_data.get("unskilled_number") or 0
        hours = cleaned_data.get("total_hours") or 0
        if hours > 0 and (skilled + semi + unskilled) == 0:
            raise forms.ValidationError(
                "If hours are entered, at least one labour category must have a number > 0"
            )
        return cleaned_data


DailyLabourUsageFormSet = inlineformset_factory(
    DailyActivityEntry,
    DailyLabourUsage,
    form=DailyLabourUsageForm,
    extra=3,
    can_delete=True,
)

DailyPlantUsageFormSet = inlineformset_factory(
    DailyActivityEntry,
    DailyPlantUsage,
    form=DailyPlantUsageForm,
    extra=3,
    can_delete=True,
)

AggregatedLabourFormSet = formset_factory(
    AggregatedLabourForm, extra=0, can_delete=False
)
