from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import formset_factory, inlineformset_factory

from app.BillOfQuantities.models import Bill, LineItem, Package, Structure
from app.core.Utilities.widgets import SearchableSelectWidget
from app.Project.models.unit_models import UnitOfMeasure

from .production_models import (
    DailyActivityEntry,
    DailyActivityReport,
    DailyLabourUsage,
    DailyPlantUsage,
    DailyProduction,
    PlanDependency,
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
            "activity",
            "line_item",
            "structure",
            "bill",
            "package",
            "start_date",
            "finish_date",
            "duration",
            "quantity",
            "unit",
        ]
        widgets = {
            "activity": forms.HiddenInput(attrs={"id": "activity"}),
            "line_item": SearchableSelectWidget(
                resource_type="line_item",
                attrs={"id": "id_line_item"},
            ),
            "structure": SearchableSelectWidget(
                resource_type="structure",
                attrs={"id": "id_structure"},
            ),
            "bill": SearchableSelectWidget(
                resource_type="bill",
                attrs={"id": "id_bill", "required": False},
            ),
            "package": SearchableSelectWidget(
                resource_type="package",
                attrs={"id": "id_package", "required": False},
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
                attrs={"id": "unit"},
            ),
        }

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id", None)
        self.project_id = project_id
        super().__init__(*args, **kwargs)

        # Determine level context
        parent_id = self.initial.get("parent") or (
            self.instance.parent_id if self.instance.pk else None
        )
        self.is_top_level = not parent_id
        self.is_new = not self.instance.pk

        if self.instance.pk and self.instance.parent_id:
            self.fields["parent"].disabled = True

        if project_id:
            # Get already planned BoQ items to filter them out
            planned_qs = ProductionPlan.objects.filter(
                project_id=project_id, is_archived=False
            )
            if self.instance.pk:
                planned_qs = planned_qs.exclude(pk=self.instance.pk)

            planned_structure_ids = planned_qs.filter(
                structure__isnull=False
            ).values_list("structure_id", flat=True)
            planned_bill_ids = planned_qs.filter(bill__isnull=False).values_list(
                "bill_id", flat=True
            )
            planned_package_ids = planned_qs.filter(package__isnull=False).values_list(
                "package_id", flat=True
            )
            planned_line_item_ids = planned_qs.filter(
                line_item__isnull=False
            ).values_list("line_item_id", flat=True)

            # Configure BoQ fields with Quick Create
            self.fields["structure"].widget.resource_type = "structure"
            self.fields["structure"].widget.create_url = True
            self.fields["structure"].queryset = Structure.objects.filter(
                project_id=project_id
            ).exclude(id__in=planned_structure_ids)

            self.fields["bill"].widget.resource_type = "bill"
            self.fields["bill"].widget.create_url = True
            self.fields["bill"].queryset = Bill.objects.filter(
                structure__project_id=project_id
            ).exclude(id__in=planned_bill_ids)

            self.fields["package"].widget.resource_type = "package"
            self.fields["package"].widget.create_url = True
            self.fields["package"].queryset = Package.objects.filter(
                bill__structure__project_id=project_id
            ).exclude(id__in=planned_package_ids)

            self.fields["line_item"].queryset = LineItem.objects.filter(
                project_id=project_id, is_work=True
            ).exclude(id__in=planned_line_item_ids)

            # Set choice_data for line_item to support auto-fill
            line_item_qs = self.fields["line_item"].queryset
            self.fields["line_item"].widget.choice_data = {
                str(li.pk): {
                    "data-description": li.description,
                    "data-item-number": li.item_number,
                    "data-unit": li.unit_measurement,
                    "data-quantity": str(li.budgeted_quantity),
                }
                for li in line_item_qs
            }

            parent_qs = ProductionPlan.objects.filter(
                project_id=project_id, is_archived=False
            ).exclude(line_item__isnull=False)
            if self.instance.pk:
                parent_qs = parent_qs.exclude(pk=self.instance.pk)

            choice_data = {
                str(plan.pk): {
                    "data-structure-id": plan.structure_id or "",
                    "data-structure-label": str(plan.structure)
                    if plan.structure
                    else "",
                    "data-bill-id": plan.bill_id or "",
                    "data-bill-label": str(plan.bill) if plan.bill else "",
                    "data-package-id": plan.package_id or "",
                    "data-package-label": str(plan.package) if plan.package else "",
                    "data-line-item-id": plan.line_item_id or "",
                    "data-line-item-label": str(plan.line_item)
                    if plan.line_item
                    else "",
                }
                for plan in parent_qs
            }

            self.fields["parent"].queryset = parent_qs
            self.fields["parent"].widget.choice_data = choice_data

        self.fields["structure"].required = False
        self.fields["bill"].required = False
        self.fields["package"].required = False
        self.fields["line_item"].required = False
        self.fields["activity"].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data:
            return cleaned_data

        start_date = cleaned_data.get("start_date")
        finish_date = cleaned_data.get("finish_date")
        line_item = cleaned_data.get("line_item")
        activity = cleaned_data.get("activity")
        parent = cleaned_data.get("parent")
        unit_obj = cleaned_data.get("unit")

        # Convert unit object to its short_name string for the database
        if unit_obj:
            from app.Project.models.unit_models import UnitOfMeasure

            if isinstance(unit_obj, UnitOfMeasure):
                cleaned_data["unit"] = unit_obj.short_name

        # Inherit hierarchy from parent
        if parent:
            cleaned_data["structure"] = parent.structure
            if parent.bill:
                cleaned_data["bill"] = parent.bill
            if parent.package:
                cleaned_data["package"] = parent.package

        # Validate structure presence
        if not cleaned_data.get("structure") and not parent:
            raise ValidationError(
                {"structure": "Structure is required for top-level plans."}
            )

        # Auto-populate activity from the NEWLY selected field
        # Auto-populate activity from the MOST SPECIFIC field provided in the form
        # We check fields in reverse order of hierarchy
        if cleaned_data.get("line_item"):
            cleaned_data["activity"] = str(cleaned_data["line_item"].description[:255])
        elif cleaned_data.get("package"):
            cleaned_data["activity"] = str(cleaned_data["package"])
        elif cleaned_data.get("bill"):
            cleaned_data["activity"] = str(cleaned_data["bill"])
        elif cleaned_data.get("structure"):
            cleaned_data["activity"] = str(cleaned_data["structure"])

        activity = cleaned_data.get("activity")
        # Use stored project_id or instance project
        project = self.project_id or (
            self.instance.project if self.instance.pk else None
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
                error_msg = f"An active plan for '{activity}' already exists within this date range ({start_date} to {finish_date})."
                if parent and parent.activity == activity:
                    error_msg = f"This sub-activity cannot have the same name as its parent ('{activity}'). Please select a more specific level (like a Package or Line Item) or adjust the selection."
                raise ValidationError(error_msg)

        # Enforce rule: Cannot change structure/parent if it has children
        if (
            self.instance.pk
            and hasattr(self.instance, "children")
            and self.instance.children.filter(deleted=False).exists()
        ):
            old_instance = ProductionPlan.objects.get(pk=self.instance.pk)
            new_parent = cleaned_data.get("parent")
            new_structure = cleaned_data.get("structure")
            new_bill = cleaned_data.get("bill")
            new_package = cleaned_data.get("package")

            if (
                old_instance.parent != new_parent
                or old_instance.structure != new_structure
                or old_instance.bill != new_bill
                or old_instance.package != new_package
            ):
                raise ValidationError(
                    "Cannot change WBS structure or parent activity because it has dependent children."
                )

        if (
            cleaned_data.get("parent")
            and cleaned_data.get("parent").pk == self.instance.pk
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
            production_plan_field: forms.ModelChoiceField = self.fields[
                "production_plan"
            ]  # type: ignore
            production_plan_field.queryset = ProductionPlan.objects.filter(
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
            resource_field: forms.ModelChoiceField = self.fields["resource"]  # type: ignore
            resource_field.queryset = ProductionResource.objects.filter(
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
            resource_field: forms.ModelChoiceField = self.fields["resource"]  # type: ignore
            resource_field.queryset = ProductionResource.objects.filter(
                production_plan_id=activity_id, resource_type="PLANT"
            )
            activity_field: forms.ModelChoiceField = self.fields["activity"]  # type: ignore
            activity_field.queryset = ProductionPlan.objects.filter(id=activity_id)

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
        if self.project_id and plan.project_id != self.project_id:
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
        self.project_id: int | None = kwargs.pop("project_id", None)
        super().__init__(*args, **kwargs)
        if self.project_id:
            activity_field: forms.ModelChoiceField = self.fields["activity"]  # type: ignore
            activity_field.queryset = ProductionPlan.objects.filter(
                project_id=self.project_id
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
            predecessor_field.queryset = qs


PlanDependencyFormSet = inlineformset_factory(
    ProductionPlan,
    PlanDependency,
    fk_name="successor",
    form=PlanDependencyForm,
    formset=BasePlanDependencyFormSet,
    extra=1,
    can_delete=True,
)
