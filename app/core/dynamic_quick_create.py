from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views import View

from app.Project.forms.unit_forms import UnitOfMeasureForm
from app.Project.models import Project
from app.Project.models.unit_models import UnitOfMeasure
from app.SiteManagement.forms.resource_forms import PlantTypeForm, SkillTypeForm
from app.SiteManagement.models.plant_type import PlantType
from app.SiteManagement.models.skill_type import SkillType


class QuickCreateRegistry:
    """Registry to map resource types to their core models and forms."""

    REGISTRY = {
        "unit_of_measure": {
            "model": UnitOfMeasure,
            "form_class": UnitOfMeasureForm,
            "title": "New Unit of Measure",
            "needs_project": False,
        },
        "skill_type": {
            "model": SkillType,
            "form_class": SkillTypeForm,
            "title": "New Skill Type",
            "needs_project": True,
        },
        "plant_type": {
            "model": PlantType,
            "form_class": PlantTypeForm,
            "title": "New Plant Type",
            "needs_project": True,
        },
    }

    @classmethod
    def get(cls, resource_type):
        return cls.REGISTRY.get(resource_type)


class QuickCreateFormView(LoginRequiredMixin, View):
    """Returns the rendered HTML of a form for the specified resource type."""

    def get(self, request, *args, **kwargs):
        resource_type = request.GET.get("resource_type")
        config = QuickCreateRegistry.get(resource_type)

        if not config:
            return JsonResponse({"error": "Invalid resource type"}, status=400)

        form = config["form_class"]()
        html = render_to_string(
            "modals/partials/generic_form_fields.html",
            {"form": form, "resource_type": resource_type, "title": config["title"]},
            request=request,
        )

        return JsonResponse(
            {
                "html": html,
                "title": config["title"],
            }
        )


class QuickCreateSubmitView(LoginRequiredMixin, View):
    """Handles the AJAX submission for any supported quick-create resource."""

    def post(self, request, *args, **kwargs):
        resource_type = request.POST.get("resource_type")
        project_pk = request.POST.get("project_pk")
        config = QuickCreateRegistry.get(resource_type)

        if not config:
            return JsonResponse({"error": "Invalid resource type"}, status=400)

        form = config["form_class"](request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    instance = form.save(commit=False)
                    if config["needs_project"]:
                        project = get_object_or_404(Project, pk=project_pk)
                        instance.project = project
                    instance.save()

                    # Return formatted response for the select widget
                    # __str__ usually provides the best label, but we can customize
                    return JsonResponse(
                        {
                            "success": True,
                            "id": instance.id,
                            "name": str(instance),
                        }
                    )
            except Exception as e:
                return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}})

        return JsonResponse({"success": False, "errors": form.errors})
