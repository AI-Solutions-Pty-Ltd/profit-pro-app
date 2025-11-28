from django.contrib import admin

from app.core.Utilities.admin import SoftDeleteAdmin

from .models import (
    ActualTransaction,
    Bill,
    Forecast,
    ForecastTransaction,
    LineItem,
    Package,
    PaymentCertificate,
    Structure,
)


@admin.register(Structure)
class StructureAdmin(SoftDeleteAdmin):
    list_display = ["name", "project", "deleted", "created_at"]
    list_filter = ["deleted", "created_at", "project"]
    search_fields = ["name", "project__name"]


@admin.register(Bill)
class BillAdmin(SoftDeleteAdmin):
    list_display = [
        "structure__project__name",
        "name",
        "structure",
        "deleted",
        "created_at",
    ]
    list_filter = ["deleted", "created_at", "structure__project"]
    search_fields = ["name", "structure__name"]


@admin.register(Package)
class PackageAdmin(SoftDeleteAdmin):
    list_display = ["name", "bill", "deleted", "created_at"]
    list_filter = ["deleted", "created_at"]
    search_fields = ["name", "bill__name"]


@admin.register(LineItem)
class LineItemAdmin(SoftDeleteAdmin):
    list_display = ["description", "item_number", "project", "deleted", "created_at"]
    list_filter = [
        "project__name",
        "deleted",
        "is_work",
        "addendum",
        "special_item",
        "created_at",
    ]
    search_fields = ["item_number", "description", "project__name"]


@admin.register(PaymentCertificate)
class PaymentCertificateAdmin(SoftDeleteAdmin):
    list_display = ["certificate_number", "project", "status", "deleted", "approved_on"]
    list_filter = ["deleted", "status", "created_at", "project"]
    search_fields = ["certificate_number", "project__name"]


@admin.register(ActualTransaction)
class ActualTransactionAdmin(SoftDeleteAdmin):
    list_display = [
        "payment_certificate",
        "get_line_item_description",
        "quantity",
        "total_price",
        "approved",
        "deleted",
    ]
    list_filter = [
        "payment_certificate__certificate_number",
        "deleted",
        "approved",
        "claimed",
        "line_item__special_item",
        "line_item__addendum",
    ]
    search_fields = [
        "line_item__description",
        "payment_certificate__certificate_number",
    ]
    autocomplete_fields = ["line_item"]

    @admin.display(description="Line Item", ordering="line_item__description")
    def get_line_item_description(self, obj):
        """Display the line item description."""
        return obj.line_item.description if obj.line_item else "-"


@admin.register(Forecast)
class ForecastAdmin(SoftDeleteAdmin):
    list_display = [
        "project",
        "status",
        "period",
        "total_forecast",
        "created_at",
        "deleted",
        "notes",
    ]
    list_filter = ["deleted", "project__name", "status", "created_at"]
    search_fields = ["project__name"]


@admin.register(ForecastTransaction)
class ForecastTransactionAdmin(SoftDeleteAdmin):
    list_display = [
        "forecast",
        "get_line_item_description",
        "quantity",
        "unit_price",
        "total_price",
        "deleted",
        "forecast__period",
        "notes",
    ]
    list_filter = [
        "forecast__project__name",
        "deleted",
        "forecast__status",
    ]
    search_fields = ["line_item__description", "forecast__project__name"]
    autocomplete_fields = ["forecast", "line_item"]

    @admin.display(description="Line Item", ordering="line_item__description")
    def get_line_item_description(self, obj):
        """Display the line item description."""
        return obj.line_item.description if obj.line_item else "-"
