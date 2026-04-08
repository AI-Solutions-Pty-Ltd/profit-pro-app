import json

from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView,
)

from app.core.Utilities.mixins import BreadcrumbItem
from app.Planning.models import (
    WorkPackage,
)
from app.Planning.views import PlanningMixin


class TenderProcessSectionCompleteAPIView(PlanningMixin, View):
    """Update completion state for a tender process section on a work package."""

    section_to_field = {
        "applied_to_advert": "applied_to_advert_completed",
        "site_inspection": "site_inspection_completed",
        "tender_close": "tender_close_completed",
        "tender_evaluation": "tender_evaluation_completed",
        "award": "award_completed",
        "contract_signing": "contract_signing_completed",
        "mobilization": "mobilization_completed",
    }

    @staticmethod
    def _to_bool(value: str | bool | None) -> bool | None:
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
        return None

    def post(self, request, project_pk: int, wp_pk: int):
        project = self.get_project()
        work_package = WorkPackage.objects.filter(project=project, pk=wp_pk).first()
        if work_package is None:
            return JsonResponse(
                {"success": False, "message": "Work package not found."}, status=404
            )

        payload: dict[str, str | bool | None] = {}
        if (request.content_type or "").startswith("application/json"):
            try:
                payload = json.loads(request.body or "{}")
            except json.JSONDecodeError:
                return JsonResponse(
                    {"success": False, "message": "Invalid JSON payload."},
                    status=400,
                )

        section = str(payload.get("section") or request.POST.get("section") or "")
        section = section.strip().lower()
        if section not in self.section_to_field:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Invalid section.",
                    "allowed_sections": sorted(self.section_to_field.keys()),
                },
                status=400,
            )

        requested_completed = payload.get("completed")
        if requested_completed is None:
            requested_completed = request.POST.get("completed")

        completed = self._to_bool(requested_completed)
        field_name = self.section_to_field[section]
        current_value = bool(getattr(work_package, field_name))
        next_value = (not current_value) if completed is None else completed

        setattr(work_package, field_name, next_value)
        work_package.save(update_fields=[field_name])

        statuses = {
            key: bool(getattr(work_package, value))
            for key, value in self.section_to_field.items()
        }
        return JsonResponse(
            {
                "success": True,
                "message": "Section completion updated.",
                "work_package_id": work_package.pk,
                "section": section,
                "completed": next_value,
                "statuses": statuses,
            }
        )


class TenderProcessOverviewView(PlanningMixin, ListView):
    """Overview of tender process timeline across all work packages in a project."""

    model = WorkPackage
    template_name = "planning/overview/tender_process.html"
    context_object_name = "work_packages"

    def get_queryset(self):
        project = self.get_project()
        return WorkPackage.objects.filter(project=project).order_by(
            "applied_to_advert_start_date"
        )

    def get_breadcrumbs(self):
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects",
                url=str(reverse_lazy("project:project-list")),
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(reverse_lazy("project:project-management", args=[project.pk])),
            ),
            BreadcrumbItem(title="Tender Process Overview", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
