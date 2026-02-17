"""Admin configuration for Ledger models."""

from django.contrib import admin

from app.Ledger.models import Ledger, Transaction, Vat


@admin.register(Vat)
class VatAdmin(admin.ModelAdmin):
    """Admin configuration for VAT model."""

    list_display = ["name", "rate", "start_date", "end_date"]
    list_filter = ["rate", "start_date", "end_date"]
    search_fields = ["name"]
    ordering = ["-start_date", "name"]


@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):
    """Admin configuration for Ledger model."""

    list_display = ["code", "name", "company", "financial_statement"]
    list_filter = ["financial_statement", "company"]
    search_fields = ["code", "name", "company__name"]
    ordering = ["company", "financial_statement", "code"]
    raw_id_fields = ["company"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for Transaction model."""

    list_display = [
        "date",
        "company",
        "project",
        "ledger",
        "type",
        "vat",
        "amount_incl_vat",
    ]
    list_filter = [
        "type",
        "date",
        "vat",
        "company",
        "project",
    ]
    search_fields = [
        "company__name",
        "project__name",
        "ledger__code",
        "ledger__name",
        "ledger__financial_statement",
        "structure__name",
        "bill__name",
    ]
    ordering = ["-date", "ledger__code"]
    autocomplete_fields = ["ledger", "bill", "vat_rate", "company", "project"]

    def get_queryset(self, request):
        """Optimize queries."""
        return (
            super()
            .get_queryset(request)
            .select_related("ledger", "bill", "vat_rate", "company", "project")
        )
