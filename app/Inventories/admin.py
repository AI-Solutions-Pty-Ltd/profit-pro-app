from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import (
    VAT,
    Inventory,
    InventoryTransaction,
    Note,
    Order,
    OrderComposition,
    Type,
    Warehouse,
)
from .models_suppliers import Supplier


@admin.register(Supplier)
class SupplierAdmin(ImportExportModelAdmin):
    list_display = ("description", "primary_contact")
    search_fields = ("description", "company_registration", "email")
    ordering = ("description",)


@admin.register(Inventory)
class InventoryAdmin(ImportExportModelAdmin):
    list_display = ("description",)
    search_fields = ("description",)
    ordering = ("description",)
    autocomplete_fields = ("type",)


@admin.register(Type)
class TypeAdmin(ImportExportModelAdmin):
    list_display = ("description",)
    search_fields = ("description",)
    ordering = ("description",)


@admin.register(Warehouse)
class WarehouseAdmin(ImportExportModelAdmin):
    list_display = ("description",)
    search_fields = ("description",)
    ordering = ("description",)


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    list_display = ("supplier", "date")
    search_fields = ("supplier__description", "date")
    ordering = ("-date",)
    autocomplete_fields = ("supplier",)


@admin.register(OrderComposition)
class OrderCompositionAdmin(ImportExportModelAdmin):
    list_display = ("inventory", "qty_ordered")
    search_fields = ("inventory__description",)
    ordering = ("inventory",)
    autocomplete_fields = ("inventory", "warehouse", "vat")


@admin.register(Note)
class NoteAdmin(ImportExportModelAdmin):
    list_display = ("description",)
    search_fields = ("description",)
    ordering = ("description",)


@admin.register(VAT)
class VATAdmin(ImportExportModelAdmin):
    list_display = ("description",)
    search_fields = ("description",)
    ordering = ("description",)


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(ImportExportModelAdmin):
    list_display = ("inventory", "qty", "date")
    search_fields = ("inventory__description", "date")
    ordering = ("-date",)
    autocomplete_fields = ("inventory", "warehouse")
