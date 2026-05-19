from typing import cast

from django import forms
from django.forms import ModelChoiceField, inlineformset_factory

from .models import (
    ContractorLabourCrew,
    ContractorLabourSpecification,
    ContractorMaterial,
    ContractorPlantCost,
    ContractorPlantSpecification,
    ContractorPreliminaryCost,
    ContractorPreliminarySpecification,
    ContractorSpecification,
    ContractorSpecificationComponent,
    ContractorTradeCode,
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


def _attach_datalists(form, field_to_list_id):
    """Wire a `list="<datalist-id>"` attribute onto each given field's widget.

    Renders a combobox in the browser: an editable text input that also
    surfaces existing values as suggestions. Templates supply the matching
    `<datalist id="...">` block.
    """
    for field_name, list_id in field_to_list_id.items():
        field = form.fields.get(field_name)
        if field is not None:
            field.widget.attrs["list"] = list_id


def _setup_trade_code(form, queryset):
    """Configure the ``trade_code`` field as a required dropdown that lists
    trades by their full trade name only (no prefix)."""
    field = cast(ModelChoiceField, form.fields["trade_code"])
    field.queryset = queryset
    field.required = True
    field.label = "Trade"
    field.empty_label = "Select a trade…"
    field.label_from_instance = (  # ty:ignore[invalid-assignment]
        lambda obj: obj.trade_name or str(obj)
    )


class MaterialForm(forms.ModelForm):
    class Meta:
        model = ProjectMaterial
        fields = [
            "trade_name",
            "material_code",
            "unit",
            "pack_qty",
            "pack_cost",
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
            "pack_qty": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "1", "step": "0.0001"}
            ),
            "pack_cost": forms.NumberInput(
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
        _setup_trade_code(
            self,
            ProjectTradeCode.objects.filter(project=project)
            if project
            else ProjectTradeCode.objects.none(),
        )
        _attach_datalists(
            self,
            {"section": "spec-sections", "unit_label": "spec-units"},
        )


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
            "trade_code",
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
            "trade_code": forms.Select(attrs={"class": TAILWIND_SELECT}),
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
        _setup_trade_code(
            self,
            ProjectTradeCode.objects.filter(project=project)
            if project
            else ProjectTradeCode.objects.none(),
        )
        _attach_datalists(
            self,
            {
                "section": "spec-sections",
                "unit": "spec-units",
            },
        )


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
            "pack_qty",
            "pack_cost",
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
            "pack_qty": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "1", "step": "0.0001"}
            ),
            "pack_cost": forms.NumberInput(
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
            "trade_code",
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
            "trade_code": forms.Select(attrs={"class": TAILWIND_SELECT}),
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
        _setup_trade_code(self, SystemTradeCode.objects.all())
        _attach_datalists(
            self,
            {
                "section": "spec-sections",
                "unit": "spec-units",
            },
        )


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
        _setup_trade_code(self, SystemTradeCode.objects.all())
        _attach_datalists(
            self,
            {"section": "spec-sections", "unit_label": "spec-units"},
        )


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
            "trade_code",
            "name",
            "unit",
            "daily_production",
            "operator_factor",
            "site_factor",
        ]
        widgets = {
            "section": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "trade_code": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Excavations - TLB Trenches",
                }
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. m3"}
            ),
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
        _setup_trade_code(
            self,
            ProjectTradeCode.objects.filter(project=project)
            if project
            else ProjectTradeCode.objects.none(),
        )
        _attach_datalists(
            self,
            {
                "section": "spec-sections",
                "unit": "spec-units",
            },
        )


class SystemPlantSpecificationForm(forms.ModelForm):
    class Meta:
        model = SystemPlantSpecification
        fields = [
            "section",
            "trade_code",
            "name",
            "unit",
            "daily_production",
            "operator_factor",
            "site_factor",
        ]
        widgets = {
            "section": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "trade_code": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Excavations - TLB Trenches",
                }
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. m3"}
            ),
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
        _setup_trade_code(self, SystemTradeCode.objects.all())
        _attach_datalists(
            self,
            {
                "section": "spec-sections",
                "unit": "spec-units",
            },
        )


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
        fields = ["section", "trade_code", "name", "unit", "preliminary_type"]
        widgets = {
            "section": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "trade_code": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Site Establishment",
                }
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Sum"}
            ),
            "preliminary_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        _setup_trade_code(
            self,
            ProjectTradeCode.objects.filter(project=project)
            if project
            else ProjectTradeCode.objects.none(),
        )
        _attach_datalists(
            self,
            {
                "section": "spec-sections",
                "unit": "spec-units",
            },
        )


class SystemPreliminarySpecificationForm(forms.ModelForm):
    class Meta:
        model = SystemPreliminarySpecification
        fields = ["section", "trade_code", "name", "unit", "preliminary_type"]
        widgets = {
            "section": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "trade_code": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Site Establishment",
                }
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Sum"}
            ),
            "preliminary_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _setup_trade_code(self, SystemTradeCode.objects.all())
        _attach_datalists(
            self,
            {
                "section": "spec-sections",
                "unit": "spec-units",
            },
        )


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


