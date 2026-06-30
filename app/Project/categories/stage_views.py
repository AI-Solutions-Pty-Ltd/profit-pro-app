"""Views for Project Stage management."""

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.views.generic.base import ContextMixin

from app.Project.models import ProjectStage

from .category_forms import ProjectStageForm


class SystemLibraryMixin(UserPassesTestMixin, ContextMixin):
    """Mixin for system library views: requires staff."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_system_view"] = True
        return context


class ProjectStageListView(SystemLibraryMixin, ListView):
    """List all project stages."""

    model = ProjectStage
    template_name = "estimator/system/stage_manage.html"
    context_object_name = "stages"

    def get_queryset(self):
        return ProjectStage.objects.all().order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ProjectStageForm()
        return context


class ProjectStageCreateView(SystemLibraryMixin, CreateView):
    """Create a new project stage."""

    model = ProjectStage
    form_class = ProjectStageForm
    template_name = "estimator/system/stage_form.html"
    success_url = reverse_lazy("estimator:sys_project_stages")

    def form_valid(self, form):
        self.object: ProjectStage = form.save()
        messages.success(
            self.request,
            f"Project stage '{self.object.name}' created successfully.",
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
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)


class ProjectStageUpdateView(SystemLibraryMixin, UpdateView):
    """Update a project stage."""

    model = ProjectStage
    form_class = ProjectStageForm
    template_name = "estimator/system/stage_form.html"
    success_url = reverse_lazy("estimator:sys_project_stages")

    def form_valid(self, form):
        self.object = form.save()
        messages.success(
            self.request,
            f"Project stage '{self.object.name}' updated successfully.",
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
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)


class ProjectStageDeleteView(SystemLibraryMixin, DeleteView):
    """Delete a project stage."""

    model = ProjectStage
    template_name = "estimator/system/stage_confirm_delete.html"
    success_url = reverse_lazy("estimator:sys_project_stages")

    def form_valid(self, form):
        stage_name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, f"Project stage '{stage_name}' deleted.")

        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return response

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        stage_name = self.object.name

        self.object.soft_delete()
        messages.success(request, f"Project stage '{stage_name}' deleted.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return self.get_success_url()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        stage_name = self.object.name

        self.object.soft_delete()
        messages.success(request, f"Project stage '{stage_name}' deleted.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return redirect("estimator:sys_project_stages")
