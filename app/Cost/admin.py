from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum

from app.Cost.models import ActualCost, Cost


@admin.register(Cost)
class CostAdmin(admin.ModelAdmin):
    """Admin configuration for Cost model."""

    list_display = [
        "description",
        "bill",
        "category",
        "quantity",
        "unit_price",
        "gross",
        "vat_display",
        "net",
        "date",
        "created_at",
    ]

    list_filter = [
        "category",
        "vat",
        "date",
        "bill__structure",
        "bill__structure__project",
        "created_at",
    ]

    search_fields = [
        "description",
        "bill__name",
        "bill__structure__name",
        "bill__structure__project__name",
    ]

    readonly_fields = [
        "vat_amount",
        "net",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        ("Basic Information", {"fields": ("bill", "date", "category", "description")}),
        ("Financial Details", {"fields": ("quantity", "unit_price", "gross", "vat")}),
        (
            "Calculated Fields",
            {
                "fields": ("vat_amount", "net"),
                "classes": ("collapse",),
                "description": "These fields are automatically calculated based on the values above.",
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    date_hierarchy = "date"

    ordering = ["-date", "-created_at"]

    list_per_page = 25

    def vat_display(self, obj):
        """Display VAT status with color coding."""
        if obj.vat:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ Yes (15%)</span>'
            )
        return format_html('<span style="color: #ef4444;">✗ No</span>')

    vat_display.short_description = "VAT"  # type: ignore
    vat_display.admin_order_field = "vat"  # type: ignore

    def get_queryset(self, request):
        """Optimize queries with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("bill", "bill__structure", "bill__structure__project")
        )

    def gross_currency(self, obj):
        """Format gross as currency."""
        return f"R {obj.gross:,.2f}"

    gross_currency.short_description = "Gross (R)"  # type: ignore
    gross_currency.admin_order_field = "gross"  # type: ignore

    def net_currency(self, obj):
        """Format net as currency."""
        return f"R {obj.net:,.2f}"

    net_currency.short_description = "Net (R)"  # type: ignore
    net_currency.admin_order_field = "net"  # type: ignore


@admin.register(ActualCost)
class ActualCostAdmin(admin.ModelAdmin):
    """Admin configuration for ActualCost model."""

    list_display = [
        "description",
        "cost_link",
        "bill",
        "category",
        "quantity",
        "unit_price",
        "gross",
        "vat_display",
        "net",
        "date",
        "created_at",
    ]

    list_filter = [
        "category",
        "vat",
        "date",
        "bill__structure",
        "bill__structure__project",
        "created_at",
    ]

    search_fields = [
        "description",
        "bill__name",
        "bill__structure__name",
        "bill__structure__project__name",
        "cost__description",
    ]

    readonly_fields = [
        "vat_amount",
        "net",
        "created_at",
        "updated_at",
    ]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("bill", "cost", "date", "category", "description")},
        ),
        ("Financial Details", {"fields": ("quantity", "unit_price", "gross", "vat")}),
        (
            "Calculated Fields",
            {
                "fields": ("vat_amount", "net"),
                "classes": ("collapse",),
                "description": "These fields are automatically calculated based on the values above.",
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    date_hierarchy = "date"

    ordering = ["-date", "-created_at"]

    list_per_page = 25

    def vat_display(self, obj):
        """Display VAT status with color coding."""
        if obj.vat:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ Yes (15%)</span>'
            )
        return format_html('<span style="color: #ef4444;">✗ No</span>')

    vat_display.short_description = "VAT"  # type: ignore
    vat_display.admin_order_field = "vat"  # type: ignore

    def cost_link(self, obj):
        """Display link to the planned cost."""
        if obj.cost:
            return format_html(
                '<a href="/admin/Cost/cost/{}/change/" style="color: #3b82f6;">{}</a>',
                obj.cost.pk,
                obj.cost.description,
            )
        return "-"

    cost_link.short_description = "Planned Cost"  # type: ignore
    cost_link.admin_order_field = "cost__description"  # type: ignore

    def get_queryset(self, request):
        """Optimize queries with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "cost", "bill", "bill__structure", "bill__structure__project"
            )
        )
