from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView

from app.Account.models import Account


class UserDetailView(LoginRequiredMixin, DetailView):
    """Detailed view for a user showing personal details and roles."""

    model = Account
    template_name = "account/user_detail.html"
    context_object_name = "user_obj"

    def get_object(self: "UserDetailView", queryset=None) -> Account:
        """Get the user object."""
        return self.request.user  # type: ignore

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        user = self.get_object()

        # Get user's projects and portfolios
        context["projects"] = user.projects.all().order_by("-created_at")[:10]
        context["portfolios"] = user.portfolios.all().order_by("-created_at")[:10]

        # Get user's groups (roles)
        context["user_groups"] = user.groups.all()

        # Get available groups that user is not in
        all_groups = user.groups.model.objects.all()
        context["available_groups"] = all_groups.exclude(id__in=context["user_groups"])

        # Role-specific assignments
        context["contractor_projects"] = user.contractor_projects.all()
        context["qs_projects"] = user.qs_projects.all()
        context["lead_consultant_projects"] = user.lead_consultant_projects.all()
        context["client_rep_projects"] = user.client_rep_projects.all()

        return context


class UserEditView(LoginRequiredMixin, UpdateView):
    """Edit user details - only accessible by superusers."""

    model = Account
    template_name = "account/user_edit.html"
    context_object_name = "user_obj"
    fields = [
        "first_name",
        "last_name",
        "email",
        "primary_contact",
    ]

    def get_object(self: "UserEditView", queryset=None) -> Account:
        """Get the user object."""
        return self.request.user  # type: ignore

    def form_valid(self, form):
        """Add success message."""
        messages.success(
            self.request,
            f"User '{form.instance.get_full_name()}' updated successfully.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to user detail page."""
        return self.object.detail_url
