"""Views for Category, SubCategory, and Discipline management."""

from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import (
    UserHasProjectRoleGenericMixin,
)
from app.Project.models.project_roles_models import Role
from app.Project.projects.category_forms import (
    CategoryForm,
    DisciplineForm,
    GroupForm,
    SubCategoryForm,
)
from app.Project.projects.projects_models import (
    Category,
    Discipline,
    Group,
    SubCategory,
)


class CategoryListView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, ListView):
    """List all categories."""

    model = Category
    template_name = "project/category_manage.html"
    context_object_name = "categories"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title=f"Setup: {project.name}",
                url=reverse("project:project-setup", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(title="Categories", url=None),
        ]

    def get_queryset(self):
        """Return categories ordered by name."""
        return Category.objects.filter(
            project=self.get_project(), deleted=False
        ).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category_form"] = CategoryForm()
        return context


class CategoryCreateView(
    UserHasProjectRoleGenericMixin,
    APIView,
):
    """Create a new category."""

    model = Category
    form_class = CategoryForm
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, *args, **kwargs):
        """Handle POST request for category creation."""
        form = CategoryForm(request.data)

        if form.is_valid():
            form.instance.project = self.get_project()
            category = form.save()
            messages.success(
                request, f"Category '{category.name}' created successfully."
            )
            response_data = {
                "success": True,
                "id": category.pk,
                "name": category.name,
                "description": category.description,
            }
            # Include return_url in AJAX response if present
            return_url = request.data.get("return_url")
            if return_url:
                response_data["return_url"] = return_url
            return Response(response_data, status=200)

        # Format errors properly for JSON serialization
        return Response(dict(form.errors), status=400)


class CategoryUpdateView(
    UserHasProjectRoleGenericMixin,
    APIView,
):
    """Update a category."""

    model = Category
    form_class = CategoryForm
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for category update."""
        category = get_object_or_404(Category, project=self.get_project(), pk=pk)
        form = CategoryForm(request.data, instance=category)

        if form.is_valid():
            form.instance.project = self.get_project()
            category = form.save()
            messages.success(
                request, f"Category '{category.name}' updated successfully."
            )
            response_data = {
                "success": True,
                "id": category.pk,
                "name": category.name,
                "description": category.description,
            }
            return Response(response_data, status=200)

        return Response(dict(form.errors), status=400)


class CategoryDeleteView(
    UserHasProjectRoleGenericMixin,
    APIView,
):
    """Delete a category."""

    model = Category
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for deletion."""
        category = get_object_or_404(Category, project=self.get_project(), pk=pk)
        category_name = category.name

        category.soft_delete()
        messages.success(request, f"Category '{category_name}' deleted.")

        return Response({"success": True}, status=200)


