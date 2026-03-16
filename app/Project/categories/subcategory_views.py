"""Views for Project SubCategory management."""

from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import ProjectSubCategory

from .category_forms import ProjectSubCategoryForm


class ProjectSubCategoryListView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """List all project subcategories."""

    model = ProjectSubCategory
    template_name = "categories/subcategory_list.html"
    context_object_name = "subcategories"
    permissions = ["contractor", "consultant"]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(title="Project Subcategories", url=None),
        ]

    def get_queryset(self):
        """Return subcategories ordered by name."""
        return ProjectSubCategory.objects.all().order_by("name")

    def get_context_data(self, **kwargs):
        """Add form for inline creation."""
        context = super().get_context_data(**kwargs)
        context["form"] = ProjectSubCategoryForm()
        return context


class ProjectSubCategoryCreateView(
    UserHasGroupGenericMixin, BreadcrumbMixin, CreateView
):
    """Create a new project subcategory."""

    model = ProjectSubCategory
    form_class = ProjectSubCategoryForm
    template_name = "categories/subcategory_form.html"
    permissions = ["contractor", "consultant"]
    success_url = reverse_lazy("project:subcategory-list")

    def get_breadcrumbs(self: "ProjectSubCategoryCreateView") -> list[BreadcrumbItem]:
        return [
            {"title": "Portfolio", "url": reverse("project:portfolio-dashboard")},
            {
                "title": "Project Subcategories",
                "url": reverse("project:subcategory-list"),
            },
            {"title": "Add Subcategory", "url": None},
        ]

    def form_valid(self: "ProjectSubCategoryCreateView", form):
        """Handle successful form submission."""
        self.object: ProjectSubCategory = form.save()

        messages.success(
            self.request, f"Subcategory '{self.object.name}' created successfully."
        )

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


class ProjectSubCategoryDeleteView(
    UserHasGroupGenericMixin, BreadcrumbMixin, DeleteView
):
    """Delete a project subcategory."""

    model = ProjectSubCategory
    template_name = "categories/subcategory_confirm_delete.html"
    permissions = ["contractor", "consultant"]
    success_url = reverse_lazy("project:subcategory-list")

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Project Subcategories", url=reverse("project:subcategory-list")
            ),
            BreadcrumbItem(title="Delete Subcategory", url=None),
        ]

    def form_valid(self, form):
        """Handle successful deletion."""
        subcategory_name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, f"Subcategory '{subcategory_name}' deleted.")

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return response

    def delete(self, request, *args, **kwargs):
        """Handle DELETE request (soft delete)."""
        self.object = self.get_object()
        subcategory_name = self.object.name

        self.object.soft_delete()
        messages.success(request, f"Subcategory '{subcategory_name}' deleted.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return self.get_success_url()

    def post(self, request, *args, **kwargs):
        """Handle POST request for deletion."""
        self.object = self.get_object()
        subcategory_name = self.object.name

        self.object.soft_delete()
        messages.success(request, f"Subcategory '{subcategory_name}' deleted.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        from django.shortcuts import redirect

        return redirect("project:subcategory-list")
