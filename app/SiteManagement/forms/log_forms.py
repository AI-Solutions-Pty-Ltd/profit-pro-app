from django import forms

from app.core.Utilities.widgets import SearchableSelectWidget
from app.Project.models.entity_definitions import (
    LabourEntity,
    MaterialEntity,
    OverheadEntity,
    PlantEntity,
    SubcontractorEntity,
)

from ..models import (
    LabourLog,
    MaterialsLog,
    OverheadDailyLog,
    PlantEquipment,
    SubcontractorLog,
)


class BaseLogForm(forms.ModelForm):
    """Base form for Site Management logs with project-filtered querysets."""

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self._filter_querysets(project)

    def _filter_querysets(self, project):
        """Filter all project-related querysets."""
        # This method should be overridden or extended by subclasses
        pass


class LabourLogForm(BaseLogForm):
    class Meta:
        model = LabourLog
        fields = ["labour_entity", "date", "hours_worked", "task_activity", "remarks"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "labour_entity": SearchableSelectWidget(
                create_url=True, resource_type="labour_entity"
            ),
        }

    def _filter_querysets(self, project):
        if "labour_entity" in self.fields:
            self.fields["labour_entity"].queryset = LabourEntity.objects.filter(
                project=project
            )


class MaterialsLogForm(BaseLogForm):
    class Meta:
        model = MaterialsLog
        fields = [
            "material_entity",
            "date_received",
            "invoice_number",
            "quantity",
            "intended_usage",
            "comments",
        ]
        widgets = {
            "date_received": forms.DateInput(attrs={"type": "date"}),
            "material_entity": SearchableSelectWidget(
                create_url=True, resource_type="material_entity"
            ),
        }

    def _filter_querysets(self, project):
        if "material_entity" in self.fields:
            self.fields["material_entity"].queryset = MaterialEntity.objects.filter(
                project=project
            )


class OverheadDailyLogForm(BaseLogForm):
    class Meta:
        model = OverheadDailyLog
        fields = ["overhead_entity", "date", "quantity", "remarks"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "overhead_entity": SearchableSelectWidget(
                create_url=True, resource_type="overhead_entity"
            ),
        }

    def _filter_querysets(self, project):
        if "overhead_entity" in self.fields:
            self.fields["overhead_entity"].queryset = OverheadEntity.objects.filter(
                project=project
            )


class PlantEquipmentLogForm(BaseLogForm):
    class Meta:
        model = PlantEquipment
        fields = [
            "plant_entity",
            "date",
            "usage_hours",
            "breakdown_status",
            "maintenance_done",
            "remarks",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "plant_entity": SearchableSelectWidget(
                create_url=True, resource_type="plant_entity"
            ),
            "breakdown_status": SearchableSelectWidget(),
        }

    def _filter_querysets(self, project):
        if "plant_entity" in self.fields:
            self.fields["plant_entity"].queryset = PlantEntity.objects.filter(
                project=project
            )


class SubcontractorLogForm(BaseLogForm):
    class Meta:
        model = SubcontractorLog
        fields = [
            "subcontractor_entity",
            "date",
            "task",
            "hours_worked",
            "output",
            "output_unit",
            "remarks",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "subcontractor_entity": SearchableSelectWidget(
                create_url=True, resource_type="subcontractor_entity"
            ),
        }

    def _filter_querysets(self, project):
        if "subcontractor_entity" in self.fields:
            self.fields[
                "subcontractor_entity"
            ].queryset = SubcontractorEntity.objects.filter(project=project)
