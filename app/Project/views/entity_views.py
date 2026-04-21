"""Views for Project Entity Management."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
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
from app.Project.models.unit_models import UnitOfMeasure
from app.SiteManagement.models.plant_type import PlantType
from app.SiteManagement.models.skill_type import SkillType


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

        # Add UnitOfMeasureForm for the quick create modal
        from ..forms.unit_forms import UnitOfMeasureForm

        context["unit_form"] = UnitOfMeasureForm()

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
        context["units"] = UnitOfMeasure.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        header_form = MaterialHeaderForm(request.POST, request.FILES)
        formset = MaterialItemFormSet(request.POST)

        if header_form.is_valid() and formset.is_valid():
            # Check if at least one item exists and is not deleted
            if not any(
                form.cleaned_data and not form.cleaned_data.get("DELETE", False)
                for form in formset.forms
            ):
                from django.contrib import messages

                messages.error(request, "You must add at least one material item.")
                return self.render_to_response(
                    self.get_context_data(header_form=header_form, formset=formset)
                )
            return self.formset_valid(header_form, formset)

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


# ==========================================
# Excel Upload/Download Views
# ==========================================


class EntityExcelTemplateView(ProjectEntityMixin, View):
    """View to download a blank Excel template for entity uploads."""

    def get(self, request, *args, **kwargs):
        import io

        import pandas as pd

        entity_type = kwargs.get("entity_type")

        # Define headers based on entity type
        headers = {
            "labour": [
                "Person Name",
                "ID Number",
                "Trade",
                "Skill Type",
                "Date Joined (YYYY-MM-DD)",
                "Unit",
                "Rate",
                "Expense Code (COS/OPEX)",
                "Description",
            ],
            "material": [
                "Name",
                "Supplier",
                "Items Received",
                "Invoice Number",
                "Quantity",
                "Date Received (YYYY-MM-DD)",
                "Unit",
                "Rate",
                "Expense Code (COS/OPEX)",
                "Description",
            ],
            "plant": [
                "Name",
                "Plant Type",
                "Specific Info",
                "Supplier",
                "Breakdown Status (OPERATIONAL/BREAKDOWN/etc)",
                "Date (YYYY-MM-DD)",
                "Unit",
                "Rate",
                "Expense Code (COS/OPEX)",
                "Description",
            ],
            "subcontractor": [
                "Name",
                "Trade",
                "Scope",
                "Start Date (YYYY-MM-DD)",
                "Planned Finish Date (YYYY-MM-DD)",
                "Actual Finish Date (YYYY-MM-DD)",
                "Unit",
                "Rate",
                "Expense Code (COS/OPEX)",
                "Description",
            ],
            "overhead": [
                "Name",
                "Category",
                "Unit",
                "Rate",
                "Expense Code (COS/OPEX)",
                "Description",
            ],
        }

        columns = headers.get(str(entity_type), ["Name", "Description", "Rate"])
        df = pd.DataFrame(columns=columns)

        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Template")

        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{entity_type}_template.xlsx"'
        )
        return response


class EntityExcelUploadView(ProjectEntityMixin, View):
    """View to handle Excel upload and project entity creation."""

    def post(self, request, *args, **kwargs):
        import pandas as pd

        entity_type = kwargs.get("entity_type")
        excel_file = request.FILES.get("excel_file")

        if not excel_file:
            messages.error(request, "Please select an Excel file to upload.")
            return redirect(
                reverse(
                    f"project:entity-{entity_type}-list",
                    kwargs={"project_pk": self.project.pk},
                )
            )

        try:
            df = pd.read_excel(excel_file)
            df = df.where(pd.notnull(df), None)  # Replace NaN with None

            success_count = 0
            errors = []

            for index, (_, row) in enumerate(df.iterrows()):
                try:
                    data = {
                        "project": self.project,
                        "name": row.get("Name") or row.get("Person Name"),
                        "unit": row.get("Unit"),
                        "rate": row.get("Rate", 0) or 0,
                        "expense_code": row.get("Expense Code (COS/OPEX)", "COS"),
                        "description": row.get("Description", ""),
                    }

                    # Basic validation: Name is required
                    if not data["name"]:
                        errors.append(f"Row {index + 2}: Name/Person Name is required.")
                        continue

                    # Expense code normalization
                    if data["expense_code"] not in ["COS", "OPEX"]:
                        data["expense_code"] = "COS"

                    # Handle specific entity types
                    if entity_type == "labour":
                        skill_type_name = row.get("Skill Type")
                        skill_type = None
                        if skill_type_name:
                            skill_type = SkillType.objects.filter(
                                project=self.project, name__iexact=skill_type_name
                            ).first()

                        LabourEntity.objects.create(
                            **data,
                            person_name=row.get("Person Name") or data["name"],
                            id_number=str(row.get("ID Number", "")) or "",
                            trade=row.get("Trade", ""),
                            skill_type=skill_type,
                            date_joined=row.get("Date Joined (YYYY-MM-DD)"),
                        )
                    elif entity_type == "material":
                        MaterialEntity.objects.create(
                            **data,
                            supplier=row.get("Supplier", ""),
                            items_received=row.get("Items Received", ""),
                            invoice_number=str(row.get("Invoice Number", "")) or "",
                            quantity=row.get("Quantity", 0) or 0,
                            date_received=row.get("Date Received (YYYY-MM-DD)"),
                        )
                    elif entity_type == "plant":
                        plant_type_name = row.get("Plant Type")
                        plant_type = None
                        if plant_type_name:
                            plant_type = PlantType.objects.filter(
                                project=self.project, name__iexact=plant_type_name
                            ).first()

                        PlantEntity.objects.create(
                            **data,
                            plant_type=plant_type,
                            specific_info=row.get("Specific Info", ""),
                            supplier=row.get("Supplier", ""),
                            breakdown_status=row.get(
                                "Breakdown Status (OPERATIONAL/BREAKDOWN/etc)",
                                "OPERATIONAL",
                            ),
                            date=row.get("Date (YYYY-MM-DD)"),
                        )
                    elif entity_type == "subcontractor":
                        SubcontractorEntity.objects.create(
                            **data,
                            trade=row.get("Trade", ""),
                            scope=row.get("Scope", ""),
                            start_date=row.get("Start Date (YYYY-MM-DD)"),
                            planned_finish_date=row.get(
                                "Planned Finish Date (YYYY-MM-DD)"
                            ),
                            actual_finish_date=row.get(
                                "Actual Finish Date (YYYY-MM-DD)"
                            ),
                        )
                    elif entity_type == "overhead":
                        OverheadEntity.objects.create(
                            **data,
                            category=row.get("Category", ""),
                        )

                    success_count += 1

                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")

            if success_count > 0:
                messages.success(
                    request, f"Successfully imported {success_count} entries."
                )

            if errors:
                for err in errors[:5]:  # Show first 5 errors to avoid flooding
                    messages.error(request, err)
                if len(errors) > 5:
                    messages.error(request, f"...and {len(errors) - 5} more errors.")

        except Exception as e:
            messages.error(request, f"Error processing Excel file: {str(e)}")

        return redirect(
            reverse(
                f"project:entity-{entity_type}-list",
                kwargs={"project_pk": self.project.pk},
            )
        )
