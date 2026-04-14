from typing import cast

from django import forms
from django.forms import ModelChoiceField, inlineformset_factory

from .models import (
    ProjectAssumptions,
    ProjectLabourCrew,
    ProjectLabourSpecification,
    ProjectMaterial,
    ProjectPlantCost,
    ProjectPlantSpecification,
    ProjectPreliminaryCost,
    ProjectPreliminarySpecification,
    ProjectSpecification,
    ProjectSpecificationComponent,
    ProjectTradeCode,
    SystemLabourCrew,
    SystemLabourSpecification,
    SystemMaterial,
    SystemPlantCost,
    SystemPlantSpecification,
    SystemPreliminaryCost,
    SystemPreliminarySpecification,
    SystemSpecification,
    SystemSpecificationComponent,
    SystemTradeCode,
)

TAILWIND_INPUT = "block w-full rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
TAILWIND_SELECT = TAILWIND_INPUT


class MaterialForm(forms.ModelForm):
    class Meta:
        model = ProjectMaterial
        fields = [
            "trade_name",
            "material_code",
            "unit",
            "market_rate",
            "material_variety",
            "market_spec",
        ]
        widgets = {
            "trade_name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. CFR-Concrete, Formwork & Reinforcement",
                }
            ),
            "material_code": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Cement 42.5N"}
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Bag"}
            ),
            "market_rate": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "0.00", "step": "0.01"}
            ),
            "material_variety": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Portland Cement"}
            ),
            "market_spec": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. 42.5N Structural"}
            ),
        }


class SpecificationForm(forms.ModelForm):
    class Meta:
        model = ProjectSpecification
        fields = ["section", "name", "trade_code", "unit_label"]
        widgets = {
            "section": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Section 1"}
            ),
            "name": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. 25MPa"}
            ),
            "trade_code": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "unit_label": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. m3"}
            ),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            cast(
                ModelChoiceField, self.fields["trade_code"]
            ).queryset = ProjectTradeCode.objects.filter(project=project)


class SpecificationComponentForm(forms.ModelForm):
    class Meta:
        model = ProjectSpecificationComponent
        fields = ["material", "label", "qty_per_unit", "sort_order"]
        widgets = {
            "material": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "label": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Cement 42.5N"}
            ),
            "qty_per_unit": forms.NumberInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "0.0000",
                    "step": "0.0001",
                }
            ),
            "sort_order": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "0"}
            ),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            cast(
                ModelChoiceField, self.fields["material"]
            ).queryset = ProjectMaterial.objects.filter(project=project)


SpecificationComponentFormSet = inlineformset_factory(
    ProjectSpecification,
    ProjectSpecificationComponent,
    form=SpecificationComponentForm,
    extra=4,
    can_delete=False,
)


class LabourCrewForm(forms.ModelForm):
    class Meta:
        model = ProjectLabourCrew
        fields = [
            "crew_type",
            "crew_size",
            "skilled",
            "semi_skilled",
            "general",
            "skilled_rate",
            "semi_skilled_rate",
            "general_rate",
        ]
        widgets = {
            field: forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"})
            for field in [
                "crew_size",
                "skilled",
                "semi_skilled",
                "general",
                "skilled_rate",
                "semi_skilled_rate",
                "general_rate",
            ]
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["crew_type"].widget = forms.TextInput(
            attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Crew 1 - 1:2:2"}
        )


class ExcelImportForm(forms.Form):
    file = forms.FileField(
        label="Excel File",
        widget=forms.ClearableFileInput(
            attrs={
                "class": TAILWIND_INPUT,
                "accept": ".xlsx",
            }
        ),
    )

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.endswith(".xlsx"):
            raise forms.ValidationError("Only .xlsx files are supported.")
        return f


class LabourSpecificationForm(forms.ModelForm):
    class Meta:
        model = ProjectLabourSpecification
        fields = [
            "section",
            "trade_name",
            "name",
            "unit",
            "crew",
            "daily_production",
            "team_mix",
            "site_factor",
            "tools_factor",
            "leadership_factor",
        ]
        widgets = {
            "section": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "trade_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Excavations - Manual Trenches",
                }
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. m3"}
            ),
            "crew": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "daily_production": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "team_mix": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.0001"}
            ),
            "site_factor": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.0001"}
            ),
            "tools_factor": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.0001"}
            ),
            "leadership_factor": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.0001"}
            ),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            cast(
                ModelChoiceField, self.fields["crew"]
            ).queryset = ProjectLabourCrew.objects.filter(project=project)


