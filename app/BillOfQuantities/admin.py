from django.contrib import admin

from app.core.Utilities.admin import SoftDeleteAdmin

from .models import (
    ActualTransaction,
    Bill,
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
    list_display = ["name", "structure", "deleted", "created_at"]
    list_filter = ["deleted", "created_at"]
    search_fields = ["name", "structure__name"]


@admin.register(Package)
class PackageAdmin(SoftDeleteAdmin):
    list_display = ["name", "bill", "deleted", "created_at"]
    list_filter = ["deleted", "created_at"]
    search_fields = ["name", "bill__name"]


@admin.register(LineItem)
class LineItemAdmin(SoftDeleteAdmin):
    list_display = ["item_number", "description", "project", "deleted", "created_at"]
    list_filter = ["deleted", "created_at", "is_work", "project"]
    search_fields = ["item_number", "description", "project__name"]


@admin.register(PaymentCertificate)
class PaymentCertificateAdmin(SoftDeleteAdmin):
    list_display = ["certificate_number", "project", "status", "deleted", "created_at"]
    list_filter = ["deleted", "status", "created_at", "project"]
    search_fields = ["certificate_number", "project__name"]


@admin.register(ActualTransaction)
class ActualTransactionAdmin(SoftDeleteAdmin):
    list_display = [
        "line_item",
        "payment_certificate",
        "quantity",
        "approved",
        "deleted",
        "created_at",
    ]
    list_filter = ["deleted", "approved", "claimed", "created_at"]
    search_fields = [
        "line_item__description",
        "payment_certificate__certificate_number",
    ]
