from app.core.dynamic_quick_create import registry
from app.Project.forms.unit_forms import UnitOfMeasureForm
from app.Project.models.unit_models import UnitOfMeasure

# Register Unit of Measure
registry.register(
    resource_type="unit_of_measure",
    model=UnitOfMeasure,
    form_class=UnitOfMeasureForm,
    title="New Unit of Measure",
    needs_project=False,
)
