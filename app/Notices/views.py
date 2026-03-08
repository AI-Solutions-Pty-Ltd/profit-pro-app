"""Views for notices and attention items."""

from typing import Any, cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .models import Notice


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict access to superusers."""

    def test_func(self) -> bool:
        """Allow only superusers."""
        request = cast(Any, self).request
        return bool(request.user.is_superuser)

    def handle_no_permission(self):
        """Redirect unauthorized users to the notice list."""
        request = cast(Any, self).request
        messages.error(request, "Only superusers can manage notices.")
        return redirect("notices:list")


class NoticeListView(LoginRequiredMixin, ListView):
    """List notices for authenticated users."""

    model = Notice
    template_name = "notices/notice_list.html"
    context_object_name = "notices"

    def get_context_data(self, **kwargs):
        """Add dummy project matters requiring attention."""
        context = super().get_context_data(**kwargs)
        context["attention_items"] = [
            {
                "title": "RFI #102 awaiting consultant response",
                "project": "Riverside Upgrade",
                "age": "2 days",
                "url": "#",
            },
            {
                "title": "RFI #106 missing drawing reference",
                "project": "Airport Terminal Fitout",
                "age": "4 days",
                "url": "#",
            },
            {
                "title": "RFI #111 blocked by client clarification",
                "project": "South Ridge Housing",
                "age": "1 day",
                "url": "#",
            },
            {
                "title": "RFI #117 requires revised specification",
                "project": "Harbor Bulk Services",
                "age": "3 days",
                "url": "#",
            },
            {
                "title": "RFI #121 pending design office feedback",
                "project": "North Link Civils",
                "age": "5 days",
                "url": "#",
            },
        ]
        # Add total count for badge
        context["total_notices"] = self.get_queryset().count() + len(
            context["attention_items"]
        )
        return context


class NoticeDetailView(LoginRequiredMixin, DetailView):
    """Display a single notice."""

    model = Notice
    template_name = "notices/notice_detail.html"
    context_object_name = "notice"


class NoticeCreateView(SuperuserRequiredMixin, CreateView):
    """Create a new notice."""

    model = Notice
    template_name = "notices/notice_form.html"
    fields = ["text"]
    success_url = reverse_lazy("notices:list")

    def form_valid(self, form):
        """Show success message after creating notice."""
        messages.success(self.request, "Notice created successfully.")
        return super().form_valid(form)


class NoticeUpdateView(SuperuserRequiredMixin, UpdateView):
    """Edit an existing notice."""

    model = Notice
    template_name = "notices/notice_form.html"
    fields = ["text"]
    success_url = reverse_lazy("notices:list")

    def form_valid(self, form):
        """Show success message after updating notice."""
        messages.success(self.request, "Notice updated successfully.")
        return super().form_valid(form)


class NoticeDeleteView(SuperuserRequiredMixin, DeleteView):
    """Delete a notice."""

    model = Notice
    template_name = "notices/notice_confirm_delete.html"
    success_url = reverse_lazy("notices:list")

    def form_valid(self, form):
        """Show success message after deleting notice."""
        messages.success(self.request, "Notice deleted successfully.")
        return super().form_valid(form)
