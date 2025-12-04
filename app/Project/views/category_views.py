"""Views for Project Category management."""

from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView

from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import ProjectCategoryForm
from app.Project.models import ProjectCategory


class ProjectCategoryListView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """List all project categories."""

    model = ProjectCategory
    template_name = "portfolio/category_list.html"
    context_object_name = "categories"
    permissions = ["contractor", "consultant"]

    def get_breadcrumbs(self):
        return [
            {"title": "Portfolio", "url": reverse("project:portfolio-list")},
            {"title": "Project Categories", "url": None},
        ]

    def get_queryset(self):
        """Return categories ordered by name."""
        return ProjectCategory.objects.all().order_by("name")

    def get_context_data(self, **kwargs):
        """Add form for inline creation."""
        context = super().get_context_data(**kwargs)
        context["form"] = ProjectCategoryForm()
        return context


class ProjectCategoryCreateView(UserHasGroupGenericMixin, BreadcrumbMixin, CreateView):
    """Create a new project category."""

    model = ProjectCategory
    form_class = ProjectCategoryForm
    template_name = "portfolio/category_form.html"
    permissions = ["contractor", "consultant"]
    success_url = reverse_lazy("project:category-list")

    def get_breadcrumbs(self):
        return [
            {"title": "Portfolio", "url": reverse("project:portfolio-list")},
            {"title": "Project Categories", "url": reverse("project:category-list")},
            {"title": "Add Category", "url": None},
        ]

    def form_valid(self: "ProjectCategoryCreateView", form):
        """Handle successful form submission."""
        response = super().form_valid(form)
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
        return response

    def form_invalid(self, form):
        """Handle form validation errors."""
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)


class ProjectCategoryDeleteView(UserHasGroupGenericMixin, BreadcrumbMixin, DeleteView):
    """Delete a project category."""

    model = ProjectCategory
    template_name = "portfolio/category_confirm_delete.html"
    permissions = ["contractor", "consultant"]
    success_url = reverse_lazy("project:category-list")

    def get_breadcrumbs(self):
        return [
            {"title": "Portfolio", "url": reverse("project:portfolio-list")},
            {"title": "Project Categories", "url": reverse("project:category-list")},
            {"title": "Delete Category", "url": None},
        ]

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

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        from django.shortcuts import redirect

        return redirect("project:category-list")
