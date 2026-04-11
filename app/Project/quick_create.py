from app.core.dynamic_quick_create import registry
from app.Project.forms.entity_forms import (
    LabourEntityForm,
    MaterialEntityForm,
    OverheadEntityForm,
    PlantEntityForm,
    SubcontractorEntityForm,
)
from app.Project.forms.unit_forms import UnitOfMeasureForm
from app.Project.models.entity_definitions import (
    LabourEntity,
    MaterialEntity,
    OverheadEntity,
    PlantEntity,
    SubcontractorEntity,
)
from app.Project.models.unit_models import UnitOfMeasure

# Register Unit of Measure
registry.register(
    resource_type="unit_of_measure",
    model=UnitOfMeasure,
    form_class=UnitOfMeasureForm,
    title="New Unit of Measure",
    needs_project=False,
)

# Register Project Entities
registry.register(
    resource_type="labour_entity",
    model=LabourEntity,
    form_class=LabourEntityForm,
    title="New Labour Definition",
    needs_project=True,
)

registry.register(
    resource_type="material_entity",
    model=MaterialEntity,
    form_class=MaterialEntityForm,
    title="New Material Definition",
    needs_project=True,
)

registry.register(
    resource_type="overhead_entity",
    model=OverheadEntity,
    form_class=OverheadEntityForm,
    title="New Overhead Definition",
    needs_project=True,
)

registry.register(
    resource_type="plant_entity",
    model=PlantEntity,
    form_class=PlantEntityForm,
    title="New Plant Definition",
    needs_project=True,
)

registry.register(
    resource_type="subcontractor_entity",
    model=SubcontractorEntity,
    form_class=SubcontractorEntityForm,
    title="New Subcontractor Definition",
    needs_project=True,
)
