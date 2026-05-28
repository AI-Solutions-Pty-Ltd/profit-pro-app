from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import DetailView, TemplateView, UpdateView

from app.Account.models import Account
from app.Account.subscription_config import Subscription


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


class DemoExpiredView(LoginRequiredMixin, TemplateView):
    """View shown to users whose demo subscription has expired."""

    template_name = "account/demo_expired.html"

    def dispatch(self, request, *args, **kwargs):
        """Redirect active non-expired users back to home."""
        user = request.user
        if not user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        is_demo = getattr(user, "subscription", None) == Subscription.DEMO_TIER
        is_expired = getattr(user, "is_subscription_expired", False)
        is_staff_or_admin = user.is_superuser or user.is_staff

        if is_staff_or_admin or not (is_demo and is_expired):
            return redirect("home")

        # Clean up target demo companies on trial expiration
        from app.Project.models import Company

        Company.clean_demo_companies(user)

        return super().dispatch(request, *args, **kwargs)
