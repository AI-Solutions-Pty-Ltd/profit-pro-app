"""Views for Category, SubCategory, and Discipline management."""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
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
    View,
):
    """Create a new category."""

    model = Category
    form_class = CategoryForm
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, *args, **kwargs):
        """Handle POST request for category creation."""
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.instance.project = self.get_project()
            category = form.save()
            messages.success(
                request, f"Category '{category.name}' created successfully."
            )

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "id": category.pk,
                        "name": category.name,
                        "description": category.description,
                    }
                )
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "errors": form.errors}, status=400
                )

        return redirect(
            "project:project-category-list", project_pk=self.get_project().pk
        )


class CategoryUpdateView(
    UserHasProjectRoleGenericMixin,
    View,
):
    """Update a category."""

    model = Category
    form_class = CategoryForm
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for category update."""
        category = get_object_or_404(Category, project=self.get_project(), pk=pk)
        form = CategoryForm(request.POST, instance=category)

        if form.is_valid():
            form.instance.project = self.get_project()
            category = form.save()
            messages.success(
                request, f"Category '{category.name}' updated successfully."
            )

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "id": category.pk,
                        "name": category.name,
                        "description": category.description,
                    }
                )
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "errors": form.errors}, status=400
                )

        return redirect(
            "project:project-category-list", project_pk=self.get_project().pk
        )


class CategoryDeleteView(
    UserHasProjectRoleGenericMixin,
    View,
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

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return redirect(
            "project:project-category-list", project_pk=self.get_project().pk
        )


class SubCategoryListView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, ListView):
    """List all subcategories."""

    model = SubCategory
    template_name = "project/subcategory_manage.html"
    context_object_name = "subcategories"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title=f"Setup: {project.name}",
                url=reverse("project:project-setup", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(title="Sub Categories", url=None),
        ]

    def get_queryset(self):
        """Return subcategories ordered by name."""
        return SubCategory.objects.filter(
            project=self.get_project(), deleted=False
        ).order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subcategory_form"] = SubCategoryForm(project=self.get_project())
        return context


class SubCategoryCreateView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, View):
    """Handle subcategory creation via POST."""

    model = SubCategory
    template_name = "project/subcategory_manage.html"
    context_object_name = "subcategories"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, *args, **kwargs):
        """Handle POST request for subcategory creation."""
        form = SubCategoryForm(request.POST, project=self.get_project())
        if form.is_valid():
            form.instance.project = self.get_project()
            subcategory = form.save()
            messages.success(
                request, f"Sub category '{subcategory.name}' created successfully."
            )

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "id": subcategory.pk,
                        "name": subcategory.name,
                        "description": subcategory.description,
                    }
                )
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "errors": form.errors}, status=400
                )

        return redirect(
            "project:project-subcategory-list", project_pk=self.get_project().pk
        )


class SubCategoryUpdateView(UserHasProjectRoleGenericMixin, View):
    """Handle subcategory update via POST."""

    model = SubCategory
    context_object_name = "subcategories"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for subcategory update."""
        subcategory = get_object_or_404(SubCategory, project=self.get_project(), pk=pk)
        form = SubCategoryForm(
            request.POST, instance=subcategory, project=self.get_project()
        )

        if form.is_valid():
            form.instance.project = self.get_project()
            subcategory = form.save()
            messages.success(
                request, f"Sub category '{subcategory.name}' updated successfully."
            )

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "id": subcategory.pk,
                        "name": subcategory.name,
                        "description": subcategory.description,
                    }
                )
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "errors": form.errors}, status=400
                )

        return redirect(
            "project:project-subcategory-list", project_pk=self.get_project().pk
        )


