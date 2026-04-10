from django.contrib import admin

from app.SiteManagement.models import (
    RFI,
    EarlyWarning,
    Incident,
    LabourLog,
    Meeting,
    NonConformance,
    OverheadDailyLog,
    SiteInstruction,
    SkillType,
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


@admin.register(LabourLog)
class LabourLogAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "date",
        "person_name",
        "trade",
        "skill_type",
        "hours_worked",
    ]
    list_filter = ["project", "date", "skill_type"]
    search_fields = ["person_name", "trade", "task_activity"]


@admin.register(SkillType)
class SkillTypeAdmin(admin.ModelAdmin):
    list_display = ["project", "name", "hourly_rate"]
    list_filter = ["project"]
    search_fields = ["name"]


@admin.register(OverheadDailyLog)
class OverheadDailyLogAdmin(admin.ModelAdmin):
    list_display = ["project", "date", "description", "category", "quantity"]
    list_filter = ["project", "date", "category"]
    search_fields = ["description", "remarks"]
    readonly_fields = ["description", "category"]


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = [
        "reference_number",
        "project",
        "incident_type",
        "date",
        "location",
        "reported_by",
        "status",
    ]
    list_filter = ["incident_type", "status", "project"]
    search_fields = ["reference_number", "description", "location"]
    readonly_fields = ["reference_number", "date_closed"]


@admin.register(NonConformance)
class NonConformanceAdmin(admin.ModelAdmin):
    list_display = [
        "reference_number",
        "project",
        "ncr_type",
        "date",
        "responsible_person",
        "status",
    ]
    list_filter = ["ncr_type", "status", "project"]
    search_fields = ["reference_number", "description", "defect_description"]
    readonly_fields = ["reference_number", "date", "date_closed"]
