"""Views for Category, SubCategory, and Discipline management."""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.projects.category_forms import (
    CategoryForm,
    DisciplineForm,
    SubCategoryForm,
)
from app.Project.projects.projects_models import (
    Category,
    Discipline,
    Project,
    SubCategory,
)


class CategoryListView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """List all categories."""

    model = Category
    template_name = "project/category_manage.html"
    context_object_name = "categories"
    permissions = ["contractor", "consultant"]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(title="Categories", url=None),
        ]

    def get_queryset(self):
        """Return categories ordered by name."""
        return Category.objects.filter(
            projects_id=self.kwargs["project_pk"], deleted=False
        ).order_by("name")

    def get_context_data(self, **kwargs):
        """Add form for inline creation."""
        context = super().get_context_data(**kwargs)
        context["form"] = CategoryForm()
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
        return context


class CategoryCreateView(UserHasGroupGenericMixin, BreadcrumbMixin, CreateView):
    """Create a new category."""

    model = Category
    form_class = CategoryForm
    template_name = "project/category_form.html"
    permissions = ["contractor", "consultant"]

    def get_success_url(self):
        return reverse_lazy(
            "project:project-category-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Categories",
                url=reverse(
                    "project:project-category-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title="Add Category", url=None),
        ]

    def form_valid(self, form):
        """Handle successful form submission."""
        form.instance.projects_id = self.kwargs["project_pk"]
        self.object = form.save()
        messages.success(
            self.request, f"Category '{self.object.name}' created successfully."
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


class CategoryUpdateView(UserHasGroupGenericMixin, BreadcrumbMixin, UpdateView):
    """Update a category."""

    model = Category
    form_class = CategoryForm
    template_name = "project/category_form.html"
    permissions = ["contractor", "consultant"]

    def get_success_url(self):
        return reverse_lazy(
            "project:project-category-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Categories",
                url=reverse(
                    "project:project-category-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title="Edit Category", url=None),
        ]

    def form_valid(self, form):
        """Handle successful form submission."""
        form.instance.projects_id = self.kwargs["project_pk"]
        self.object = form.save()
        messages.success(
            self.request, f"Category '{self.object.name}' updated successfully."
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


class CategoryDeleteView(UserHasGroupGenericMixin, BreadcrumbMixin, DeleteView):
    """Delete a category."""

    model = Category
    template_name = "project/category_confirm_delete.html"
    permissions = ["contractor", "consultant"]

    def get_success_url(self):
        return reverse_lazy(
            "project:project-category-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Categories",
                url=reverse(
                    "project:project-category-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title="Delete Category", url=None),
        ]

    def post(self, request, *args, **kwargs):
        """Handle POST request for deletion."""
        self.object = self.get_object()
        category_name = self.object.name

        self.object.soft_delete()
        messages.success(request, f"Category '{category_name}' deleted.")

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return redirect(
            "project:project-category-list", project_pk=self.kwargs["project_pk"]
        )


class SubCategoryListView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """List all subcategories."""

    model = SubCategory
    template_name = "project/subcategory_manage.html"
    context_object_name = "subcategories"
    permissions = ["contractor", "consultant"]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(title="Sub Categories", url=None),
        ]

    def get_queryset(self):
        """Return subcategories ordered by name."""
        return SubCategory.objects.filter(
            project_id=self.kwargs["project_pk"], deleted=False
        ).order_by("name")

    def get_context_data(self, **kwargs):
        """Add form for inline creation."""
        context = super().get_context_data(**kwargs)
        context["form"] = SubCategoryForm()
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
        return context


class SubCategoryCreateView(UserHasGroupGenericMixin, BreadcrumbMixin, CreateView):
    """Create a new subcategory."""

    model = SubCategory
    form_class = SubCategoryForm
    template_name = "project/subcategory_form.html"
    permissions = ["contractor", "consultant"]

    def get_success_url(self):
        return reverse_lazy(
            "project:project-subcategory-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Sub Categories",
                url=reverse(
                    "project:project-subcategory-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title="Add Sub Category", url=None),
        ]

    def form_valid(self, form):
        """Handle successful form submission."""
        form.instance.project_id = self.kwargs["project_pk"]
        self.object = form.save()
        messages.success(
            self.request, f"Sub category '{self.object.name}' created successfully."
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


class SubCategoryUpdateView(UserHasGroupGenericMixin, BreadcrumbMixin, UpdateView):
    """Update a subcategory."""

    model = SubCategory
    form_class = SubCategoryForm
    template_name = "project/subcategory_form.html"
    permissions = ["contractor", "consultant"]

    def get_success_url(self):
        return reverse_lazy(
            "project:project-subcategory-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Sub Categories",
                url=reverse(
                    "project:project-subcategory-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title="Edit Sub Category", url=None),
        ]

    def form_valid(self, form):
        """Handle successful form submission."""
        form.instance.project_id = self.kwargs["project_pk"]
        self.object = form.save()
        messages.success(
            self.request, f"Sub category '{self.object.name}' updated successfully."
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


class SubCategoryDeleteView(UserHasGroupGenericMixin, BreadcrumbMixin, DeleteView):
    """Delete a subcategory."""

    model = SubCategory
    template_name = "project/subcategory_confirm_delete.html"
    permissions = ["contractor", "consultant"]

    def get_success_url(self):
        return reverse_lazy(
            "project:project-subcategory-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Sub Categories",
                url=reverse(
                    "project:project-subcategory-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title="Delete Sub Category", url=None),
        ]

    def post(self, request, *args, **kwargs):
        """Handle POST request for deletion."""
        self.object = self.get_object()
        subcategory_name = self.object.name

        self.object.soft_delete()
        messages.success(request, f"Sub category '{subcategory_name}' deleted.")

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return redirect(
            "project:project-subcategory-list", project_pk=self.kwargs["project_pk"]
        )


class DisciplineListView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """List all disciplines."""

    model = Discipline
    template_name = "project/discipline_manage.html"
    context_object_name = "disciplines"
    permissions = ["contractor", "consultant"]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(title="Disciplines", url=None),
        ]

    def get_queryset(self):
        """Return disciplines ordered by name."""
        return Discipline.objects.filter(
            projects=self.kwargs["project_pk"], deleted=False
        ).order_by("name")

    def get_context_data(self, **kwargs):
        """Add form for inline creation."""
        context = super().get_context_data(**kwargs)
        context["form"] = DisciplineForm()
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
        return context


class DisciplineCreateView(UserHasGroupGenericMixin, BreadcrumbMixin, CreateView):
    """Create a new discipline."""

    model = Discipline
    form_class = DisciplineForm
    template_name = "project/discipline_form.html"
    permissions = ["contractor", "consultant"]

    def get_success_url(self):
        return reverse_lazy(
            "project:project-discipline-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Disciplines",
                url=reverse(
                    "project:project-discipline-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title="Add Discipline", url=None),
        ]

    def form_valid(self, form):
        """Handle successful form submission."""
        form.instance.projects_id = self.kwargs["project_pk"]
        self.object = form.save()
        messages.success(
            self.request, f"Discipline '{self.object.name}' created successfully."
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


class DisciplineUpdateView(UserHasGroupGenericMixin, BreadcrumbMixin, UpdateView):
    """Update a discipline."""

    model = Discipline
    form_class = DisciplineForm
    template_name = "project/discipline_form.html"
    permissions = ["contractor", "consultant"]

    def get_success_url(self):
        return reverse_lazy(
            "project:project-discipline-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Disciplines",
                url=reverse(
                    "project:project-discipline-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title="Edit Discipline", url=None),
        ]

    def form_valid(self, form):
        """Handle successful form submission."""
        form.instance.projects_id = self.kwargs["project_pk"]
        self.object = form.save()
        messages.success(
            self.request, f"Discipline '{self.object.name}' updated successfully."
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


class DisciplineDeleteView(UserHasGroupGenericMixin, BreadcrumbMixin, DeleteView):
    """Delete a discipline."""

    model = Discipline
    template_name = "project/discipline_confirm_delete.html"
    permissions = ["contractor", "consultant"]

    def get_success_url(self):
        return reverse_lazy(
            "project:project-discipline-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Disciplines",
                url=reverse(
                    "project:project-discipline-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title="Delete Discipline", url=None),
        ]

    def post(self, request, *args, **kwargs):
        """Handle POST request for deletion."""
        self.object = self.get_object()
        discipline_name = self.object.name

        self.object.soft_delete()
        messages.success(request, f"Discipline '{discipline_name}' deleted.")

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return redirect(
            "project:project-discipline-list", project_pk=self.kwargs["project_pk"]
        )
