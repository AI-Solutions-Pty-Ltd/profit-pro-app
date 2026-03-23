"""Admin configuration for Planning & Procurement models."""

from django.contrib import admin

from app.Planning.models import (
    DesignCategory,
    DesignCategoryFile,
    DesignDiscipline,
    DesignDisciplineFile,
    DesignGroup,
    DesignGroupFile,
    DesignSubCategory,
    DesignSubCategoryFile,
    TenderDocument,
    WorkPackage,
)


class TenderDocumentInline(admin.TabularInline):
    """Inline for TenderDocument within WorkPackage admin."""

    model = TenderDocument
    extra = 0


class DesignCategoryFileInline(admin.TabularInline):
    """Inline for DesignCategoryFile."""

    model = DesignCategoryFile
    extra = 0


class DesignSubCategoryFileInline(admin.TabularInline):
    """Inline for DesignSubCategoryFile."""

    model = DesignSubCategoryFile
    extra = 0


class DesignGroupFileInline(admin.TabularInline):
    """Inline for DesignGroupFile."""

    model = DesignGroupFile
    extra = 0


class DesignDisciplineFileInline(admin.TabularInline):
    """Inline for DesignDisciplineFile."""

    model = DesignDisciplineFile
    extra = 0


@admin.register(WorkPackage)
class WorkPackageAdmin(admin.ModelAdmin):
    """Admin for WorkPackage model."""

    list_display = [
        "name",
        "package_number",
        "project",
        "package_start_date",
        "package_finish_date",
        "package_budget",
    ]
    list_filter = [
        "package_start_date",
        "package_finish_date",
    ]
    search_fields = ["name", "package_number", "project__name"]
    inlines = [TenderDocumentInline]


@admin.register(TenderDocument)
class TenderDocumentAdmin(admin.ModelAdmin):
    """Admin for TenderDocument model."""

    list_display = [
        "name",
        "work_package",
        "percentage_completed",
        "planned_date",
        "actual_date",
    ]
    list_filter = ["name"]
    search_fields = ["name", "work_package__name"]


@admin.register(DesignCategory)
class DesignCategoryAdmin(admin.ModelAdmin):
    """Admin for DesignCategory model."""

    list_display = ["category", "work_package", "stage", "approved"]
    list_filter = ["stage", "approved"]
    inlines = [DesignCategoryFileInline]


@admin.register(DesignSubCategory)
class DesignSubCategoryAdmin(admin.ModelAdmin):
    """Admin for DesignSubCategory model."""

    list_display = ["sub_category", "work_package", "stage", "approved"]
    list_filter = ["stage", "approved"]
    inlines = [DesignSubCategoryFileInline]


@admin.register(DesignGroup)
class DesignGroupAdmin(admin.ModelAdmin):
    """Admin for DesignGroup model."""

    list_display = ["group", "work_package", "stage", "approved"]
    list_filter = ["stage", "approved"]
    inlines = [DesignGroupFileInline]


@admin.register(DesignDiscipline)
class DesignDisciplineAdmin(admin.ModelAdmin):
    """Admin for DesignDiscipline model."""

    list_display = ["discipline", "work_package", "stage", "approved"]
    list_filter = ["stage", "approved"]
    inlines = [DesignDisciplineFileInline]
