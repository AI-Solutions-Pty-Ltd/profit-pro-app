"""Admin configuration for Project app."""

from django.contrib import admin

from app.core.Utilities.admin import SoftDeleteAdmin

from .models import (
    AdministrativeCompliance,
    AdministrativeComplianceDialog,
    AdministrativeComplianceDialogFile,
    Category,
    Company,
    ContractualCompliance,
    ContractualComplianceDialog,
    ContractualComplianceDialogFile,
    Discipline,
    Drawing,
    DrawingType,
    FinalAccountCompliance,
    FinalAccountComplianceDialog,
    FinalAccountComplianceDialogFile,
    Group,
    PlannedValue,
    Portfolio,
    ProductionPlan,
    ProductionResource,
    Project,
    ProjectCategory,
    ProjectCompanyUserRole,
    ProjectDiscipline,
    ProjectDocument,
    ProjectGroup,
    ProjectRole,
    ProjectStage,
    ProjectSubCategory,
    Signatories,
    SubCategory,
)


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(SoftDeleteAdmin):
    list_display = ["name", "description", "deleted", "created_at"]
    list_filter = ["deleted", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ProjectSubCategory)
class ProjectSubCategoryAdmin(SoftDeleteAdmin):
    list_display = ["name", "description", "deleted", "created_at"]
    list_filter = ["deleted", "created_at"]
    search_fields = ["name", "description", "category__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ProjectDiscipline)
class ProjectDisciplineAdmin(SoftDeleteAdmin):
    list_display = ["name", "description", "deleted", "created_at"]
    list_filter = [
        "deleted",
        "created_at",
    ]
    search_fields = [
        "name",
        "description",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ProjectStage)
class ProjectStageAdmin(SoftDeleteAdmin):
    list_display = ["name", "description", "deleted", "created_at"]
    list_filter = [
        "deleted",
        "created_at",
    ]
    search_fields = [
        "name",
        "description",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Project)
class ProjectAdmin(SoftDeleteAdmin):
    list_display = [
        "name",
        "is_demo",
        "client",
        "status",
        "project_category",
        "deleted",
        "created_at",
    ]
    list_filter = [
        "is_demo",
        "deleted",
        "created_at",
        "vat",
        "project_category",
        "status",
    ]
    search_fields = ["name", "description", "account__email"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ProjectRole)
class ProjectRoleAdmin(SoftDeleteAdmin):
    list_display = ["project", "role", "user", "deleted", "created_at"]
    list_filter = ["deleted", "created_at", "role", "project", "user"]
    search_fields = [
        "project__name",
        "role",
        "user__email",
        "user__first_name",
        "user__last_name",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Company)
class CompanyAdmin(SoftDeleteAdmin):
    list_display = ["name", "type", "vat_registered", "deleted", "created_at"]
    list_filter = [
        "deleted",
        "created_at",
        "type",
    ]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Signatories)
class SignatoriesAdmin(SoftDeleteAdmin):
    list_display = ["user", "sequence_number", "project", "deleted", "created_at"]
    list_filter = ["deleted", "created_at", "project"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "project__name",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ProjectDocument)
