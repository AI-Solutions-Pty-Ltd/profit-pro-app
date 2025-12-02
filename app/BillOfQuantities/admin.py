from django.contrib import admin

from app.core.Utilities.admin import SoftDeleteAdmin

from .models import (
    ActualTransaction,
    AdvancePayment,
    BaselineCashflow,
    Bill,
    CashflowForecast,
    ContractualCorrespondence,
    ContractVariation,
    Escalation,
    Forecast,
    ForecastTransaction,
    LineItem,
    MaterialsOnSite,
    Package,
    PaymentCertificate,
    Retention,
    RevisedBaseline,
    RevisedBaselineDetail,
    ScheduleForecast,
    ScheduleForecastSection,
    SectionalCompletionDate,
    SpecialItemTransaction,
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


# ============================================================================
# Contract Management Admin
# ============================================================================


@admin.register(ContractVariation)
class ContractVariationAdmin(SoftDeleteAdmin):
    """Admin for Contract Variations."""

    list_display = [
        "variation_number",
        "title",
        "project",
        "category",
        "variation_type",
        "status",
        "variation_amount",
        "time_extension_days",
        "deleted",
    ]
    list_filter = [
        "project",
        "category",
        "variation_type",
        "status",
        "deleted",
        "created_at",
    ]
    search_fields = ["variation_number", "title", "description", "project__name"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]


@admin.register(ContractualCorrespondence)
class ContractualCorrespondenceAdmin(SoftDeleteAdmin):
    """Admin for Contractual Correspondences."""

    list_display = [
        "reference_number",
        "subject",
        "project",
        "correspondence_type",
        "direction",
        "date_of_correspondence",
        "requires_response",
        "response_sent",
        "deleted",
    ]
    list_filter = [
        "project",
        "correspondence_type",
        "direction",
        "requires_response",
        "response_sent",
        "deleted",
    ]
    search_fields = ["reference_number", "subject", "summary", "project__name"]
    date_hierarchy = "date_of_correspondence"
    ordering = ["-date_of_correspondence"]


# ============================================================================
# Ledger Models Admin
# ============================================================================


@admin.register(AdvancePayment)
class AdvancePaymentAdmin(SoftDeleteAdmin):
    """Admin for Advance Payments."""

    list_display = [
        "project",
        "payment_certificate",
        "transaction_type",
        "amount",
        "recovery_method",
        "date",
        "deleted",
    ]
    list_filter = [
        "project",
        "transaction_type",
        "recovery_method",
        "deleted",
    ]
    search_fields = ["project__name", "description", "guarantee_reference"]


@admin.register(Retention)
class RetentionAdmin(SoftDeleteAdmin):
    """Admin for Retentions."""

    list_display = [
        "project",
        "payment_certificate",
        "retention_type",
        "transaction_type",
        "amount",
        "retention_percentage",
        "date",
        "deleted",
    ]
    list_filter = [
        "project",
        "retention_type",
        "transaction_type",
        "deleted",
    ]
    search_fields = ["project__name", "description"]


@admin.register(MaterialsOnSite)
class MaterialsOnSiteAdmin(SoftDeleteAdmin):
    """Admin for Materials on Site."""

    list_display = [
        "project",
        "payment_certificate",
        "material_description",
        "material_status",
        "transaction_type",
        "amount",
        "quantity",
        "deleted",
    ]
    list_filter = [
        "project",
        "material_status",
        "transaction_type",
        "deleted",
    ]
    search_fields = ["project__name", "material_description", "delivery_note_reference"]


@admin.register(Escalation)
class EscalationAdmin(SoftDeleteAdmin):
    """Admin for Escalations."""

    list_display = [
        "project",
        "payment_certificate",
        "escalation_type",
        "transaction_type",
        "amount",
        "escalation_factor",
        "deleted",
    ]
    list_filter = [
        "project",
        "escalation_type",
        "transaction_type",
        "deleted",
    ]
    search_fields = ["project__name", "description", "formula_reference"]


@admin.register(SpecialItemTransaction)
class SpecialItemTransactionAdmin(SoftDeleteAdmin):
    """Admin for Special Item Transactions."""

    list_display = [
        "project",
        "payment_certificate",
        "special_item_type",
        "transaction_type",
        "amount",
        "item_reference",
        "deleted",
    ]
    list_filter = [
        "project",
        "special_item_type",
        "transaction_type",
        "deleted",
    ]
    search_fields = ["project__name", "description", "item_reference"]


# ============================================================================
# Cashflow Models Admin
# ============================================================================


@admin.register(BaselineCashflow)
class BaselineCashflowAdmin(SoftDeleteAdmin):
    """Admin for Baseline Cashflows."""

    list_display = [
        "project",
        "version",
        "period",
        "planned_value",
        "cumulative_value",
        "status",
        "deleted",
    ]
    list_filter = ["project", "status", "deleted"]
    search_fields = ["project__name"]
    date_hierarchy = "period"
    ordering = ["project", "version", "period"]


@admin.register(RevisedBaseline)
class RevisedBaselineAdmin(SoftDeleteAdmin):
    """Admin for Revised Baselines."""

    list_display = [
        "project",
        "revision_number",
        "revision_date",
        "revision_reason",
        "status",
        "original_completion_date",
        "revised_completion_date",
        "deleted",
    ]
    list_filter = ["project", "revision_reason", "status", "deleted"]
    search_fields = ["project__name", "reason_description"]
    date_hierarchy = "revision_date"


class RevisedBaselineDetailInline(admin.TabularInline):
    """Inline for Revised Baseline Details."""

    model = RevisedBaselineDetail
    extra = 0
    fields = ["period", "planned_value", "cumulative_value", "notes"]


@admin.register(RevisedBaselineDetail)
class RevisedBaselineDetailAdmin(SoftDeleteAdmin):
    """Admin for Revised Baseline Details."""

    list_display = [
        "revised_baseline",
        "period",
        "planned_value",
        "cumulative_value",
        "deleted",
    ]
    list_filter = ["revised_baseline__project", "deleted"]
    search_fields = ["revised_baseline__project__name"]
    date_hierarchy = "period"


@admin.register(CashflowForecast)
class CashflowForecastAdmin(SoftDeleteAdmin):
    """Admin for Cashflow Forecasts."""

    list_display = [
        "project",
        "forecast_date",
        "forecast_period",
        "forecast_value",
        "baseline_value",
        "variance",
        "status",
        "deleted",
    ]
    list_filter = ["project", "status", "deleted"]
    search_fields = ["project__name"]
    date_hierarchy = "forecast_period"


# ============================================================================
# Schedule Models Admin
# ============================================================================


@admin.register(SectionalCompletionDate)
class SectionalCompletionDateAdmin(SoftDeleteAdmin):
    """Admin for Sectional Completion Dates."""

    list_display = [
        "project",
        "section_name",
        "status",
        "planned_completion_date",
        "forecast_completion_date",
        "actual_completion_date",
        "percentage_complete",
        "deleted",
    ]
    list_filter = ["project", "status", "has_penalty", "deleted"]
    search_fields = ["project__name", "section_name", "section_description"]
    date_hierarchy = "planned_completion_date"


@admin.register(ScheduleForecast)
class ScheduleForecastAdmin(SoftDeleteAdmin):
    """Admin for Schedule Forecasts."""

    list_display = [
        "project",
        "forecast_date",
        "reporting_period",
        "planned_project_completion",
        "forecast_project_completion",
        "overall_percentage_complete",
        "status",
        "deleted",
    ]
    list_filter = ["project", "status", "deleted"]
    search_fields = ["project__name"]
    date_hierarchy = "forecast_date"


@admin.register(ScheduleForecastSection)
class ScheduleForecastSectionAdmin(SoftDeleteAdmin):
    """Admin for Schedule Forecast Sections."""

    list_display = [
        "schedule_forecast",
        "sectional_completion",
        "forecast_completion_date",
        "percentage_complete",
        "deleted",
    ]
    list_filter = ["schedule_forecast__project", "deleted"]
    search_fields = [
        "schedule_forecast__project__name",
        "sectional_completion__section_name",
    ]
