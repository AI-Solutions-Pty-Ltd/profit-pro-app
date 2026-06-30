"""Views for Project Discipline management."""

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.views.generic.base import ContextMixin

from app.Project.models import ProjectDiscipline

from .category_forms import ProjectDisciplineForm


class SystemLibraryMixin(UserPassesTestMixin, ContextMixin):
    """Mixin for system library views: requires staff."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_system_view"] = True
        return context


class ProjectDisciplineListView(SystemLibraryMixin, ListView):
    """List all project disciplines."""

    model = ProjectDiscipline
    template_name = "estimator/system/discipline_manage.html"
    context_object_name = "disciplines"

    def get_queryset(self):
        """Return disciplines ordered by name."""
        return ProjectDiscipline.objects.all().order_by("name")

    def get_context_data(self, **kwargs):
        """Add form for inline creation."""
        context = super().get_context_data(**kwargs)
        context["form"] = ProjectDisciplineForm()
        return context


class ProjectDisciplineCreateView(SystemLibraryMixin, CreateView):
    """Create a new project discipline."""

    model = ProjectDiscipline
    form_class = ProjectDisciplineForm
    template_name = "estimator/system/discipline_form.html"
    success_url = reverse_lazy("estimator:sys_disciplines")

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


class ProjectDisciplineUpdateView(SystemLibraryMixin, UpdateView):
    """Update a project discipline."""

    model = ProjectDiscipline
    form_class = ProjectDisciplineForm
    template_name = "estimator/system/discipline_form.html"
    success_url = reverse_lazy("estimator:sys_disciplines")

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


class ProjectDisciplineDeleteView(SystemLibraryMixin, DeleteView):
    """Delete a project discipline."""

    model = ProjectDiscipline
    template_name = "estimator/system/discipline_confirm_delete.html"
    success_url = reverse_lazy("estimator:sys_disciplines")

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

        return redirect("estimator:sys_disciplines")