class SubCategoryDeleteView(UserHasProjectRoleGenericMixin, View):
    """Delete a subcategory."""

    model = SubCategory
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for deletion."""
        subcategory = get_object_or_404(SubCategory, project=self.get_project(), pk=pk)
        subcategory_name = subcategory.name

        subcategory.soft_delete()
        messages.success(request, f"Sub category '{subcategory_name}' deleted.")

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return redirect(
            "project:project-subcategory-list", project_pk=self.get_project().pk
        )


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
    View,
):
    """Create a new discipline."""

    model = Discipline
    form_class = DisciplineForm
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, *args, **kwargs):
        """Handle POST request for discipline creation."""
        form = DisciplineForm(request.POST)
        if form.is_valid():
            form.instance.project = self.get_project()
            discipline = form.save()
            messages.success(
                request, f"Discipline '{discipline.name}' created successfully."
            )

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "id": discipline.pk,
                        "name": discipline.name,
                        "description": discipline.description,
                    }
                )
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "errors": form.errors}, status=400
                )

        return redirect(
            "project:project-discipline-list", project_pk=self.get_project().pk
        )


class DisciplineUpdateView(
    UserHasProjectRoleGenericMixin,
    View,
):
    """Update a discipline."""

    model = Discipline
    form_class = DisciplineForm
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for discipline update."""
        discipline = get_object_or_404(Discipline, project=self.get_project(), pk=pk)
        form = DisciplineForm(request.POST, instance=discipline)

        if form.is_valid():
            form.instance.project = self.get_project()
            discipline = form.save()
            messages.success(
                request, f"Discipline '{discipline.name}' updated successfully."
            )

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "id": discipline.pk,
                        "name": discipline.name,
                        "description": discipline.description,
                    }
                )
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "errors": form.errors}, status=400
                )

        return redirect(
            "project:project-discipline-list", project_pk=self.get_project().pk
        )


class DisciplineDeleteView(
    UserHasProjectRoleGenericMixin,
    View,
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

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return redirect(
            "project:project-discipline-list", project_pk=self.get_project().pk
        )


# Group Views
class GroupListView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, ListView):
    """List all groups."""

    model = Group
    template_name = "project/group_manage.html"
    context_object_name = "groups"
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_breadcrumbs(self):
        """Return breadcrumbs for the view."""
        project = self.get_project()
        return [
            BreadcrumbItem(
                title=f"Setup: {project.name}",
                url=reverse("project:project-setup", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(title="Groups", url=None),
        ]

    def get_queryset(self):
        """Return groups ordered by name."""
        return Group.objects.filter(project=self.get_project(), deleted=False).order_by(
            "name"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["group_form"] = GroupForm(project=self.get_project())
        return context


class GroupCreateView(
    UserHasProjectRoleGenericMixin,
    View,
):
    """Create a new group."""

    model = Group
    form_class = GroupForm
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, *args, **kwargs):
        """Handle POST request for group creation."""
        form = GroupForm(request.POST, project=self.get_project())
        if form.is_valid():
            form.instance.project = self.get_project()
            group = form.save()
            messages.success(request, f"Group '{group.name}' created successfully.")

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "id": group.pk,
                        "name": group.name,
                        "description": group.description,
                    }
                )
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "errors": form.errors}, status=400
                )

        return redirect("project:project-group-list", project_pk=self.get_project().pk)


class GroupUpdateView(
    UserHasProjectRoleGenericMixin,
    View,
):
    """Update a group."""

    model = Group
    form_class = GroupForm
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for group update."""
        group = get_object_or_404(Group, project=self.get_project(), pk=pk)
        form = GroupForm(request.POST, instance=group, project=self.get_project())

        if form.is_valid():
            form.instance.project = self.get_project()
            group = form.save()
            messages.success(request, f"Group '{group.name}' updated successfully.")

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": True,
                        "id": group.pk,
                        "name": group.name,
                        "description": group.description,
                    }
                )
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": False, "errors": form.errors}, status=400
                )

        return redirect("project:project-group-list", project_pk=self.get_project().pk)


class GroupDeleteView(
    UserHasProjectRoleGenericMixin,
    View,
):
    """Delete a group."""

    model = Group
    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def post(self, request, pk, *args, **kwargs):
        """Handle POST request for deletion."""
        group = get_object_or_404(Group, project=self.get_project(), pk=pk)
        group_name = group.name

        group.soft_delete()
        messages.success(request, f"Group '{group_name}' deleted.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return redirect("project:project-group-list", project_pk=self.get_project().pk)
