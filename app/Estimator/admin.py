from django.contrib import admin

from .models import (
    BOQItem,
    ContractorItemLibraryEntry,
    ProjectItemLibraryEntry,
    ProjectLabourCrew,
    ProjectLabourSpecification,
    ProjectMaterial,
    ProjectPlantCost,
    ProjectPlantSpecification,
    ProjectPlantSpecificationComponent,
    ProjectPreliminaryCost,
    ProjectPreliminarySpecification,
    ProjectSpecification,
    ProjectSpecificationComponent,
    ProjectTradeCode,
    SystemItemLibraryEntry,
    SystemLabourCrew,
    SystemLabourSpecification,
    SystemMaterial,
    SystemPlantCost,
    SystemPlantSpecification,
    SystemPlantSpecificationComponent,
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


class SystemPlantSpecificationComponentInline(admin.TabularInline):
    model = SystemPlantSpecificationComponent
    extra = 1


@admin.register(SystemPlantSpecification)
class SystemPlantSpecificationAdmin(admin.ModelAdmin):
    list_display = ["section", "name", "unit", "daily_production", "rate_per_unit"]
    list_filter = ["section"]
    inlines = [SystemPlantSpecificationComponentInline]


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
    list_display = ["section", "name", "unit", "preliminary_type", "amount"]
    list_filter = ["section", "preliminary_type"]


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


class ProjectPlantSpecificationComponentInline(admin.TabularInline):
    model = ProjectPlantSpecificationComponent
    extra = 1


@admin.register(ProjectPlantSpecification)
class ProjectPlantSpecificationAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "section",
        "name",
        "unit",
        "daily_production",
        "rate_per_unit",
    ]
    list_filter = ["project", "section"]
    inlines = [ProjectPlantSpecificationComponentInline]


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
    list_display = ["project", "section", "name", "unit", "preliminary_type", "amount"]
    list_filter = ["project", "section", "preliminary_type"]


@admin.register(SystemItemLibraryEntry)
class SystemItemLibraryEntryAdmin(admin.ModelAdmin):
    list_display = ["item_code", "trade_code", "component", "description", "unit"]
    list_filter = ["trade_code"]
    search_fields = ["item_code", "description", "component", "accounts_code"]
    raw_id_fields = [
        "trade_code",
        "material_spec",
        "labour_spec",
        "plant_spec",
        "preliminary_spec",
    ]


@admin.register(ContractorItemLibraryEntry)
class ContractorItemLibraryEntryAdmin(admin.ModelAdmin):
    list_display = [
        "company",
        "item_code",
        "trade_code",
        "component",
        "description",
        "unit",
    ]
    list_filter = ["company", "trade_code"]
    search_fields = ["item_code", "description", "component", "accounts_code"]
    raw_id_fields = [
        "trade_code",
        "material_spec",
        "labour_spec",
        "plant_spec",
        "preliminary_spec",
        "source",
    ]


@admin.register(ProjectItemLibraryEntry)
class ProjectItemLibraryEntryAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "item_code",
        "trade_code",
        "component",
        "description",
        "unit",
    ]
    list_filter = ["project", "trade_code"]
    search_fields = ["item_code", "description", "component", "accounts_code"]
    raw_id_fields = [
        "trade_code",
        "material_spec",
        "labour_spec",
        "plant_spec",
        "preliminary_spec",
        "source_system",
        "source_contractor",
    ]


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
