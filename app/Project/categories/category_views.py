"""Views for Project Category management."""

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.views.generic.base import ContextMixin

from app.Project.models import ProjectCategory

from .category_forms import ProjectCategoryForm


class SystemLibraryMixin(UserPassesTestMixin, ContextMixin):
    """Mixin for system library views: requires staff."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_system_view"] = True
        return context


class ProjectCategoryListView(SystemLibraryMixin, ListView):
    """List all project categories."""

    model = ProjectCategory
    template_name = "estimator/system/sector_manage.html"
    context_object_name = "categories"

    def get_queryset(self):
        """Return categories ordered by name."""
        return ProjectCategory.objects.all().order_by("name")

    def get_context_data(self, **kwargs):
        """Add form for inline creation."""
        context = super().get_context_data(**kwargs)
        context["form"] = ProjectCategoryForm()
        return context


class ProjectCategoryCreateView(SystemLibraryMixin, CreateView):
    """Create a new project category."""

    model = ProjectCategory
    form_class = ProjectCategoryForm
    template_name = "estimator/system/sector_form.html"
    success_url = reverse_lazy("estimator:sys_sectors")

    def form_valid(self, form):
        """Handle successful form submission."""
        self.object = form.save()

        messages.success(
            self.request, f"Category '{self.object.name}' created successfully."
        )

        # Handle AJAX requests
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": True,
                    "id": self.object.pk,
                    "name": self.object.name,
                    "description": self.object.description,
                }
            )

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle form validation errors."""
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)


class ProjectCategoryUpdateView(SystemLibraryMixin, UpdateView):
    """Update a project category."""

    model = ProjectCategory
    form_class = ProjectCategoryForm
    template_name = "estimator/system/sector_form.html"
    success_url = reverse_lazy("estimator:sys_sectors")

    def form_valid(self, form):
        """Handle successful form submission."""
        self.object = form.save()
        messages.success(
            self.request, f"Category '{self.object.name}' updated successfully."
        )

        # Handle AJAX requests
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": True,
                    "id": self.object.pk,
                    "name": self.object.name,
                    "description": self.object.description,
                }
            )

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle form validation errors."""
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)


class ProjectCategoryDeleteView(SystemLibraryMixin, DeleteView):
    """Delete a project category."""

    model = ProjectCategory
    template_name = "estimator/system/sector_confirm_delete.html"
    success_url = reverse_lazy("estimator:sys_sectors")

    def form_valid(self, form):
        """Handle successful deletion."""
        category_name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, f"Category '{category_name}' deleted.")

        # Handle AJAX requests
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return response

    def delete(self, request, *args, **kwargs):
        """Handle DELETE request (soft delete)."""
        self.object = self.get_object()
        category_name = self.object.name

        # Use soft delete
        self.object.soft_delete()
        messages.success(request, f"Category '{category_name}' deleted.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return self.get_success_url()

    def post(self, request, *args, **kwargs):
        """Handle POST request for deletion."""
        self.object = self.get_object()
        category_name = self.object.name

        # Use soft delete
        self.object.soft_delete()
        messages.success(request, f"Category '{category_name}' deleted.")

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return redirect("estimator:sys_sectors")
