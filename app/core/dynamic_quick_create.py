from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views import View

# We import Project here as it is a core dependency for the submission view,
# but individual resource models/forms will be registered dynamically.
from app.Project.models import Project


class QuickCreateRegistry:
    """
    Registry to map resource types to their models and forms dynamically.
    Enables scaling to many resource types without bloating core views.
    """

    def __init__(self):
        self._registry = {}

    def register(self, resource_type, model, form_class, title, needs_project=False):
        """
        Register a new resource type.

        Args:
            resource_type (str): Unique slug for the resource.
            model (Model): Django model class.
            form_class (Form): Django form class.
            title (str): Display title for the modal.
            needs_project (bool): Whether the model requires a 'project' association.
        """
        self._registry[resource_type] = {
            "model": model,
            "form_class": form_class,
            "title": title,
            "needs_project": needs_project,
        }

    def get(self, resource_type):
        """Retrieve configuration for a resource type."""
        return self._registry.get(resource_type)


# Global singleton instance
registry = QuickCreateRegistry()


class QuickCreateFormView(LoginRequiredMixin, View):
    """Returns the rendered HTML of a form for the specified resource type."""

    def get(self, request, *args, **kwargs):
        resource_type = request.GET.get("resource_type")
        config = registry.get(resource_type)

        if not config:
            return JsonResponse(
                {"error": f"Invalid resource type: {resource_type}"}, status=400
            )

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
    """Handles the AJAX submission for any dynamically registered quick-create resource."""

    def post(self, request, *args, **kwargs):
        resource_type = request.POST.get("resource_type")
        project_pk = request.POST.get("project_pk")
        config = registry.get(resource_type)

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