class ProjectDocumentAdmin(SoftDeleteAdmin):
    list_display = [
        "title",
        "project",
        "category",
        "uploaded_by",
        "deleted",
        "created_at",
    ]
    list_filter = ["deleted", "created_at", "category", "project"]
    search_fields = ["title", "notes", "project__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Drawing)
class DrawingAdmin(SoftDeleteAdmin):
    list_display = [
        "drawing_number",
        "name",
        "revision_number",
        "project",
        "discipline",
        "deleted",
        "created_at",
    ]
    list_filter = [
        "deleted",
        "created_at",
        "project",
        "discipline",
        "category",
        "sub_category",
        "group",
    ]
    search_fields = ["drawing_number", "name", "project__name", "notes"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = [
        "project",
        "discipline",
        "category",
        "sub_category",
        "group",
    ]


@admin.register(Portfolio)
class PortfolioAdmin(SoftDeleteAdmin):
    list_display = ["pk", "deleted", "created_at", "updated_at"]
    list_filter = ["deleted", "created_at", "projects", "users"]
    search_fields = ["users__email", "project__name", "project__description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(PlannedValue)
class PlannedValueAdmin(SoftDeleteAdmin):
    list_display = ["pk", "project", "period", "value"]
    list_filter = ["deleted", "created_at", "project"]
    search_fields = ["project__name", "project__description"]
    readonly_fields = ["created_at", "updated_at"]


# ============================================================================
# Compliance Models Admin
# ============================================================================


@admin.register(ContractualCompliance)
class ContractualComplianceAdmin(SoftDeleteAdmin):
    list_display = [
        "project",
        "status",
        "due_date",
        "deleted",
        "created_at",
    ]
    list_filter = ["deleted", "created_at", "status", "project"]
    search_fields = ["project__name", "description", "notes"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ContractualComplianceDialog)
class ContractualComplianceDialogAdmin(SoftDeleteAdmin):
    list_display = ["compliance", "sender", "receiver", "created_at"]
    list_filter = ["compliance", "created_at"]
    search_fields = ["message", "sender__email", "receiver__email"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]


@admin.register(ContractualComplianceDialogFile)
class ContractualComplianceFileAdmin(SoftDeleteAdmin):
    list_display = ["dialog", "file", "created_at"]
    list_filter = ["dialog", "created_at"]
    search_fields = ["file"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]


@admin.register(AdministrativeCompliance)
class AdministrativeComplianceAdmin(SoftDeleteAdmin):
    list_display = [
        "project",
        "status",
        "submission_due_date",
        "deleted",
        "created_at",
    ]
    list_filter = ["deleted", "created_at", "status", "project"]
    search_fields = ["project__name", "description", "notes"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(AdministrativeComplianceDialog)
class AdministrativeComplianceDialogAdmin(SoftDeleteAdmin):
    list_display = ["compliance", "sender", "receiver", "created_at"]
    list_filter = ["compliance", "created_at"]
    search_fields = ["message", "sender__email", "receiver__email"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]


@admin.register(AdministrativeComplianceDialogFile)
class AdministrativeComplianceDialogFileAdmin(SoftDeleteAdmin):
    list_display = ["dialog", "file", "created_at"]
    list_filter = ["dialog", "created_at"]
    search_fields = ["file"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]


@admin.register(FinalAccountCompliance)
class FinalAccountComplianceAdmin(SoftDeleteAdmin):
    list_display = [
        "project",
        "status",
        "submission_date",
        "deleted",
        "created_at",
    ]
    list_filter = ["deleted", "created_at", "status", "project"]
    search_fields = ["project__name", "description", "notes"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(FinalAccountComplianceDialog)
class FinalAccountComplianceDialogAdmin(SoftDeleteAdmin):
    list_display = ["compliance", "sender", "receiver", "created_at"]
    list_filter = ["compliance", "created_at"]
    search_fields = ["message", "sender__email", "receiver__email"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]


@admin.register(FinalAccountComplianceDialogFile)
class FinalAccountComplianceDialogFileAdmin(SoftDeleteAdmin):
    list_display = ["dialog", "file", "created_at"]
    list_filter = ["dialog", "created_at"]
    search_fields = ["file"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]


@admin.register(Category)
class CategoryAdmin(SoftDeleteAdmin):
    list_display = ["name", "description", "deleted", "created_at"]
    list_filter = [
        "deleted",
        "created_at",
    ]
    search_fields = [
        "name",
        "description",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(SubCategory)
class SubCategoryAdmin(SoftDeleteAdmin):
    list_display = [
        "name",
        "description",
        "deleted",
        "created_at",
        "get_category_name",
    ]
    list_filter = [
        "category",
        "deleted",
        "created_at",
    ]
    search_fields = [
        "category__name",
        "name",
        "description",
    ]
    readonly_fields = ["created_at", "updated_at"]

    @admin.display(description="Category", ordering="category__name")
    def get_category_name(self, obj):
        """Display the category name."""
        return obj.category.name if obj.category else "-"


@admin.register(Group)
class GroupAdmin(SoftDeleteAdmin):
    list_display = [
        "name",
        "description",
        "deleted",
        "created_at",
        "get_sub_category_name",
    ]
    list_filter = [
        "sub_category",
        "deleted",
        "created_at",
    ]
    search_fields = [
        "sub_category__name",
        "name",
        "description",
    ]
    readonly_fields = ["created_at", "updated_at"]

    @admin.display(description="Sub Category", ordering="sub_category__name")
    def get_sub_category_name(self, obj):
        """Display the sub category name."""
        return obj.sub_category.name if obj.sub_category else "-"


@admin.register(Discipline)
class DisciplineAdmin(SoftDeleteAdmin):
    list_display = ["name", "description", "deleted", "created_at"]
    list_filter = [
        "deleted",
        "created_at",
    ]
    search_fields = [
        "name",
        "description",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(DrawingType)
class DrawingTypeAdmin(SoftDeleteAdmin):
    """Admin for DrawingType model."""

    list_display = ["name", "project", "description", "deleted", "created_at"]
    list_filter = ["project", "deleted", "created_at"]
    search_fields = ["name", "project__name", "description"]
    readonly_fields = ["created_at", "updated_at"]


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


@admin.register(ProjectCompanyUserRole)
class ProjectCompanyUserRoleAdmin(SoftDeleteAdmin):
    list_display = ["project", "company", "user", "role", "deleted", "created_at"]
    list_filter = ["deleted", "created_at", "project", "company", "role"]
    search_fields = ["project__name", "company__name", "user__email", "role"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ProjectGroup)
class ProjectGroupAdmin(SoftDeleteAdmin):
    list_display = ["name", "user", "deleted", "created_at"]
    list_filter = ["deleted", "created_at", "user"]
    search_fields = ["name", "user__email"]
    readonly_fields = ["created_at", "updated_at"]

