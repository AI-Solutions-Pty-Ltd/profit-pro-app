from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import formset_factory, inlineformset_factory

from ..models.production_models import (
    DailyActivityEntry,
    DailyActivityReport,
    DailyLabourUsage,
    DailyPlantUsage,
    DailyProduction,
    ProductionPlan,
    ProductionResource,
)


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

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data:
            return cleaned_data

        start_date = cleaned_data.get("start_date")
        finish_date = cleaned_data.get("finish_date")
        activity = cleaned_data.get("activity")
        project = (
            self.instance.project if self.instance.pk else cleaned_data.get("project")
        )

        if start_date and finish_date and finish_date < start_date:
            raise ValidationError(
                {"finish_date": "Finish date cannot be before start date."}
            )

        # Check for overlapping plans for the same activity
        if start_date and finish_date and activity:
            overlapping_plans = ProductionPlan.objects.filter(
                activity=activity, is_archived=False
            ).filter(Q(start_date__lte=finish_date) & Q(finish_date__gte=start_date))

            if self.instance.pk:
                overlapping_plans = overlapping_plans.exclude(pk=self.instance.pk)
            # Since project might not be in cleaned_data if it's passed via kwargs in view
            # we rely on the instance's project which is usually set in form_valid or passed to __init__
            if project:
                overlapping_plans = overlapping_plans.filter(project=project)

            if overlapping_plans.exists():
                raise ValidationError(
                    f"An active plan for '{activity}' already exists within this date range ({start_date} to {finish_date})."
                )

        return cleaned_data


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
            "number": forms.NumberInput(attrs={"class": "input", "min": "0"}),
            "hours": forms.NumberInput(
                attrs={"class": "input", "step": "1", "min": "0", "placeholder": "0"}
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

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data is None:
            return cleaned_data

        resource = cleaned_data.get("resource")
        number = cleaned_data.get("number")
        hours = cleaned_data.get("hours")

        if number and number > 0:
            if not resource:
                raise ValidationError(
                    {"resource": "Resource is required if number is specified."}
                )
            if not hours or hours <= 0:
                raise ValidationError(
                    {"hours": "Hours must be greater than 0 if number is specified."}
                )
        elif hours and hours > 0:
            if not number or number <= 0:
                raise ValidationError(
                    {"number": "Number is required if hours are specified."}
                )

        return cleaned_data


class AggregatedLabourForm(forms.Form):
    activity = forms.ModelChoiceField(
        queryset=ProductionPlan.objects.none(), widget=forms.HiddenInput()
    )
    quantity = forms.DecimalField(
        min_value=0,
        max_digits=15,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(
            attrs={
                "class": "input  focus:border-primary",
                "placeholder": "0",
                "step": "1",
            }
        ),
    )
    skilled_number = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "input", "placeholder": "0"}),
    )
    semi_skilled_number = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "input", "placeholder": "0"}),
    )
    unskilled_number = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "input", "placeholder": "0"}),
    )
    total_hours = forms.DecimalField(
        min_value=0,
        max_digits=5,
        decimal_places=0,
        widget=forms.NumberInput(
            attrs={
                "class": "input",
                "placeholder": "0",
                "step": "1",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data:
            return cleaned_data

        plan = cleaned_data.get("activity")
        if not plan:
            return cleaned_data

        skilled = cleaned_data.get("skilled_number") or 0
        semi = cleaned_data.get("semi_skilled_number") or 0
        unskilled = cleaned_data.get("unskilled_number") or 0
        total_hours = cleaned_data.get("total_hours") or 0

        if (skilled > 0 or semi > 0 or unskilled > 0) and total_hours <= 0:
            raise ValidationError(
                {
                    "total_hours": "Total hours must be greater than 0 if labourers are specified."
                }
            )

        # Optional project check if project_id was passed to form
        if hasattr(self, "project_id") and self.project_id:
            if plan.project_id != self.project_id:
                raise ValidationError("Invalid activity for this project.")

        try:
            resources = ProductionResource.objects.filter(
                production_plan=plan, resource_type="LABOUR"
            )
            validation_errors = {}
            for res in resources:
                res_name = res.name.lower()
                if "skilled" in res_name and "semi" not in res_name:
                    if skilled > res.number:
                        validation_errors["skilled_number"] = (
                            f"Exceeds planned ({res.number})"
                        )
                elif "semi" in res_name:
                    if semi > res.number:
                        validation_errors["semi_skilled_number"] = (
                            f"Exceeds planned ({res.number})"
                        )
                elif "unskilled" in res_name:
                    if unskilled > res.number:
                        validation_errors["unskilled_number"] = (
                            f"Exceeds planned ({res.number})"
                        )

            if validation_errors:
                raise ValidationError(validation_errors)
        except Exception:
            pass

        return cleaned_data

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id", None)
        super().__init__(*args, **kwargs)
        if project_id:
            self.fields["activity"].queryset = ProductionPlan.objects.filter(
                project_id=project_id
            )


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
    extra=1,
    can_delete=True,
)

AggregatedLabourFormSet = formset_factory(
    AggregatedLabourForm, extra=0, can_delete=False
)
