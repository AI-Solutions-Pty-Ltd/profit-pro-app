"""Delete views for design files."""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Planning.models import (
    DesignCategoryFile,
    DesignDisciplineFile,
    DesignGroupFile,
    DesignSubCategoryFile,
)
from app.Project.models import Project, Role


class PlanningFileMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Base mixin for file delete views."""

    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        """Get the project from the URL kwargs."""
        return Project.objects.get(pk=self.kwargs["project_pk"])


class DesignCategoryFileDeleteView(PlanningFileMixin, APIView):
    """Delete a design category file."""

    model = DesignCategoryFile

    def delete(self, request, pk, *args, **kwargs):
        self.object = get_object_or_404(
            DesignCategoryFile,
            pk=pk,
            design_category__category__project=self.get_project(),
        )
        self.object.delete()
        messages.success(request, "File deleted successfully.")
        return JsonResponse({"success": True})


class DesignSubCategoryFileDeleteView(PlanningFileMixin, APIView):
    """Delete a design subcategory file."""

    model = DesignSubCategoryFile

    def delete(self, request, pk, *args, **kwargs):
        self.object = get_object_or_404(
            DesignSubCategoryFile,
            pk=pk,
            design_sub_category__sub_category__category__project=self.get_project(),
        )
        self.object.delete()
        messages.success(request, "File deleted successfully.")
        return JsonResponse({"success": True})


class DesignGroupFileDeleteView(PlanningFileMixin, APIView):
    """Delete a design group file."""

    model = DesignGroupFile

    def delete(self, request, pk, *args, **kwargs):
        self.object = get_object_or_404(
            DesignGroupFile,
            pk=pk,
            design_group__group__sub_category__category__project=self.get_project(),
        )
        self.object.delete()
        messages.success(request, "File deleted successfully.")
        return JsonResponse({"success": True})


class DesignDisciplineFileDeleteView(PlanningFileMixin, APIView):
    """Delete a design discipline file."""

    model = DesignDisciplineFile

    def delete(self, request, pk, *args, **kwargs):
        self.object = get_object_or_404(
            DesignDisciplineFile,
            pk=pk,
            design_discipline__discipline__project=self.get_project(),
        )
        self.object.delete()
        messages.success(request, "File deleted successfully.")
        return JsonResponse({"success": True})
