from django.contrib import admin

from .models import (
    BOQItem,
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

# ── System Library Admin ──────────────────────────────────────────


@admin.register(SystemTradeCode)
class SystemTradeCodeAdmin(admin.ModelAdmin):
    list_display = ["prefix", "trade_name", "trade_code"]


@admin.register(SystemMaterial)
class SystemMaterialAdmin(admin.ModelAdmin):
    list_display = [
        "material_code",
        "trade_name",
        "material_variety",
        "market_spec",
        "market_rate",
        "unit",
    ]
    search_fields = ["material_code", "material_variety"]


class SystemSpecificationComponentInline(admin.TabularInline):
    model = SystemSpecificationComponent
    extra = 1


@admin.register(SystemSpecification)
class SystemSpecificationAdmin(admin.ModelAdmin):
    list_display = ["section", "name", "unit_label", "rate_per_unit", "boq_quantity"]
    list_filter = ["section"]
    inlines = [SystemSpecificationComponentInline]


@admin.register(SystemLabourCrew)
class SystemLabourCrewAdmin(admin.ModelAdmin):
    list_display = [
        "crew_type",
        "crew_size",
        "skilled",
        "semi_skilled",
        "general",
        "daily_production",
        "crew_daily_cost",
    ]


@admin.register(SystemLabourSpecification)
class SystemLabourSpecificationAdmin(admin.ModelAdmin):
    list_display = [
        "section",
        "name",
        "unit",
        "crew",
        "daily_production",
        "rate_per_unit",
    ]
    list_filter = ["section"]


@admin.register(SystemPlantCost)
class SystemPlantCostAdmin(admin.ModelAdmin):
    list_display = ["name", "hourly_production", "hourly_rate"]


@admin.register(SystemPlantSpecification)
class SystemPlantSpecificationAdmin(admin.ModelAdmin):
    list_display = ["section", "name", "unit", "plant_type", "daily_production"]
    list_filter = ["section"]


@admin.register(SystemPreliminaryCost)
class SystemPreliminaryCostAdmin(admin.ModelAdmin):
    list_display = [
        "preliminary_type",
        "name",
        "sum_value",
        "amount",
        "number_per_month",
        "monthly_rate",
        "months",
        "computed_amount",
    ]
    list_filter = ["preliminary_type"]


@admin.register(SystemPreliminarySpecification)
class SystemPreliminarySpecificationAdmin(admin.ModelAdmin):
    list_display = ["section", "name", "unit", "amount"]
    list_filter = ["section"]


# ── Project-Scoped Admin ─────────────────────────────────────────


@admin.register(ProjectTradeCode)
class ProjectTradeCodeAdmin(admin.ModelAdmin):
    list_display = ["project", "prefix", "trade_name", "trade_code"]
    list_filter = ["project"]


@admin.register(ProjectMaterial)
class ProjectMaterialAdmin(admin.ModelAdmin):
    list_display = ["project", "material_code", "trade_name", "market_rate", "unit"]
    list_filter = ["project"]
    search_fields = ["material_code", "material_variety"]


class ProjectSpecificationComponentInline(admin.TabularInline):
    model = ProjectSpecificationComponent
    extra = 1


@admin.register(ProjectSpecification)
class ProjectSpecificationAdmin(admin.ModelAdmin):
    list_display = ["project", "section", "name", "unit_label", "rate_per_unit"]
    list_filter = ["project", "section"]
    inlines = [ProjectSpecificationComponentInline]


@admin.register(ProjectLabourCrew)
class ProjectLabourCrewAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "crew_type",
        "crew_size",
        "skilled",
        "semi_skilled",
        "general",
        "crew_daily_cost",
    ]
    list_filter = ["project"]


@admin.register(ProjectLabourSpecification)
class ProjectLabourSpecificationAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "section",
        "name",
        "unit",
        "crew",
        "daily_production",
        "rate_per_unit",
    ]
    list_filter = ["project", "section"]


@admin.register(ProjectPlantCost)
class ProjectPlantCostAdmin(admin.ModelAdmin):
    list_display = ["project", "name", "hourly_production", "hourly_rate"]
    list_filter = ["project"]


@admin.register(ProjectPlantSpecification)
class ProjectPlantSpecificationAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "section",
        "name",
        "unit",
        "plant_type",
        "daily_production",
    ]
    list_filter = ["project", "section"]


@admin.register(ProjectPreliminaryCost)
class ProjectPreliminaryCostAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "preliminary_type",
        "name",
        "amount",
        "computed_amount",
    ]
    list_filter = ["project", "preliminary_type"]


@admin.register(ProjectPreliminarySpecification)
class ProjectPreliminarySpecificationAdmin(admin.ModelAdmin):
    list_display = ["project", "section", "name", "unit", "amount"]
    list_filter = ["project", "section"]


@admin.register(BOQItem)
class BOQItemAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "section",
        "bill_no",
        "description",
        "unit",
        "contract_quantity",
        "contract_rate",
        "contract_amount",
        "new_materials_rate",
        "new_labour_rate",
        "baseline_new_price",
    ]
    list_filter = ["project", "section", "is_section_header"]
