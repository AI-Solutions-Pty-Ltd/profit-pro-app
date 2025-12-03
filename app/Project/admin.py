"""Admin configuration for Project app."""

from django.contrib import admin

from app.core.Utilities.admin import SoftDeleteAdmin

from .models import Client, PlannedValue, Portfolio, Project, Signatories


@admin.register(Project)
class ProjectAdmin(SoftDeleteAdmin):
    list_display = ["name", "account", "status", "deleted", "created_at"]
    list_filter = ["deleted", "created_at", "vat"]
    search_fields = ["name", "description", "account__email"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Client)
class ClientAdmin(SoftDeleteAdmin):
    list_display = ["name", "user", "consultant", "deleted", "created_at"]
    list_filter = ["deleted", "created_at"]
    search_fields = ["name", "description", "user__email"]
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