class SystemTradeCodeForm(forms.ModelForm):
    class Meta:
        model = SystemTradeCode
        fields = ["prefix", "trade_name"]
        widgets = {
            "prefix": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. CFR"}
            ),
            "trade_name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Concrete, Formwork & Reinforcement",
                }
            ),
        }


class SystemMaterialForm(forms.ModelForm):
    class Meta:
        model = SystemMaterial
        fields = [
            "trade_name",
            "material_code",
            "unit",
            "market_rate",
            "material_variety",
            "market_spec",
        ]
        widgets = {
            "trade_name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. CFR-Concrete, Formwork & Reinforcement",
                }
            ),
            "material_code": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Cement 42.5N"}
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Bag"}
            ),
            "market_rate": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "0.00", "step": "0.01"}
            ),
            "material_variety": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Portland Cement"}
            ),
            "market_spec": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. 42.5N Structural"}
            ),
        }


class SystemLabourCrewForm(forms.ModelForm):
    class Meta:
        model = SystemLabourCrew
        fields = [
            "crew_type",
            "crew_size",
            "skilled",
            "semi_skilled",
            "general",
            "daily_production",
            "skilled_rate",
            "semi_skilled_rate",
            "general_rate",
        ]
        widgets = {
            field: forms.NumberInput(attrs={"class": TAILWIND_INPUT, "step": "0.01"})
            for field in [
                "crew_size",
                "skilled",
                "semi_skilled",
                "general",
                "daily_production",
                "skilled_rate",
                "semi_skilled_rate",
                "general_rate",
            ]
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["crew_type"].widget = forms.TextInput(
            attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Crew 1 - 1:2:2"}
        )


class SystemLabourSpecificationForm(forms.ModelForm):
    class Meta:
        model = SystemLabourSpecification
        fields = [
            "section",
            "trade_name",
            "name",
            "unit",
            "crew",
            "daily_production",
            "team_mix",
            "site_factor",
            "tools_factor",
            "leadership_factor",
        ]
        widgets = {
            "section": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "trade_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Excavations - Manual Trenches",
                }
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. m3"}
            ),
            "crew": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "daily_production": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "team_mix": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.0001"}
            ),
            "site_factor": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.0001"}
            ),
            "tools_factor": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.0001"}
            ),
            "leadership_factor": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.0001"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cast(
            ModelChoiceField, self.fields["crew"]
        ).queryset = SystemLabourCrew.objects.all()


class SystemSpecificationForm(forms.ModelForm):
    class Meta:
        model = SystemSpecification
        fields = ["section", "name", "trade_code", "unit_label"]
        widgets = {
            "section": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Section 1"}
            ),
            "name": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. 25MPa"}
            ),
            "trade_code": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "unit_label": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. m3"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cast(
            ModelChoiceField, self.fields["trade_code"]
        ).queryset = SystemTradeCode.objects.all()


class SystemSpecificationComponentForm(forms.ModelForm):
    class Meta:
        model = SystemSpecificationComponent
        fields = ["material", "label", "qty_per_unit", "sort_order"]
        widgets = {
            "material": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "label": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Cement 42.5N"}
            ),
            "qty_per_unit": forms.NumberInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "0.0000",
                    "step": "0.0001",
                }
            ),
            "sort_order": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "0"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cast(
            ModelChoiceField, self.fields["material"]
        ).queryset = SystemMaterial.objects.all()


SystemSpecificationComponentFormSet = inlineformset_factory(
    SystemSpecification,
    SystemSpecificationComponent,
    form=SystemSpecificationComponentForm,
    extra=4,
    can_delete=False,
)


