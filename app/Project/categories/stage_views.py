"""Views for Project Stage management."""

from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import ProjectStage

from .category_forms import ProjectStageForm


class ProjectStageListView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """List all project stages."""

    model = ProjectStage
    template_name = "categories/stage_manage.html"
    context_object_name = "stages"
    permissions = ["contractor", "consultant"]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(title="Project Stages", url=None),
        ]

    def get_queryset(self):
        return ProjectStage.objects.all().order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ProjectStageForm()
        return context


class ProjectStageCreateView(UserHasGroupGenericMixin, BreadcrumbMixin, CreateView):
    """Create a new project stage."""

    model = ProjectStage
    form_class = ProjectStageForm
    template_name = "categories/stage_form.html"
    permissions = ["contractor", "consultant"]
    success_url = reverse_lazy("project:project-stage-list")

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Project Stages", url=reverse("project:project-stage-list")
            ),
            BreadcrumbItem(title="Add Project Stage", url=None),
        ]

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


class ProjectStageUpdateView(UserHasGroupGenericMixin, BreadcrumbMixin, UpdateView):
    """Update a project stage."""

    model = ProjectStage
    form_class = ProjectStageForm
    template_name = "categories/stage_form.html"
    permissions = ["contractor", "consultant"]
    success_url = reverse_lazy("project:project-stage-list")

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Project Stages", url=reverse("project:project-stage-list")
            ),
            BreadcrumbItem(title="Edit Project Stage", url=None),
        ]

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


class ProjectStageDeleteView(UserHasGroupGenericMixin, BreadcrumbMixin, DeleteView):
    """Delete a project stage."""

    model = ProjectStage
    template_name = "categories/stage_confirm_delete.html"
    permissions = ["contractor", "consultant"]
    success_url = reverse_lazy("project:project-stage-list")

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title="Project Stages", url=reverse("project:project-stage-list")
            ),
            BreadcrumbItem(title="Delete Project Stage", url=None),
        ]

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

        from django.shortcuts import redirect

        return redirect("project:project-stage-list")
