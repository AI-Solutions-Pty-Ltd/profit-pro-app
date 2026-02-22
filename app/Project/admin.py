"""Admin configuration for Project app."""

from django.contrib import admin

from app.core.Utilities.admin import SoftDeleteAdmin

from .models import (
    AdministrativeCompliance,
    AdministrativeComplianceDialog,
    AdministrativeComplianceDialogFile,
    Company,
    ContractualCompliance,
    ContractualComplianceDialog,
    ContractualComplianceDialogFile,
    FinalAccountCompliance,
    FinalAccountComplianceDialog,
    FinalAccountComplianceDialogFile,
    PlannedValue,
    Portfolio,
    Project,
    ProjectCategory,
    ProjectDocument,
    ProjectRole,
    Signatories,
)


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(SoftDeleteAdmin):
    list_display = ["name", "description", "deleted", "created_at"]
    list_filter = ["deleted", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Project)
class ProjectAdmin(SoftDeleteAdmin):
    list_display = ["name", "client", "status", "category", "deleted", "created_at"]
    list_filter = ["deleted", "created_at", "vat", "category", "status"]
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
    list_display = ["name", "deleted", "created_at"]
    list_filter = ["deleted", "created_at"]
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
