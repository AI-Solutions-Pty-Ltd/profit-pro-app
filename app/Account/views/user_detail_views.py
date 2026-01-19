"""Views for user detail pages and role management."""

from typing import TYPE_CHECKING

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    DetailView,
    FormView,
    UpdateView,
)

from app.Account.models import Account

if TYPE_CHECKING:
    from django.http import HttpRequest


class UserDetailView(LoginRequiredMixin, DetailView):
    """Detailed view for a user showing personal details and roles."""

    model = Account
    template_name = "account/user_detail.html"
    context_object_name = "user_obj"

    def get_object(self):
        """Get the user object."""
        return get_object_or_404(Account, pk=self.kwargs["user_pk"])

    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        user_obj = self.get_object()

        # Get user's projects and portfolios
        context["projects"] = user_obj.projects.all().order_by("-created_at")[:10]
        context["portfolios"] = user_obj.portfolios.all().order_by("-created_at")[:10]

        # Get user's groups (roles)
        context["user_groups"] = user_obj.groups.all()

        # Get available groups that user is not in
        all_groups = user_obj.groups.model.objects.all()
        context["available_groups"] = all_groups.exclude(id__in=context["user_groups"])

        # Role-specific assignments
        context["contractor_projects"] = user_obj.contractor_projects.all()
        context["qs_projects"] = user_obj.qs_projects.all()
        context["lead_consultant_projects"] = user_obj.lead_consultant_projects.all()
        context["client_rep_projects"] = user_obj.client_rep_projects.all()

        return context


class UserGroupMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure user has permission to manage roles."""

    request: "HttpRequest"

    def test_func(self) -> bool:
        """Only superusers can manage user roles."""
        return self.request.user.is_superuser

    def handle_no_permission(self):
        """Redirect if not authorized."""
        from django.contrib import messages
        from django.shortcuts import redirect

        messages.error(self.request, "You don't have permission to manage user roles.")
        return redirect("account:login")


class UserGroupAddView(UserGroupMixin, FormView):
    """Add a user to a group (role)."""

    template_name = "account/user_group_add.html"
    form_class = forms.Form

    def get_user(self):
        """Get the user object."""
        return get_object_or_404(Account, pk=self.kwargs["user_pk"])

    def get_context_data(self, **kwargs):
        """Add user and groups to context."""
        context = super().get_context_data(**kwargs)
        user = self.get_user()
        context["user_obj"] = user

        # Get available groups
        all_groups = user.groups.model.objects.all()
        context["available_groups"] = all_groups.exclude(id__in=user.groups.all())

        return context

    def post(self, request, *args, **kwargs):
        """Add user to selected groups."""
        user = self.get_user()
        group_ids = request.POST.getlist("groups")

        from django.contrib.auth.models import Group

        groups = Group.objects.filter(id__in=group_ids)
        user.groups.add(*groups)

        from django.contrib import messages

        messages.success(
            request, f"Added {user.get_full_name()} to {len(groups)} group(s)."
        )

        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        """Redirect to user detail page."""
        return reverse_lazy(
            "project:portfolio-users",
        )


class UserGroupRemoveView(UserGroupMixin, FormView):
    """Remove a user from a group (role)."""

    template_name = "account/user_group_remove.html"
    form_class = forms.Form

    def get_context_data(self, **kwargs):
        """Add user and group to context."""
        context = super().get_context_data(**kwargs)
        from django.contrib.auth.models import Group

        context["user_obj"] = get_object_or_404(Account, pk=self.kwargs["user_pk"])
        context["group"] = get_object_or_404(Group, pk=self.kwargs["group_pk"])
        return context

    def form_valid(self, form):
        """Remove user from group."""
        user = get_object_or_404(Account, pk=self.kwargs["user_pk"])
        from django.contrib.auth.models import Group

        group = get_object_or_404(Group, pk=self.kwargs["group_pk"])
        user.groups.remove(group)

        messages.success(
            self.request, f"Removed {user.get_full_name()} from {group.name}."
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to user detail page."""
        return reverse_lazy(
            "account:user-detail", kwargs={"user_pk": self.kwargs["user_pk"]}
        )


class UserEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit user details - only accessible by superusers."""

    model = Account
    template_name = "account/user_edit.html"
    context_object_name = "user_obj"
    fields = [
        "first_name",
        "last_name",
        "email",
        "primary_contact",
        "suburb",
        "postcode",
        "type",
        "is_active",
    ]

    def get_object(self):
        """Get the user object."""
        return get_object_or_404(Account, pk=self.kwargs["user_pk"])

    def test_func(self):
        """Only allow superusers to edit users."""
        return self.request.user.is_superuser  # type: ignore[attr-defined]

    def handle_no_permission(self):
        """Show error message if not superuser."""
        messages.error(self.request, "You don't have permission to edit users.")
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(
            reverse_lazy(
                "account:user-detail", kwargs={"user_pk": self.kwargs["user_pk"]}
            )
        )

    def form_valid(self, form):
        """Add success message."""
        messages.success(
            self.request,
            f"User '{form.instance.get_full_name()}' updated successfully.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to user detail page."""
        return reverse_lazy(
            "account:user-detail", kwargs={"user_pk": self.kwargs["user_pk"]}
        )
