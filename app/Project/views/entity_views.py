"""Views for Project Entity Management."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.forms.entity_forms import (
    LabourEntityForm,
    MaterialEntityForm,
    MaterialHeaderForm,
    MaterialItemFormSet,
    OverheadEntityForm,
    PlantEntityForm,
    SubcontractorEntityForm,
)
from app.Project.models import Project
from app.Project.models.entity_definitions import (
    LabourEntity,
    MaterialEntity,
    OverheadEntity,
    PlantEntity,
    SubcontractorEntity,
)


class ProjectEntityMixin(LoginRequiredMixin):
    """Mixin for scoped project entity views."""

    project: Project
    entity_name: str
    entity_type: str

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.get("project_pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(project=self.project)  # type: ignore

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # type: ignore
        context["project"] = self.project
        context["entity_name"] = self.entity_name
        context["entity_type"] = self.entity_type
        # Add a flag to identify the entity type in the template if needed
        context[f"is_{self.entity_type}"] = True
        return context

    def form_valid(self, form):
        if hasattr(form, "instance"):
            form.instance.project = self.project
        return super().form_valid(form)  # type: ignore

    def get_success_url(self):
        """Redirect to the list view of the current entity type."""
        return reverse(
            f"project:entity-{self.entity_type}-list",
            kwargs={"project_pk": self.project.pk},
        )


# ==========================================
# Labour Views
# ==========================================


class LabourEntityListView(ProjectEntityMixin, ListView):
    model = LabourEntity
    template_name = "entity_management/list.html"
    entity_name = "Labour"
    entity_type = "labour"
    context_object_name = "entities"


class LabourEntityCreateView(ProjectEntityMixin, CreateView):
    model = LabourEntity
    form_class = LabourEntityForm
    template_name = "entity_management/form.html"
    entity_name = "Labour"
    entity_type = "labour"


class LabourEntityUpdateView(ProjectEntityMixin, UpdateView):
    model = LabourEntity
    form_class = LabourEntityForm
    template_name = "entity_management/form.html"
    entity_name = "Labour"
    entity_type = "labour"


class LabourEntityDeleteView(ProjectEntityMixin, DeleteView):
    model = LabourEntity
    template_name = "entity_management/confirm_delete.html"
    entity_name = "Labour"
    entity_type = "labour"


# ==========================================
# Material Views
# ==========================================


class MaterialEntityListView(ProjectEntityMixin, ListView):
    model = MaterialEntity
    template_name = "entity_management/list.html"
    entity_name = "Material"
    entity_type = "material"
    context_object_name = "entities"


class MaterialEntityCreateView(ProjectEntityMixin, CreateView):
    model = MaterialEntity
    form_class = MaterialHeaderForm  # Use header form as primary for validation
    template_name = "entity_management/material_bulk_form.html"
    entity_name = "Material"
    entity_type = "material"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "header_form" in kwargs:
            context["header_form"] = kwargs["header_form"]
        elif self.request.POST:
            context["header_form"] = MaterialHeaderForm(
                self.request.POST, self.request.FILES
            )
        else:
            context["header_form"] = MaterialHeaderForm()

        if "formset" in kwargs:
            context["formset"] = kwargs["formset"]
        elif self.request.POST:
            context["formset"] = MaterialItemFormSet(
                self.request.POST, queryset=MaterialEntity.objects.none()
            )
        else:
            context["formset"] = MaterialItemFormSet(
                queryset=MaterialEntity.objects.none()
            )
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        header_form = MaterialHeaderForm(request.POST, request.FILES)
        formset = MaterialItemFormSet(request.POST)

        if header_form.is_valid() and formset.is_valid():
            return self.formset_valid(header_form, formset)
        else:
            return self.render_to_response(
                self.get_context_data(header_form=header_form, formset=formset)
            )

    def formset_valid(self, header_form, formset):
        supplier = header_form.cleaned_data["supplier"]
        invoice_number = header_form.cleaned_data["invoice_number"]
        date_received = header_form.cleaned_data["date_received"]
        invoice_attachment = header_form.cleaned_data.get("invoice_attachment")

        instances = formset.save(commit=False)
        for instance in instances:
            instance.project = self.project
            instance.supplier = supplier
            instance.invoice_number = invoice_number
            instance.date_received = date_received
            if invoice_attachment:
                instance.invoice_attachment = invoice_attachment
            instance.save()

        # Handle deletions if any (though usually not in a pure CreateView)
        for obj in formset.deleted_objects:
            obj.delete()

        # We return HttpResponseRedirect instead of calling super().form_valid(header_form)
        # to avoid CreateView potentially saving the header form as a separate MaterialEntity
        from django.http import HttpResponseRedirect

        return HttpResponseRedirect(self.get_success_url())


class MaterialEntityUpdateView(ProjectEntityMixin, UpdateView):
    model = MaterialEntity
    form_class = MaterialEntityForm
    template_name = "entity_management/form.html"
    entity_name = "Material"
    entity_type = "material"


class MaterialEntityDeleteView(ProjectEntityMixin, DeleteView):
    model = MaterialEntity
    template_name = "entity_management/confirm_delete.html"
    entity_name = "Material"
    entity_type = "material"


# ==========================================
# Plant Views
# ==========================================


class PlantEntityListView(ProjectEntityMixin, ListView):
    model = PlantEntity
    template_name = "entity_management/list.html"
    entity_name = "Plant & Equipment"
    entity_type = "plant"
    context_object_name = "entities"


class PlantEntityCreateView(ProjectEntityMixin, CreateView):
    model = PlantEntity
    form_class = PlantEntityForm
    template_name = "entity_management/form.html"
    entity_name = "Plant & Equipment"
    entity_type = "plant"


class PlantEntityUpdateView(ProjectEntityMixin, UpdateView):
    model = PlantEntity
    form_class = PlantEntityForm
    template_name = "entity_management/form.html"
    entity_name = "Plant & Equipment"
    entity_type = "plant"


class PlantEntityDeleteView(ProjectEntityMixin, DeleteView):
    model = PlantEntity
    template_name = "entity_management/confirm_delete.html"
    entity_name = "Plant & Equipment"
    entity_type = "plant"


# ==========================================
# Subcontractor Views
# ==========================================


class SubcontractorEntityListView(ProjectEntityMixin, ListView):
    model = SubcontractorEntity
    template_name = "entity_management/list.html"
    entity_name = "Subcontractor"
    entity_type = "subcontractor"
    context_object_name = "entities"


class SubcontractorEntityCreateView(ProjectEntityMixin, CreateView):
    model = SubcontractorEntity
    form_class = SubcontractorEntityForm
    template_name = "entity_management/form.html"
    entity_name = "Subcontractor"
    entity_type = "subcontractor"


class SubcontractorEntityUpdateView(ProjectEntityMixin, UpdateView):
    model = SubcontractorEntity
    form_class = SubcontractorEntityForm
    template_name = "entity_management/form.html"
    entity_name = "Subcontractor"
    entity_type = "subcontractor"


class SubcontractorEntityDeleteView(ProjectEntityMixin, DeleteView):
    model = SubcontractorEntity
    template_name = "entity_management/confirm_delete.html"
    entity_name = "Subcontractor"
    entity_type = "subcontractor"


# ==========================================
# Overhead Views
# ==========================================


class OverheadEntityListView(ProjectEntityMixin, ListView):
    model = OverheadEntity
    template_name = "entity_management/list.html"
    entity_name = "Overhead"
    entity_type = "overhead"
    context_object_name = "entities"


class OverheadEntityCreateView(ProjectEntityMixin, CreateView):
    model = OverheadEntity
    form_class = OverheadEntityForm
    template_name = "entity_management/form.html"
    entity_name = "Overhead"
    entity_type = "overhead"


class OverheadEntityUpdateView(ProjectEntityMixin, UpdateView):
    model = OverheadEntity
    form_class = OverheadEntityForm
    template_name = "entity_management/form.html"
    entity_name = "Overhead"
    entity_type = "overhead"


class OverheadEntityDeleteView(ProjectEntityMixin, DeleteView):
    model = OverheadEntity
    template_name = "entity_management/confirm_delete.html"
    entity_name = "Overhead"
    entity_type = "overhead"


# ==========================================
# API Views
# ==========================================


class EntityDetailView(LoginRequiredMixin, View):
    """API view to return entity details as JSON for auto-filling site logs."""

    def get(self, request, *args, **kwargs):
        entity_type = kwargs.get("entity_type", "")
        pk = kwargs.get("pk")
        project_pk = kwargs.get("project_pk")

        if not pk or not project_pk:
            return JsonResponse({"error": "Missing parameters"}, status=400)

        models_map = {
            "labour": LabourEntity,
            "material": MaterialEntity,
            "plant": PlantEntity,
            "subcontractor": SubcontractorEntity,
            "overhead": OverheadEntity,
        }

        model = models_map.get(str(entity_type))
        if not model:
            return JsonResponse({"error": "Invalid entity type"}, status=400)

        entity = get_object_or_404(model, pk=pk, project__pk=project_pk)

        data = {}
        if entity_type == "labour":
            data = {
                "person_name": entity.person_name,
                "id_number": entity.id_number,
                "trade": entity.trade,
                "skill_type_id": entity.skill_type.id if entity.skill_type else "",
            }
        elif entity_type == "material":
            data = {
                "supplier": entity.supplier,
                "items_received": entity.items_received or entity.name,
                "unit": entity.unit,
            }
        elif entity_type == "plant":
            data = {
                "equipment_name": entity.name,
                "supplier": entity.supplier,
                "plant_type_id": entity.plant_type.id if entity.plant_type else "",
            }
        elif entity_type == "subcontractor":
            data = {
                "name": entity.name,
                "trade": entity.trade,
                "scope": entity.scope,
                "start_date": (
                    entity.start_date.isoformat() if entity.start_date else ""
                ),
                "planned_finish_date": (
                    entity.planned_finish_date.isoformat()
                    if entity.planned_finish_date
                    else ""
                ),
                "actual_finish_date": (
                    entity.actual_finish_date.isoformat()
                    if entity.actual_finish_date
                    else ""
                ),
            }

        return JsonResponse(data)
