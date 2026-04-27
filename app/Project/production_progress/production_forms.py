from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import inlineformset_factory

from app.core.Utilities.widgets import SearchableSelectWidget
from app.Estimator.models import (
    BOQItem,
    ProjectLabourSpecification,
    ProjectPlantSpecification,
)
from app.Project.models.unit_models import UnitOfMeasure

from .production_models import (
    DailyProduction,
    PlanDependency,
    ProductionPlan,
    ProductionResource,
)


class PlanFilterForm(forms.Form):
    """Form for filtering the productivity dashboard by plan."""

    plan_id = forms.ModelChoiceField(
        queryset=ProductionPlan.objects.none(),
        widget=SearchableSelectWidget(
            attrs={
                "onchange": "this.form.submit()",
                "class": "w-full",
            }
        ),
        required=False,
        label="Select Plan",
    )

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id", None)
        super().__init__(*args, **kwargs)
        if project_id:
            plans = (
                ProductionPlan.objects.filter(
                    project_id=project_id, labour_activity__isnull=False
                )
                .select_related("labour_activity")
                .order_by("activity")
            )
            self.fields["plan_id"].queryset = plans

            # Customize the label to match the template's logic: activity (section/bill_no)
            self.fields["plan_id"].label_from_instance = lambda obj: (
                f"{obj.activity} ({obj.section}/{obj.bill_no})"
                if obj.section or obj.bill_no
                else f"{obj.activity}"
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

    duration = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "id": "duration",
                "readonly": "readonly",
                "tabindex": "-1",
            }
        ),
    )
    daily_rate = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                "id": "daily_rate",
                "readonly": "readonly",
                "tabindex": "-1",
            }
        ),
    )

    section = forms.CharField(
        required=False,
        widget=forms.Select(attrs={"id": "id_section", "class": "form-select"}),
    )
    bill_no = forms.CharField(
        required=False,
        widget=forms.Select(attrs={"id": "id_bill_no", "class": "form-select"}),
    )
    labour_activity = forms.ModelChoiceField(
        queryset=ProjectLabourSpecification.objects.none(),
        required=False,
        widget=SearchableSelectWidget(
            resource_type="labor_activity",
            attrs={"id": "id_labour_activity"},
        ),
    )
    plant_specification = forms.ModelChoiceField(
        queryset=ProjectPlantSpecification.objects.none(),
        required=False,
        widget=SearchableSelectWidget(
            resource_type="plant_specification",
            attrs={"id": "id_plant_specification"},
        ),
    )
    unit = forms.ModelChoiceField(
        queryset=UnitOfMeasure.objects.all(),
        to_field_name="short_name",
        widget=SearchableSelectWidget(
            resource_type="unit_of_measure",
            create_url=True,
            attrs={"id": "unit"},
        ),
        required=True,
    )

    class Meta:
        model = ProductionPlan
        fields = [
            "parent",
            "section",
            "bill_no",
            "labour_activity",
            "plant_specification",
            "activity",
            "start_date",
            "finish_date",
            "duration",
            "daily_rate",
            "quantity",
            "unit",
        ]
        widgets = {
            "activity": forms.TextInput(
                attrs={
                    "id": "activity",
                    "class": "form-input",
                    "placeholder": "Activity name",
                }
            ),
            "parent": SearchableSelectWidget(attrs={"id": "id_parent"}),
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
            "quantity": forms.NumberInput(
                attrs={
                    "id": "quantity",
                    "step": "0.01",
                    "placeholder": "10000.00",
                    "format": "{:.2f}",
                }
            ),
            "unit": SearchableSelectWidget(
                resource_type="unit_of_measure",
                attrs={"id": "unit", "readonly": "readonly"},
            ),
        }

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id", None)
        self.project_id = project_id
        super().__init__(*args, **kwargs)

        # Basic state
        parent_id = self.initial.get("parent") or (
            self.instance.parent_id if self.instance.pk else None
        )
        self.is_top_level = not parent_id
        self.is_new = not self.instance.pk

        if self.instance.pk and self.instance.parent_id:
            self.fields["parent"].disabled = True

        if project_id:
            # Populating Sections from BOQItems (Project-wide)
            sections = (
                BOQItem.objects.filter(project_id=project_id)
                .values_list("section", flat=True)
                .distinct()
                .order_by("section")
            )
            self.fields["section"].widget.choices = [("", "---------")] + [  # ty:ignore[unresolved-attribute]
                (s, s) for s in sections if s
            ]

            # Populating ALL Bills for the project to pass validation
            all_bills = (
                BOQItem.objects.filter(project_id=project_id)
                .values_list("bill_no", flat=True)
                .distinct()
                .order_by("bill_no")
            )
            self.fields["bill_no"].widget.choices = [("", "---------")] + [  # ty:ignore[unresolved-attribute]
                (b, b) for b in all_bills if b
            ]

            # Expand labour_activity queryset to include ALL specs for the project
            project_specs = ProjectLabourSpecification.objects.filter(
                project_id=project_id
            )
            self.fields["labour_activity"].queryset = project_specs  # ty:ignore[unresolved-attribute]
            self.fields[
                "plant_specification"
            ].queryset = ProjectPlantSpecification.objects.filter(project_id=project_id)  # ty:ignore[unresolved-attribute]

            # Configure plant_specification choice metadata
            if self.instance.pk and self.instance.plant_specification:
                components = (
                    self.instance.plant_specification.components.all().select_related(
                        "plant_type"
                    )
                )
                types = [c.plant_type.name for c in components if c.plant_type]
                self.fields["plant_specification"].widget.choice_data = {
                    str(self.instance.plant_specification_id): {
                        "data-type": ", ".join(sorted(set(types))) if types else ""
                    }
                }

            # Configure activity metadata for auto-fill in JS
            # We don't populate all groupings here because there could be many (Spec x Section x Bill)
            # Instead, the SearchableSelectWidget JS should handle fetching data from the AJAX endpoint.
            # However, we need to handle the case where we are editing an existing record.
            if self.instance.pk and self.instance.labour_activity:
                # Provide minimal metadata for the selected activity
                self.fields["labour_activity"].widget.choice_data = {
                    str(self.instance.labour_activity_id): {
                        "data-section": self.instance.section or "",
                        "data-bill-no": self.instance.bill_no or "",
                        "data-quantity": str(self.instance.quantity),
                        "data-unit": self.instance.unit,
                        "data-activity_name": self.instance.activity,
                        "data-daily-output": str(self.instance.daily_rate),
                    }
                }

            # Configure parent metadata
            parent_qs = ProductionPlan.objects.filter(
                project_id=project_id, is_archived=False
            ).exclude(labour_activity__isnull=False)
            if self.instance.pk:
                parent_qs = parent_qs.exclude(pk=self.instance.pk)

            self.fields["parent"].queryset = parent_qs  # ty:ignore[unresolved-attribute]
            self.fields["parent"].widget.choice_data = {
                str(plan.pk): {
                    "data-section": plan.section or "",
                    "data-bill-no": plan.bill_no or "",
                }
                for plan in parent_qs
            }

        self.fields["section"].required = not parent_id
        self.fields["bill_no"].required = not parent_id

        # ── Hardening Structural Headers ──────────────────────────────────────
        # If we are editing a non-leaf node (Section/Bill), prevent direct metric edits
        if self.instance.pk and not self.instance.is_leaf:
            readonly_fields = [
                "start_date",
                "finish_date",
                "duration",
                "quantity",
                "unit",
                "labour_activity",
                "plant_specification",
                "daily_rate",
                "section",
                "bill_no",
            ]
            for field in readonly_fields:
                if field in self.fields:
                    self.fields[field].disabled = True
                    # Add visual cues for disabled fields
                    if "class" not in self.fields[field].widget.attrs:
                        self.fields[field].widget.attrs["class"] = ""
                    self.fields[field].widget.attrs["class"] += (
                        " bg-gray-50 cursor-not-allowed"
                    )
                    self.fields[
                        field
                    ].help_text = "Calculated from children (Read-only)"
        self.fields["labour_activity"].required = False
        self.fields[
            "activity"
        ].required = not parent_id  # Activity name usually required

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data:
            return cleaned_data

        start_date = cleaned_data.get("start_date")
        finish_date = cleaned_data.get("finish_date")
        labour_activity = cleaned_data.get("labour_activity")
        section = cleaned_data.get("section")
        bill_no = cleaned_data.get("bill_no")
        activity = cleaned_data.get("activity")
        parent = cleaned_data.get("parent")
        unit_obj = cleaned_data.get("unit")

        # Convert unit object to its short_name string for the database
        if unit_obj:
            from app.Project.models.unit_models import UnitOfMeasure

            if isinstance(unit_obj, UnitOfMeasure):
                cleaned_data["unit"] = unit_obj.short_name

        # Inherit hierarchy from parent if not manually set
        if parent:
            if not section:
                cleaned_data["section"] = parent.section
            if not bill_no:
                cleaned_data["bill_no"] = parent.bill_no

        # If labor activity is selected, prioritize its values (usually handled by JS but good for safety)
        if labour_activity:
            if not section:
                cleaned_data["section"] = labour_activity.section
            if not activity:
                cleaned_data["activity"] = labour_activity.name

        activity = cleaned_data.get("activity")
        project = self.project_id or (
            self.instance.project if self.instance.pk else None
        )

        if start_date and finish_date and finish_date < start_date:
            raise ValidationError(
                {"finish_date": "Finish date cannot be before start date."}
            )

        # Check for overlapping plans for the same activity in this branch
        if start_date and finish_date and activity:
            overlapping_plans = ProductionPlan.objects.filter(
                activity=activity,
                section=cleaned_data.get("section", ""),
                bill_no=cleaned_data.get("bill_no", ""),
                is_archived=False,
            ).filter(Q(start_date__lte=finish_date) & Q(finish_date__gte=start_date))

            if self.instance.pk:
                overlapping_plans = overlapping_plans.exclude(pk=self.instance.pk)

            if project:
                overlapping_plans = overlapping_plans.filter(project=project)

            if overlapping_plans.exists():
                error_msg = f"An active plan for '{activity}' already exists in this section/bill within this date range."
                raise ValidationError(error_msg)

        # Enforce rule: Cannot change hierarchy/parent if it has children
        if (
            self.instance.pk
            and hasattr(self.instance, "children")
            and self.instance.children.filter(deleted=False).exists()
        ):
            old_instance = ProductionPlan.objects.get(pk=self.instance.pk)
            new_parent = cleaned_data.get("parent")
            new_section = cleaned_data.get("section")
            new_bill_no = cleaned_data.get("bill_no")

            if (
                old_instance.parent != new_parent
                or old_instance.section != new_section
                or old_instance.bill_no != new_bill_no
            ):
                raise ValidationError(
                    "Cannot change hierarchy or parent activity because it has dependent children."
                )

        if (
            cleaned_data.get("parent")
            and cleaned_data.get("parent").id == self.instance.pk  # ty:ignore[unresolved-attribute]
        ):
            raise ValidationError({"parent": "An activity cannot be its own parent."})

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
            production_plan_field: forms.ModelChoiceField = self.fields[
                "production_plan"
            ]  # type: ignore
            production_plan_field.queryset = ProductionPlan.objects.filter(
                project_id=project_id
            )

            skill_type_field: forms.ModelChoiceField = self.fields["skill_type"]  # type: ignore
            if skill_type_field.queryset:
                skill_type_field.queryset = skill_type_field.queryset.filter(
                    project_id=project_id
                )

            plant_type_field: forms.ModelChoiceField = self.fields["plant_type"]  # type: ignore
            if plant_type_field.queryset:
                plant_type_field.queryset = plant_type_field.queryset.filter(
                    project_id=project_id
                )
        for field_name in disabled_fields:
            if field_name in self.fields:
                self.fields[field_name].disabled = True


class BasePlanDependencyFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.project_id = kwargs.pop("project_id", None)
        self.plan_id = kwargs.pop("plan_id", None)
        # Capture current activity hierarchy for same-level validation
        self.parent_id = kwargs.pop("parent_id", None)
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["project_id"] = self.project_id
        kwargs["plan_id"] = self.plan_id
        return kwargs

    def add_fields(self, form, index):
        super().add_fields(form, index)
        # Enforce "same level" rule structurally
        if "predecessor" in form.fields:
            qs = form.fields["predecessor"].queryset
            if self.parent_id:
                qs = qs.filter(parent_id=self.parent_id)
            else:
                qs = qs.filter(parent__isnull=True)
            form.fields["predecessor"].queryset = qs.distinct()


class PlanDependencyForm(forms.ModelForm):
    class Meta:
        model = PlanDependency
        fields = ["predecessor"]
        widgets = {"predecessor": SearchableSelectWidget()}

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id", None)
        plan_id = kwargs.pop("plan_id", None)
        super().__init__(*args, **kwargs)
        if project_id:
            predecessor_field = self.fields["predecessor"]
            qs = ProductionPlan.objects.filter(project_id=project_id, is_archived=False)
            if plan_id:
                qs = qs.exclude(pk=plan_id)
            predecessor_field.queryset = qs  # ty:ignore[unresolved-attribute]


PlanDependencyFormSet = inlineformset_factory(
    ProductionPlan,
    PlanDependency,
    fk_name="successor",
    form=PlanDependencyForm,
    formset=BasePlanDependencyFormSet,
    extra=1,
    can_delete=True,
)
