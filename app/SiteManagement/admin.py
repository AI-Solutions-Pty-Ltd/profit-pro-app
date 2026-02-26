from django.contrib import admin

from app.SiteManagement.models import EarlyWarning


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
