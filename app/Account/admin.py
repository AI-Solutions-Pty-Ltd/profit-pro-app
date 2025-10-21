from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from app.core.Utilities.admin import SoftDeleteImportExportAdmin

from .models import Account, Suburb, Town


@admin.register(Account)
class AccountAdmin(SoftDeleteImportExportAdmin, BaseUserAdmin):
    """Custom admin for Account model that combines soft delete, import/export, and user admin features."""

    # Override UserAdmin's fieldsets with our custom ones
    fieldsets = (
        (None, {
            "fields": ("email", "password")
        }),
        ("Personal Information", {
            "fields": ("first_name", "last_name", "primary_contact", "alternative_contact", "type")
        }),
        ("Permissions", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            "classes": ("collapse",),
        }),
        ("Important Dates", {
            "fields": ("last_login", "date_joined", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
        ("Status", {
            "fields": ("deleted",),
        }),
    )

    # Fields to use when creating a new user
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "primary_contact", "password1", "password2"),
        }),
    )

    list_display = ["email", "first_name", "last_name", "type", "is_staff", "deleted", "created_at"]
    list_filter = ["deleted", "created_at", "is_staff", "is_superuser", "type", "groups"]
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    # Use horizontal filter for better UX with groups and permissions
    filter_horizontal = ("groups", "user_permissions")

    # Tell UserAdmin to use email as the username field
    readonly_fields = ["created_at", "updated_at", "last_login", "date_joined"]


@admin.register(Suburb)
class SuburbAdmin(SoftDeleteImportExportAdmin):
    list_display = ["suburb", "postcode", "deleted", "created_at"]
    list_filter = ["deleted", "created_at"]
    search_fields = ["suburb", "postcode"]


@admin.register(Town)
class TownAdmin(SoftDeleteImportExportAdmin):
    list_display = ["town", "deleted", "created_at"]
    list_filter = ["deleted", "created_at"]
    search_fields = ["town"]
