"""Views for Project Entity Management."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.forms.entity_forms import (
    LabourEntityForm,
    MaterialEntityForm,
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
        return super().get_queryset().filter(project=self.project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["entity_name"] = self.entity_name
        context["entity_type"] = self.entity_type
        # Add a flag to identify the entity type in the template if needed
        context[f"is_{self.entity_type}"] = True
        return context

    def form_valid(self, form):
        if hasattr(form, "instance"):
            form.instance.project = self.project
        return super().form_valid(form)

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
    form_class = MaterialEntityForm
    template_name = "entity_management/form.html"
    entity_name = "Material"
    entity_type = "material"


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
