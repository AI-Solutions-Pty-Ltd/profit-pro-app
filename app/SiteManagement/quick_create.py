from app.core.dynamic_quick_create import registry
from app.SiteManagement.forms.resource_forms import PlantTypeForm, SkillTypeForm
from app.SiteManagement.models.plant_type import PlantType
from app.SiteManagement.models.skill_type import SkillType

# Register Skill Type
registry.register(
    resource_type="skill_type",
    model=SkillType,
    form_class=SkillTypeForm,
    title="New Skill Type",
    needs_project=True,
)

# Register Plant Type
registry.register(
    resource_type="plant_type",
    model=PlantType,
    form_class=PlantTypeForm,
    title="New Plant Type",
    needs_project=True,
)
