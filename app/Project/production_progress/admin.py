from django.contrib import admin

from app.core.Utilities.admin import SoftDeleteAdmin

from .production_models import ProductionPlan, ProductionResource


@admin.register(ProductionPlan)
class ProductionPlanAdmin(SoftDeleteAdmin):
    list_display = [
        "project",
        "activity",
        "start_date",
        "finish_date",
        "quantity",
        "unit",
        "deleted",
        "created_at",
    ]
    list_filter = ["deleted", "created_at", "project"]
    search_fields = ["activity", "project__name"]
    readonly_fields = ["created_at", "updated_at", "duration"]


@admin.register(ProductionResource)
class ProductionResourceAdmin(SoftDeleteAdmin):
    list_display = [
        "production_plan",
        "resource_type",
        "skill_type",
        "plant_type",
        "name",
        "number",
        "days",
        "rate",
        "total_cost",
    ]
    list_filter = ["resource_type", "production_plan__project", "production_plan"]
    search_fields = ["name", "production_plan__activity"]
    readonly_fields = ["created_at", "updated_at", "name", "rate", "total_cost"]
