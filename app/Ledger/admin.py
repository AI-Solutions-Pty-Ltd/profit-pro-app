"""Admin configuration for Ledger models."""

from django.contrib import admin

from app.Ledger.models import FinancialStatement, Ledger, Transaction, Vat


@admin.register(Vat)
class VatAdmin(admin.ModelAdmin):
    """Admin configuration for VAT model."""

    list_display = ["name", "rate", "start_date", "end_date"]
    list_filter = ["rate", "start_date", "end_date"]
    search_fields = ["name"]
    ordering = ["-start_date", "name"]


@admin.register(FinancialStatement)
class FinancialStatementAdmin(admin.ModelAdmin):
    """Admin configuration for FinancialStatement model."""

    list_display = ["name"]
    search_fields = ["name"]
    ordering = ["name"]


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
        "debit_ledger",
        "credit_ledger",
        "vat",
        "amount_incl_vat",
    ]
    list_filter = [
        "date",
        "vat",
        "company",
        "project",
    ]
    search_fields = [
        "company__name",
        "project__name",
        "debit_ledger__code",
        "debit_ledger__name",
        "debit_ledger__financial_statement",
        "credit_ledger__code",
        "credit_ledger__name",
        "credit_ledger__financial_statement",
        "structure__name",
        "bill__name",
    ]
    ordering = [
        "-date",
        "debit_ledger__financial_statement",
        "debit_ledger__code",
        "credit_ledger__code",
    ]
    autocomplete_fields = [
        "debit_ledger",
        "credit_ledger",
        "bill",
        "vat_rate",
        "company",
        "project",
    ]

    def get_queryset(self, request):
        """Optimize queries."""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "debit_ledger", "credit_ledger", "vat_rate", "company", "project"
            )
        )
