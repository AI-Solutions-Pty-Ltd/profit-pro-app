from django.contrib import admin

from app.SiteManagement.models import (
    EarlyWarning,
    Meeting,
    RFI,
    SiteInstruction,
)


@admin.register(EarlyWarning)
class EarlyWarningAdmin(admin.ModelAdmin):
    list_display = [
        "reference_number",
        "project",
        "subject",
        "submitted_by",
        "to_user",
        "status",
        "date",
        "respond_by_date",
    ]
    list_filter = ["status", "impact_time", "impact_cost", "impact_quality", "project"]
    search_fields = ["reference_number", "subject", "message"]
    readonly_fields = [
        "reference_number",
        "date",
        "submitted_by",
        "submitted_by_role",
        "response_date",
        "date_closed",
    ]


@admin.register(SiteInstruction)
class SiteInstructionAdmin(admin.ModelAdmin):
    list_display = [
        "reference_number",
        "project",
        "subject",
        "issued_by",
        "to_user",
        "status",
        "date_notified",
    ]
    list_filter = ["status", "project"]
    search_fields = ["reference_number", "subject", "instruction"]
    readonly_fields = [
        "reference_number",
        "date_notified",
        "issued_by",
        "date_closed",
    ]


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "meeting_type",
        "date",
        "status",
        "date_closed",
    ]
    list_filter = ["meeting_type", "status", "project"]
    search_fields = ["key_decisions"]
    readonly_fields = ["date_closed"]


@admin.register(RFI)
class RFIAdmin(admin.ModelAdmin):
    list_display = [
        "reference_number",
        "project",
        "subject",
        "issued_by",
        "to_user",
        "status",
        "date_issued",
        "respond_by_date",
    ]
    list_filter = ["status", "project"]
    search_fields = ["reference_number", "subject", "message"]
    readonly_fields = [
        "reference_number",
        "date_issued",
        "issued_by",
        "response_date",
        "date_closed",
    ]