# ── Plant Cost Forms ──────────────────────────────────────────────


class PlantCostForm(forms.ModelForm):
    class Meta:
        model = ProjectPlantCost
        fields = ["name", "hourly_production", "hourly_rate"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. TLB - Case 580",
                }
            ),
            "hourly_production": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "hourly_rate": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
        }


class SystemPlantCostForm(forms.ModelForm):
    class Meta:
        model = SystemPlantCost
        fields = ["name", "hourly_production", "hourly_rate"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. TLB - Case 580",
                }
            ),
            "hourly_production": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "hourly_rate": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
        }


# ── Plant Specification Forms ────────────────────────────────────


class PlantSpecificationForm(forms.ModelForm):
    class Meta:
        model = ProjectPlantSpecification
        fields = [
            "section",
            "trade_name",
            "name",
            "unit",
            "plant_type",
            "daily_production",
            "operator_factor",
            "site_factor",
        ]
        widgets = {
            "section": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "trade_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Excavations - TLB Trenches",
                }
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. m3"}
            ),
            "plant_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "daily_production": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "operator_factor": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.0001"}
            ),
            "site_factor": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.0001"}
            ),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            cast(
                ModelChoiceField, self.fields["plant_type"]
            ).queryset = ProjectPlantCost.objects.filter(project=project)


class SystemPlantSpecificationForm(forms.ModelForm):
    class Meta:
        model = SystemPlantSpecification
        fields = [
            "section",
            "trade_name",
            "name",
            "unit",
            "plant_type",
            "daily_production",
            "operator_factor",
            "site_factor",
        ]
        widgets = {
            "section": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "trade_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Excavations - TLB Trenches",
                }
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. m3"}
            ),
            "plant_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "daily_production": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "operator_factor": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.0001"}
            ),
            "site_factor": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.0001"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cast(
            ModelChoiceField, self.fields["plant_type"]
        ).queryset = SystemPlantCost.objects.all()


# ── Preliminary Cost Forms ───────────────────────────────────────


class PreliminaryCostForm(forms.ModelForm):
    class Meta:
        model = ProjectPreliminaryCost
        fields = [
            "name",
            "preliminary_type",
            "sum_value",
            "amount",
            "number_per_month",
            "monthly_rate",
            "months",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Site Establishment",
                }
            ),
            "preliminary_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "sum_value": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "amount": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "number_per_month": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "monthly_rate": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "months": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
        }


class SystemPreliminaryCostForm(forms.ModelForm):
    class Meta:
        model = SystemPreliminaryCost
        fields = [
            "name",
            "preliminary_type",
            "sum_value",
            "amount",
            "number_per_month",
            "monthly_rate",
            "months",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Site Establishment",
                }
            ),
            "preliminary_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "sum_value": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "amount": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "number_per_month": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "monthly_rate": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "months": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
        }


# ── Preliminary Specification Forms ──────────────────────────────


class PreliminarySpecificationForm(forms.ModelForm):
    class Meta:
        model = ProjectPreliminarySpecification
        fields = ["section", "trade_name", "name", "unit", "amount"]
        widgets = {
            "section": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "trade_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Site Establishment",
                }
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Sum"}
            ),
            "amount": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
        }


class SystemPreliminarySpecificationForm(forms.ModelForm):
    class Meta:
        model = SystemPreliminarySpecification
        fields = ["section", "trade_name", "name", "unit", "amount"]
        widgets = {
            "section": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "trade_name": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Site Establishment",
                }
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Sum"}
            ),
            "amount": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
        }


class ProjectAssumptionsForm(forms.ModelForm):
    class Meta:
        model = ProjectAssumptions
        fields = [
            "material_markup_pct",
            "labour_markup_pct",
            "transport_pct",
            "wastage_pct",
        ]
        widgets = {
            "material_markup_pct": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "labour_markup_pct": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "transport_pct": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
            "wastage_pct": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "step": "0.01"}
            ),
        }
