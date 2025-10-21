"""Base admin classes for models with soft delete support."""

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin


class SoftDeleteAdmin(admin.ModelAdmin):
    """Base admin class that shows all objects including soft-deleted ones.

    This admin class overrides get_queryset to use the all_objects manager,
    which includes soft-deleted items. This prevents 404 errors when viewing
    soft-deleted objects in the admin interface.

    Usage:
        @admin.register(MyModel)
        class MyModelAdmin(SoftDeleteAdmin):
            list_display = ["name", "deleted", "created_at"]
    """

    def get_queryset(self, request):
        """Use all_objects manager to include soft-deleted items."""
        qs = self.model.all_objects.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    list_display = ["__str__", "deleted", "created_at", "updated_at"]
    list_filter = ["deleted", "created_at"]
    readonly_fields = ["created_at", "updated_at"]


class SoftDeleteImportExportAdmin(SoftDeleteAdmin, ImportExportModelAdmin):
    """Admin class that combines soft delete support with import/export functionality."""

    pass