# ── Contractor Library Forms ─────────────────────────────────────
# These mirror the System* forms but bind to Contractor* models. The
# `company` FK is set by the view before save, not exposed on the form.


class ContractorTradeCodeForm(forms.ModelForm):
    class Meta:
        model = ContractorTradeCode
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


class ContractorMaterialForm(forms.ModelForm):
    class Meta:
        model = ContractorMaterial
        fields = [
            "trade_name",
            "material_code",
            "unit",
            "pack_qty",
            "pack_cost",
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
            "pack_qty": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "1", "step": "0.0001"}
            ),
            "pack_cost": forms.NumberInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "0.00", "step": "0.01"}
            ),
            "material_variety": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Portland Cement"}
            ),
            "market_spec": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. 42.5N Structural"}
            ),
        }


class ContractorLabourCrewForm(forms.ModelForm):
    class Meta:
        model = ContractorLabourCrew
        fields = [
            "crew_type",
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
                "skilled",
                "semi_skilled",
                "general",
                "daily_production",
                "skilled_rate",
                "semi_skilled_rate",
                "general_rate",
            ]
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["crew_type"].widget = forms.TextInput(
            attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Crew 1 - 1:2:2"}
        )


class ContractorLabourSpecificationForm(forms.ModelForm):
    class Meta:
        model = ContractorLabourSpecification
        fields = [
            "section",
            "trade_code",
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
            "trade_code": forms.Select(attrs={"class": TAILWIND_SELECT}),
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

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        crew_qs = ContractorLabourCrew.objects.all()
        if company is not None:
            crew_qs = crew_qs.filter(company=company)
        cast(ModelChoiceField, self.fields["crew"]).queryset = crew_qs
        tc_qs = ContractorTradeCode.objects.all()
        if company is not None:
            tc_qs = tc_qs.filter(company=company)
        else:
            tc_qs = ContractorTradeCode.objects.none()
        _setup_trade_code(self, tc_qs)
        _attach_datalists(
            self,
            {
                "section": "spec-sections",
                "unit": "spec-units",
            },
        )


class ContractorSpecificationForm(forms.ModelForm):
    class Meta:
        model = ContractorSpecification
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

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        tc_qs = ContractorTradeCode.objects.all()
        if company is not None:
            tc_qs = tc_qs.filter(company=company)
        else:
            tc_qs = ContractorTradeCode.objects.none()
        _setup_trade_code(self, tc_qs)
        _attach_datalists(
            self,
            {"section": "spec-sections", "unit_label": "spec-units"},
        )


class ContractorSpecificationComponentForm(forms.ModelForm):
    class Meta:
        model = ContractorSpecificationComponent
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

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        mat_qs = ContractorMaterial.objects.all()
        if company is not None:
            mat_qs = mat_qs.filter(company=company)
        cast(ModelChoiceField, self.fields["material"]).queryset = mat_qs


ContractorSpecificationComponentFormSet = inlineformset_factory(
    ContractorSpecification,
    ContractorSpecificationComponent,
    form=ContractorSpecificationComponentForm,
    extra=4,
    can_delete=False,
)


class ContractorPlantCostForm(forms.ModelForm):
    class Meta:
        model = ContractorPlantCost
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


class ContractorPlantSpecificationForm(forms.ModelForm):
    class Meta:
        model = ContractorPlantSpecification
        fields = [
            "section",
            "trade_code",
            "name",
            "unit",
            "daily_production",
            "operator_factor",
            "site_factor",
        ]
        widgets = {
            "section": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "trade_code": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Excavations - TLB Trenches",
                }
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. m3"}
            ),
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

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        tc_qs = ContractorTradeCode.objects.all()
        if company is not None:
            tc_qs = tc_qs.filter(company=company)
        else:
            tc_qs = ContractorTradeCode.objects.none()
        _setup_trade_code(self, tc_qs)
        _attach_datalists(
            self,
            {
                "section": "spec-sections",
                "unit": "spec-units",
            },
        )


class ContractorPreliminaryCostForm(forms.ModelForm):
    class Meta:
        model = ContractorPreliminaryCost
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


class ContractorPreliminarySpecificationForm(forms.ModelForm):
    class Meta:
        model = ContractorPreliminarySpecification
        fields = ["section", "trade_code", "name", "unit", "preliminary_type"]
        widgets = {
            "section": forms.TextInput(attrs={"class": TAILWIND_INPUT}),
            "trade_code": forms.Select(attrs={"class": TAILWIND_SELECT}),
            "name": forms.TextInput(
                attrs={
                    "class": TAILWIND_INPUT,
                    "placeholder": "e.g. Site Establishment",
                }
            ),
            "unit": forms.TextInput(
                attrs={"class": TAILWIND_INPUT, "placeholder": "e.g. Sum"}
            ),
            "preliminary_type": forms.Select(attrs={"class": TAILWIND_SELECT}),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        tc_qs = ContractorTradeCode.objects.all()
        if company is not None:
            tc_qs = tc_qs.filter(company=company)
        else:
            tc_qs = ContractorTradeCode.objects.none()
        _setup_trade_code(self, tc_qs)
        _attach_datalists(
            self,
            {
                "section": "spec-sections",
                "unit": "spec-units",
            },
        )
