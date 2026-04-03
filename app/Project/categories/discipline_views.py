"""Views for Project Discipline management."""

from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import ProjectDiscipline

from .category_forms import ProjectDisciplineForm


class ProjectDisciplineListView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """List all project disciplines."""

    model = ProjectDiscipline
    template_name = "categories/discipline_manage.html"
    context_object_name = "disciplines"
    permissions = ["contractor", "consultant"]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(title="Project Disciplines", url=None),
        ]

    def get_queryset(self):
        """Return disciplines ordered by name."""
        return ProjectDiscipline.objects.all().order_by("name")

    def get_context_data(self, **kwargs):
        """Add form for inline creation."""
        context = super().get_context_data(**kwargs)
        context["form"] = ProjectDisciplineForm()
        return context


class ProjectDisciplineCreateView(
    UserHasGroupGenericMixin, BreadcrumbMixin, CreateView
):
    """Create a new project discipline."""

    model = ProjectDiscipline
    form_class = ProjectDisciplineForm
    template_name = "categories/discipline_form.html"
    permissions = ["contractor", "consultant"]
    success_url = reverse_lazy("project:discipline-list")

    def get_breadcrumbs(self: "ProjectDisciplineCreateView") -> list[BreadcrumbItem]:
        return [
            {"title": "Portfolio", "url": reverse("project:portfolio-dashboard")},
            {"title": "Project Disciplines", "url": reverse("project:discipline-list")},
            {"title": "Add Discipline", "url": None},
        ]

    def form_valid(self: "ProjectDisciplineCreateView", form):
        """Handle successful form submission."""
        self.object: ProjectDiscipline = form.save()

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


class ProjectDisciplineUpdateView(
    UserHasGroupGenericMixin, BreadcrumbMixin, UpdateView
):
    """Update a project discipline."""

    model = ProjectDiscipline
    form_class = ProjectDisciplineForm
    template_name = "categories/discipline_form.html"
    permissions = ["contractor", "consultant"]
    success_url = reverse_lazy("project:discipline-list")

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Project Disciplines", url=reverse("project:discipline-list")
            ),
            BreadcrumbItem(title="Edit Discipline", url=None),
        ]

    def form_valid(self, form):
        """Handle successful form submission."""
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


class ProjectDisciplineDeleteView(
    UserHasGroupGenericMixin, BreadcrumbMixin, DeleteView
):
    """Delete a project discipline."""

    model = ProjectDiscipline
    template_name = "categories/discipline_confirm_delete.html"
    permissions = ["contractor", "consultant"]
    success_url = reverse_lazy("project:discipline-list")

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Project Disciplines", url=reverse("project:discipline-list")
            ),
            BreadcrumbItem(title="Delete Discipline", url=None),
        ]

    def form_valid(self, form):
        """Handle successful deletion."""
        discipline_name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, f"Discipline '{discipline_name}' deleted.")

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return response

    def delete(self, request, *args, **kwargs):
        """Handle DELETE request (soft delete)."""
        self.object = self.get_object()
        discipline_name = self.object.name

        self.object.soft_delete()
        messages.success(request, f"Discipline '{discipline_name}' deleted.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return self.get_success_url()

    def post(self, request, *args, **kwargs):
        """Handle POST request for deletion."""
        self.object = self.get_object()
        discipline_name = self.object.name

        self.object.soft_delete()
        messages.success(request, f"Discipline '{discipline_name}' deleted.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        from django.shortcuts import redirect

        return redirect("project:discipline-list")
