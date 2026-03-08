from django.contrib import admin

from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    """Admin configuration for notices."""

    list_display = ("id", "short_text", "created_at", "updated_at")
    search_fields = ("text",)
    ordering = ("-created_at",)

    @staticmethod
    def short_text(obj: Notice) -> str:
        """Display truncated notice text in list view."""
        return obj.text[:80]