class SubCategoryListView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, ListView):
    """List all subcategories for a specific category."""

    model = SubCategory
    template_name = "project/subcategory_manage.html"
    context_object_name = "subcategories"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_category(self):
        """Get the parent category from URL."""
        category_pk = self.kwargs.get("category_pk")
        return get_object_or_404(
            Category, pk=category_pk, project=self.get_project(), deleted=False
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        category = self.get_category()
        return [
            BreadcrumbItem(
                title=project.name,
                url=reverse("project:project-management", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Setup",
                url=reverse("project:project-setup", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Categories",
                url=reverse(
                    "project:project-category-list", kwargs={"project_pk": project.pk}
                ),
            ),
            BreadcrumbItem(title=f"{category.name} - Sub Categories", url=None),
        ]

    def get_queryset(self):
        """Return subcategories for the parent category."""
        category = self.get_category()
        return SubCategory.objects.filter(
            category=category, project=self.get_project(), deleted=False
        ).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_category()
        context["category"] = category
        context["subcategory_form"] = SubCategoryForm(project=self.get_project())
        return context


class SubCategoryCreateView(UserHasProjectRoleGenericMixin, APIView):
    """Handle subcategory creation via POST."""

    model = SubCategory
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_category(self):
        """Get the parent category from URL."""
        category_pk = self.kwargs.get("category_pk")
        return get_object_or_404(
            Category, pk=category_pk, project=self.get_project(), deleted=False
        )

    def post(self, request, *args, **kwargs):
        """Handle POST request for subcategory creation."""
        form = SubCategoryForm(request.data, project=self.get_project())
        if form.is_valid():
            form.instance.project = self.get_project()
            form.instance.category = self.get_category()  # Auto-fill parent category
            subcategory = form.save()
            messages.success(
                request, f"Sub category '{subcategory.name}' created successfully."
            )
            response_data = {
                "success": True,
                "id": subcategory.pk,
                "name": subcategory.name,
                "description": subcategory.description,
            }
            return Response(response_data, status=200)

        return Response(dict(form.errors), status=400)


class SubCategoryUpdateView(UserHasProjectRoleGenericMixin, APIView):
    """Handle subcategory update via POST."""

    model = SubCategory
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_category(self):
        """Get the parent category from URL."""
        category_pk = self.kwargs.get("category_pk")
        return get_object_or_404(
            Category, pk=category_pk, project=self.get_project(), deleted=False
        )

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for subcategory update."""
        category = self.get_category()
        subcategory = get_object_or_404(
            SubCategory, project=self.get_project(), pk=pk, category=category
        )
        form = SubCategoryForm(
            request.data, instance=subcategory, project=self.get_project()
        )

        if form.is_valid():
            form.instance.project = self.get_project()
            form.instance.category = category  # Ensure parent category stays the same
            subcategory = form.save()
            messages.success(
                request, f"Sub category '{subcategory.name}' updated successfully."
            )
            response_data = {
                "success": True,
                "id": subcategory.pk,
                "name": subcategory.name,
                "description": subcategory.description,
            }
            return Response(response_data, status=200)

        return Response(dict(form.errors), status=400)


class SubCategoryDeleteView(UserHasProjectRoleGenericMixin, APIView):
    """Delete a subcategory."""

    model = SubCategory
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_category(self):
        """Get the parent category from URL."""
        category_pk = self.kwargs.get("category_pk")
        return get_object_or_404(
            Category, pk=category_pk, project=self.get_project(), deleted=False
        )

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for deletion."""
        category = self.get_category()
        subcategory = get_object_or_404(
            SubCategory, project=self.get_project(), pk=pk, category=category
        )
        subcategory_name = subcategory.name

        subcategory.soft_delete()
        messages.success(request, f"Sub category '{subcategory_name}' deleted.")

        return Response({"success": True}, status=200)


class DisciplineListView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, ListView):
    """List all disciplines."""

    model = Discipline
    template_name = "project/discipline_manage.html"
    context_object_name = "disciplines"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title=f"Setup: {project.name}",
                url=reverse("project:project-setup", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(title="Disciplines", url=None),
        ]

    def get_queryset(self):
        """Return disciplines ordered by name."""
        return Discipline.objects.filter(
            project=self.get_project(), deleted=False
        ).order_by("name")


class DisciplineCreateView(
    UserHasProjectRoleGenericMixin,
    APIView,
):
    """Create a new discipline."""

    model = Discipline
    form_class = DisciplineForm
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, *args, **kwargs):
        """Handle POST request for discipline creation."""
        form = DisciplineForm(request.data)
        if form.is_valid():
            form.instance.project = self.get_project()
            discipline = form.save()
            messages.success(
                request, f"Discipline '{discipline.name}' created successfully."
            )
            response_data = {
                "success": True,
                "id": discipline.pk,
                "name": discipline.name,
                "description": discipline.description,
            }
            return Response(response_data, status=200)

        return Response(dict(form.errors), status=400)


class DisciplineUpdateView(
    UserHasProjectRoleGenericMixin,
    APIView,
):
    """Update a discipline."""

    model = Discipline
    form_class = DisciplineForm
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for discipline update."""
        discipline = get_object_or_404(Discipline, project=self.get_project(), pk=pk)
        form = DisciplineForm(request.data, instance=discipline)

        if form.is_valid():
            form.instance.project = self.get_project()
            discipline = form.save()
            messages.success(
                request, f"Discipline '{discipline.name}' updated successfully."
            )
            response_data = {
                "success": True,
                "id": discipline.pk,
                "name": discipline.name,
                "description": discipline.description,
            }
            return Response(response_data, status=200)

        return Response(dict(form.errors), status=400)


class DisciplineDeleteView(
    UserHasProjectRoleGenericMixin,
    APIView,
):
    """Delete a discipline."""

    model = Discipline
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for deletion."""
        discipline = get_object_or_404(Discipline, project=self.get_project(), pk=pk)
        discipline_name = discipline.name

        discipline.soft_delete()
        messages.success(request, f"Discipline '{discipline_name}' deleted.")

        return Response({"success": True}, status=200)


# Group Views
class GroupListView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, ListView):
    """List all groups for a specific subcategory."""

    model = Group
    template_name = "project/group_manage.html"
    context_object_name = "groups"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_subcategory(self):
        """Get the parent subcategory from URL."""
        subcategory_pk = self.kwargs.get("subcategory_pk")
        return get_object_or_404(
            SubCategory, pk=subcategory_pk, project=self.get_project(), deleted=False
        )

    def get_breadcrumbs(self):
        """Return breadcrumbs for the view."""
        project = self.get_project()
        subcategory = self.get_subcategory()
        category = subcategory.category
        return [
            BreadcrumbItem(
                title=f"Setup: {project.name}",
                url=reverse("project:project-setup", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Categories",
                url=reverse(
                    "project:project-category-list", kwargs={"project_pk": project.pk}
                ),
            ),
            BreadcrumbItem(
                title=f"{category.name} - Sub Categories",
                url=reverse(
                    "project:project-subcategory-list",
                    kwargs={"project_pk": project.pk, "category_pk": category.pk},
                ),
            ),
            BreadcrumbItem(title=f"{subcategory.name} - Groups", url=None),
        ]

    def get_queryset(self):
        """Return groups for the parent subcategory."""
        subcategory = self.get_subcategory()
        return Group.objects.filter(
            sub_category=subcategory, project=self.get_project(), deleted=False
        ).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subcategory = self.get_subcategory()
        context["subcategory"] = subcategory
        context["group_form"] = GroupForm(project=self.get_project())
        return context


class GroupCreateView(
    UserHasProjectRoleGenericMixin,
    APIView,
):
    """Create a new group."""

    model = Group
    form_class = GroupForm
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_subcategory(self):
        """Get the parent subcategory from URL."""
        subcategory_pk = self.kwargs.get("subcategory_pk")
        return get_object_or_404(
            SubCategory, pk=subcategory_pk, project=self.get_project(), deleted=False
        )

    def post(self, request, *args, **kwargs):
        """Handle POST request for group creation."""
        form = GroupForm(request.data, project=self.get_project())
        if form.is_valid():
            form.instance.project = self.get_project()
            form.instance.sub_category = (
                self.get_subcategory()
            )  # Auto-fill parent subcategory
            group = form.save()
            messages.success(request, f"Group '{group.name}' created successfully.")
            response_data = {
                "success": True,
                "id": group.pk,
                "name": group.name,
                "description": group.description,
            }
            return Response(response_data, status=200)

        return Response(dict(form.errors), status=400)


class GroupUpdateView(
    UserHasProjectRoleGenericMixin,
    APIView,
):
    """Update a group."""

    model = Group
    form_class = GroupForm
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_subcategory(self):
        """Get the parent subcategory from URL."""
        subcategory_pk = self.kwargs.get("subcategory_pk")
        return get_object_or_404(
            SubCategory, pk=subcategory_pk, project=self.get_project(), deleted=False
        )

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for group update."""
        subcategory = self.get_subcategory()
        group = get_object_or_404(
            Group, project=self.get_project(), pk=pk, sub_category=subcategory
        )
        form = GroupForm(request.data, instance=group, project=self.get_project())

        if form.is_valid():
            form.instance.project = self.get_project()
            form.instance.sub_category = (
                subcategory  # Ensure parent subcategory stays the same
            )
            group = form.save()
            messages.success(request, f"Group '{group.name}' updated successfully.")
            response_data = {
                "success": True,
                "id": group.pk,
                "name": group.name,
                "description": group.description,
            }
            return Response(response_data, status=200)

        return Response(dict(form.errors), status=400)


class GroupDeleteView(
    UserHasProjectRoleGenericMixin,
    APIView,
):
    """Delete a group."""

    model = Group
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_subcategory(self):
        """Get the parent subcategory from URL."""
        subcategory_pk = self.kwargs.get("subcategory_pk")
        return get_object_or_404(
            SubCategory, pk=subcategory_pk, project=self.get_project(), deleted=False
        )

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for deletion."""
        subcategory = self.get_subcategory()
        group = get_object_or_404(
            Group, project=self.get_project(), pk=pk, sub_category=subcategory
        )
        group_name = group.name

        group.soft_delete()
        messages.success(request, f"Group '{group_name}' deleted.")

        return Response({"success": True}, status=200)
