import json
import os
import tempfile
from decimal import Decimal
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import models
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, ListView, TemplateView
from django.views.generic.base import ContextMixin

from app.BillOfQuantities.models.structure_models import LineItem
from app.Project.models import Project

from .calculations import (
    calculate_boq_summary,
    calculate_pct_of_total,
    calculate_variance,
)
from .data_adapters import DjangoORMAdapter
from .forms import (
    ExcelImportForm,
    LabourCrewForm,
    LabourSpecificationForm,
    MaterialForm,
    ProjectAssumptionsForm,
    SpecificationComponentFormSet,
    SpecificationForm,
    SystemLabourCrewForm,
    SystemLabourSpecificationForm,
    SystemMaterialForm,
    SystemSpecificationComponentFormSet,
    SystemSpecificationForm,
    SystemTradeCodeForm,
)
from .models import (
    BOQItem,
    ProjectAssumptions,
    ProjectLabourCrew,
    ProjectLabourSpecification,
    ProjectMaterial,
    ProjectSpecification,
    ProjectSpecificationComponent,
    ProjectTradeCode,
    SystemLabourCrew,
    SystemLabourSpecification,
    SystemMaterial,
    SystemSpecification,
    SystemSpecificationComponent,
    SystemTradeCode,
    sync_boq_from_lineitems,
)


class ProjectEstimatorMixin(ContextMixin):
    """Mixin that loads the project from URL kwargs and adds it to context."""

    def get_project(self):
        if not hasattr(self, "_project"):
            kwargs = getattr(self, "kwargs", {})
            self._project = get_object_or_404(Project, pk=kwargs.get("project_pk"))
        return self._project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["project_pk"] = getattr(self, "kwargs", {}).get("project_pk")
        return context


class ProjectAssumptionsView(ProjectEstimatorMixin, TemplateView):
    template_name = "estimator/project_assumptions.html"

    def get_assumptions(self):
        obj, _ = ProjectAssumptions.objects.get_or_create(project=self.get_project())
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ProjectAssumptionsForm(instance=self.get_assumptions())
        return context

    def post(self, request, *args, **kwargs):
        assumptions = self.get_assumptions()
        form = ProjectAssumptionsForm(request.POST, instance=assumptions)
        if form.is_valid():
            form.save()
            messages.success(request, "Project assumptions saved.")
            return redirect(
                "estimator:project_assumptions", project_pk=self.kwargs["project_pk"]
            )
        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)


class DashboardView(ProjectEstimatorMixin, ListView):
    model = BOQItem
    template_name = "estimator/dashboard.html"
    context_object_name = "items"

    def get_queryset(self):
        qs = (
            BOQItem.objects.filter(project=self.get_project())
            .select_related(
                "trade_code",
                "specification",
                "labour_specification",
                "labour_specification__crew",
                "material",
            )
            .prefetch_related(
                "specification__spec_components__material",
            )
        )

        # Apply filters from query params
        section = self.request.GET.get("section")
        if section:
            qs = qs.filter(section=section)

        bill_no = self.request.GET.get("bill_no")
        if bill_no:
            qs = qs.filter(bill_no=bill_no)

        trade_code = self.request.GET.get("trade_code")
        if trade_code:
            qs = qs.filter(trade_code__id=trade_code)

        mat_spec = self.request.GET.get("mat_spec")
        if mat_spec == "none":
            qs = qs.filter(specification__isnull=True, material__isnull=True)
        elif mat_spec == "has_spec":
            qs = qs.filter(specification__isnull=False)
        elif mat_spec == "has_material":
            qs = qs.filter(material__isnull=False)
        elif mat_spec:
            qs = qs.filter(specification__name=mat_spec)

        lab_spec = self.request.GET.get("lab_spec")
        if lab_spec == "none":
            qs = qs.filter(labour_specification__isnull=True)
        elif lab_spec:
            qs = qs.filter(labour_specification__name=lab_spec)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()

        adapter = DjangoORMAdapter(project_id=project.pk)
        boq_data = adapter.get_boq_items(project_id=project.pk)
        summary = calculate_boq_summary(boq_data)

        context["total_contract_amount"] = summary["total_contract_amount"]
        context["total_materials_rate"] = summary["total_materials_rate"]
        context["total_labour_rate"] = summary["total_labour_rate"]
        context["total_progress_amount"] = summary["total_progress_amount"]
        context["total_forecast_amount"] = summary["total_forecast_amount"]

        # Filter options (scoped to project)
        project_items = BOQItem.objects.filter(project=project)
        context["sections"] = (
            project_items.exclude(section="")
            .values_list("section", flat=True)
            .distinct()
            .order_by("section")
        )
        context["bill_nos"] = (
            project_items.exclude(bill_no="")
            .values_list("bill_no", flat=True)
            .distinct()
            .order_by("bill_no")
        )
        context["trade_codes"] = ProjectTradeCode.objects.filter(project=project)
        context["spec_names"] = (
            ProjectSpecification.objects.filter(project=project)
            .exclude(name="")
            .values_list("name", flat=True)
            .distinct()
            .order_by("name")
        )
        context["labour_spec_names"] = (
            ProjectLabourSpecification.objects.filter(project=project)
            .exclude(name="")
            .values_list("name", flat=True)
            .distinct()
            .order_by("name")
        )

        # Current filter values
        context["f_section"] = self.request.GET.get("section", "")
        context["f_bill_no"] = self.request.GET.get("bill_no", "")
        context["f_trade_code"] = self.request.GET.get("trade_code", "")
        context["f_mat_spec"] = self.request.GET.get("mat_spec", "")
        context["f_lab_spec"] = self.request.GET.get("lab_spec", "")

        # Project assumptions (wastage)
        assumptions, _ = ProjectAssumptions.objects.get_or_create(project=project)
        context["wastage_pct"] = assumptions.wastage_pct

        return context


class BaselineBoqView(ProjectEstimatorMixin, ListView):
    """Reads baseline BoQ data from BillOfQuantities LineItem for the project."""

    model = LineItem
    template_name = "estimator/baseline_boq.html"
    context_object_name = "items"

    def get_queryset(self):
        project = self.get_project()
        qs = (
            LineItem.objects.filter(project=project)
            .select_related("bill", "bill__structure", "structure", "package")
            .order_by("row_index")
        )

        section = self.request.GET.get("section")
        if section:
            qs = qs.filter(bill__name=section)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = context["items"]

        total_contract = Decimal("0")
        for item in items:
            if item.is_work and item.total_price:
                total_contract += item.total_price

        context["total_contract_amount"] = total_contract
        context["item_count"] = items.count() if hasattr(items, "count") else len(items)

        # Filter options
        project = self.get_project()
        context["sections"] = (
            LineItem.objects.filter(project=project)
            .exclude(bill__isnull=True)
            .values_list("bill__name", flat=True)
            .distinct()
            .order_by("bill__name")
        )

        context["f_section"] = self.request.GET.get("section", "")
        context["boq_item_count"] = BOQItem.objects.filter(project=project).count()

        return context


class SyncBoqView(ProjectEstimatorMixin, View):
    """Sync BOQItems from BillOfQuantities LineItems for this project."""

    def get_project(self):
        if not hasattr(self, "_project"):
            self._project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        return self._project

    def post(self, request, project_pk):
        project = self.get_project()
        created, updated, deleted = sync_boq_from_lineitems(project)
        messages.success(
            request,
            f"BoQ synced: {created} created, {updated} updated, {deleted} deleted",
        )
        return redirect(
            reverse("estimator:dashboard", kwargs={"project_pk": project_pk})
        )


class SpecificationListView(ProjectEstimatorMixin, TemplateView):
    """Material calculator — driven by Output BoQ.

    Groups BOQItems by (section, specification) and sums contract_quantity
    per group. Looks up components and rates from the ProjectSpecification.
    """

    template_name = "estimator/specification_list.html"

    def _build_calculator_rows(
        self, project, section_filter=None, trade_code_filter=None, name_filter=None
    ):
        qs = (
            BOQItem.objects.filter(
                project=project,
                specification__isnull=False,
                is_section_header=False,
            )
            .select_related(
                "specification__trade_code",
            )
            .prefetch_related(
                "specification__spec_components__material",
            )
        )

        if section_filter:
            qs = qs.filter(section=section_filter)
        if name_filter:
            qs = qs.filter(specification__name=name_filter)
        if trade_code_filter:
            qs = qs.filter(specification__trade_code_id=trade_code_filter)

        # Group by (section, specification_id)
        from collections import OrderedDict

        groups = OrderedDict()
        for boq in qs.order_by("section", "specification__name"):
            key = (boq.section, getattr(boq, "specification_id", None))
            if key not in groups:
                groups[key] = {
                    "section": boq.section,
                    "spec": boq.specification,
                    "boq_qty": Decimal("0"),
                }
            if boq.contract_quantity:
                groups[key]["boq_qty"] += boq.contract_quantity

        # Build rows with component totals
        rows = []
        for group in groups.values():
            spec = group["spec"]
            boq_qty = group["boq_qty"]
            component_totals = []
            for sc in spec.spec_components.select_related("material").all():
                component_totals.append(
                    {
                        "id": sc.id,
                        "label": sc.label,
                        "qty_per_unit": sc.qty_per_unit,
                        "total_quantity": boq_qty * sc.qty_per_unit
                        if boq_qty
                        else Decimal("0"),
                        "unit": sc.material.unit if sc.material else "",
                    }
                )
            rows.append(
                {
                    "section": group["section"],
                    "spec": spec,
                    "boq_qty": boq_qty,
                    "rate_per_unit": spec.rate_per_unit,
                    "component_totals": component_totals,
                }
            )
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()

        f_section = self.request.GET.get("section", "")
        f_trade_code = self.request.GET.get("trade_code", "")
        f_name = self.request.GET.get("name", "")

        context["specs"] = self._build_calculator_rows(
            project,
            section_filter=f_section or None,
            trade_code_filter=f_trade_code or None,
            name_filter=f_name or None,
        )

        context["spec_form"] = context.get(
            "spec_form", SpecificationForm(project=project)
        )
        context["component_formset"] = context.get(
            "component_formset", SpecificationComponentFormSet()
        )

        # Filter options from Output BoQ
        boq_with_spec = BOQItem.objects.filter(
            project=project,
            specification__isnull=False,
            is_section_header=False,
        )
        context["sections"] = (
            boq_with_spec.exclude(section="")
            .values_list("section", flat=True)
            .distinct()
            .order_by("section")
        )
        context["trade_codes"] = ProjectTradeCode.objects.filter(
            pk__in=boq_with_spec.exclude(specification__trade_code__isnull=True)
            .values_list("specification__trade_code_id", flat=True)
            .distinct()
        )
        context["names"] = (
            boq_with_spec.values_list("specification__name", flat=True)
            .distinct()
            .order_by("specification__name")
        )

        context["f_section"] = f_section
        context["f_trade_code"] = f_trade_code
        context["f_name"] = f_name

        return context

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        spec_form = SpecificationForm(request.POST, project=project)
        component_formset = SpecificationComponentFormSet(request.POST)
        if spec_form.is_valid():
            spec = spec_form.save(commit=False)
            spec.project = project
            spec.save()
            component_formset = SpecificationComponentFormSet(
                request.POST, instance=spec
            )
            if component_formset.is_valid():
                component_formset.save()
                return redirect(
                    reverse(
                        "estimator:specifications",
                        kwargs={"project_pk": self.kwargs["project_pk"]},
                    )
                )
            else:
                spec.delete()
        return self.render_to_response(
            self.get_context_data(
                spec_form=spec_form, component_formset=component_formset
            )
        )


class MaterialSpecListView(ProjectEstimatorMixin, ListView):
    """Simple material specifications view — Name, Trade Code, Unit, Components."""

    model = ProjectSpecification
    template_name = "estimator/material_spec_list.html"
    context_object_name = "specs"

    def get_queryset(self):
        project = self.get_project()
        qs = (
            ProjectSpecification.objects.filter(project=project)
            .select_related("trade_code")
            .prefetch_related("spec_components__material")
        )

        section = self.request.GET.get("section")
        if section:
            qs = qs.filter(section=section)

        trade_code = self.request.GET.get("trade_code")
        if trade_code:
            qs = qs.filter(trade_code__id=trade_code)

        name = self.request.GET.get("name")
        if name:
            qs = qs.filter(name=name)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["spec_form"] = context.get(
            "spec_form", SpecificationForm(project=project)
        )
        context["component_formset"] = context.get(
            "component_formset", SpecificationComponentFormSet()
        )

        project_specs = ProjectSpecification.objects.filter(project=project)
        context["sections"] = (
            project_specs.exclude(section="")
            .values_list("section", flat=True)
            .distinct()
            .order_by("section")
        )
        context["trade_codes"] = ProjectTradeCode.objects.filter(project=project)
        context["names"] = (
            project_specs.values_list("name", flat=True).distinct().order_by("name")
        )

        context["f_section"] = self.request.GET.get("section", "")
        context["f_trade_code"] = self.request.GET.get("trade_code", "")
        context["f_name"] = self.request.GET.get("name", "")

        return context

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        spec_form = SpecificationForm(request.POST, project=project)
        component_formset = SpecificationComponentFormSet(request.POST)
        if spec_form.is_valid():
            spec = spec_form.save(commit=False)
            spec.project = project
            spec.save()
            component_formset = SpecificationComponentFormSet(
                request.POST, instance=spec
            )
            if component_formset.is_valid():
                component_formset.save()
                return redirect(
                    reverse(
                        "estimator:material_specs",
                        kwargs={"project_pk": self.kwargs["project_pk"]},
                    )
                )
            else:
                spec.delete()
        self.object_list = self.get_queryset()
        return self.render_to_response(
            self.get_context_data(
                spec_form=spec_form, component_formset=component_formset
            )
        )


class MaterialsListView(ProjectEstimatorMixin, ListView):
    model = ProjectMaterial
    template_name = "estimator/materials_list.html"
    context_object_name = "materials"

    def get_queryset(self):
        return ProjectMaterial.objects.filter(project=self.get_project())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = context.get("form", MaterialForm())
        return context

    def post(self, request, *args, **kwargs):
        form = MaterialForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.project = self.get_project()
            obj.save()
            return redirect(
                reverse(
                    "estimator:materials",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                )
            )
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))


class LabourCostListView(ProjectEstimatorMixin, ListView):
    model = ProjectLabourCrew
    template_name = "estimator/labour_costs_list.html"
    context_object_name = "crews"

    def get_queryset(self):
        return ProjectLabourCrew.objects.filter(project=self.get_project())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = context.get("form", LabourCrewForm())
        return context

    def post(self, request, *args, **kwargs):
        form = LabourCrewForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.project = self.get_project()
            obj.save()
            return redirect(
                reverse(
                    "estimator:labour_costs",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                )
            )
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))


class LabourSpecificationListView(ProjectEstimatorMixin, TemplateView):
    """Labour calculator — driven by Output BoQ.

    Groups BOQItems by (section, labour_specification) and sums
    contract_quantity per group.
    """

    template_name = "estimator/labour_specification_list.html"

    def _build_calculator_rows(
        self, project, section_filter=None, trade_name_filter=None, name_filter=None
    ):
        qs = BOQItem.objects.filter(
            project=project,
            labour_specification__isnull=False,
            is_section_header=False,
        ).select_related(
            "labour_specification__crew",
        )

        if section_filter:
            qs = qs.filter(section=section_filter)
        if name_filter:
            qs = qs.filter(labour_specification__name=name_filter)
        if trade_name_filter:
            qs = qs.filter(labour_specification__trade_name=trade_name_filter)

        from collections import OrderedDict

        groups = OrderedDict()
        for boq in qs.order_by("section", "labour_specification__name"):
            key = (boq.section, getattr(boq, "labour_specification_id", None))
            if key not in groups:
                groups[key] = {
                    "section": boq.section,
                    "ls": boq.labour_specification,
                    "boq_qty": Decimal("0"),
                }
            if boq.contract_quantity:
                groups[key]["boq_qty"] += boq.contract_quantity

        rows = []
        for group in groups.values():
            ls = group["ls"]
            boq_qty = group["boq_qty"]
            rows.append(
                {
                    "section": group["section"],
                    "ls": ls,
                    "boq_qty": boq_qty,
                    "daily_output": ls.daily_output,
                    "daily_cost": ls.daily_cost,
                    "rate_per_unit": ls.rate_per_unit,
                    "total_cost": boq_qty * ls.daily_cost if boq_qty else Decimal("0"),
                }
            )
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()

        f_section = self.request.GET.get("section", "")
        f_trade_name = self.request.GET.get("trade_name", "")
        f_name = self.request.GET.get("name", "")

        context["labour_specs"] = self._build_calculator_rows(
            project,
            section_filter=f_section or None,
            trade_name_filter=f_trade_name or None,
            name_filter=f_name or None,
        )

        context["form"] = context.get("form", LabourSpecificationForm(project=project))

        # Filter options from Output BoQ
        boq_with_lspec = BOQItem.objects.filter(
            project=project,
            labour_specification__isnull=False,
            is_section_header=False,
        )
        context["sections"] = (
            boq_with_lspec.exclude(section="")
            .values_list("section", flat=True)
            .distinct()
            .order_by("section")
        )
        context["trade_names"] = (
            boq_with_lspec.exclude(labour_specification__trade_name="")
            .values_list("labour_specification__trade_name", flat=True)
            .distinct()
            .order_by("labour_specification__trade_name")
        )
        context["names"] = (
            boq_with_lspec.values_list("labour_specification__name", flat=True)
            .distinct()
            .order_by("labour_specification__name")
        )

        context["f_section"] = f_section
        context["f_trade_name"] = f_trade_name
        context["f_name"] = f_name

        return context

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        form = LabourSpecificationForm(request.POST, project=project)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.project = project
            obj.save()
            return redirect(
                reverse(
                    "estimator:labour_specs",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                )
            )
        return self.render_to_response(self.get_context_data(form=form))


class TradeCodeListView(ProjectEstimatorMixin, ListView):
    model = ProjectTradeCode
    template_name = "estimator/trade_code_list.html"
    context_object_name = "trade_codes"

    def get_queryset(self):
        return ProjectTradeCode.objects.filter(project=self.get_project())


class ExcelImportView(ProjectEstimatorMixin, FormView):
    template_name = "estimator/import_excel.html"
    form_class = ExcelImportForm

    def get_success_url(self):
        return reverse(
            "estimator:import_excel", kwargs={"project_pk": self.kwargs["project_pk"]}
        )

    def form_valid(self, form):
        uploaded = form.cleaned_data["file"]

        # Write uploaded file to a temp file for openpyxl
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        try:
            for chunk in uploaded.chunks():
                tmp.write(chunk)
            tmp.close()

            from .management.commands.import_excel import ExcelImporter

            importer = ExcelImporter(tmp.name, project=self.get_project())
            results = importer.run()

            parts = []
            labels = {
                "trade_codes": "Trade Codes",
                "materials": "Material Costs",
                "specifications": "Material Estimator",
                "labour_crews": "Labour Crews",
                "labour_specs": "Labour Specs",
                "boq_items": "Output BoQ Items",
            }
            for key, label in labels.items():
                if key in results:
                    parts.append(f"{label}: {results[key]}")

            messages.success(self.request, f"Import successful — {', '.join(parts)}")
        except Exception as e:
            messages.error(self.request, f"Import failed: {e}")
        finally:
            os.unlink(tmp.name)

        return redirect(self.get_success_url())


class ReportsIndexView(ProjectEstimatorMixin, TemplateView):
    template_name = "estimator/reports_index.html"


class PricedBoqReportView(ProjectEstimatorMixin, ListView):
    model = BOQItem
    template_name = "estimator/reports/priced_boq.html"
    context_object_name = "items"

    REPORT_CONFIGS = {
        "baseline_assessment": {
            "title": "Baseline Assessment",
            "subtitle": "Compares new and old amount based on original quantities",
            "amount_a_label": "Baseline Amount",
            "amount_b_label": "New Baseline Amount",
            "key_rates_only": False,
        },
        "progress_assessment": {
            "title": "Progress Assessment",
            "subtitle": "Compares original amount and new amount based on progress quantities",
            "amount_a_label": "Baseline Amount",
            "amount_b_label": "Progress Amount",
            "key_rates_only": False,
        },
        "forecast_assessment": {
            "title": "Forecast Assessment",
            "subtitle": "Compares baseline BoQ with new rates and forecast quantities",
            "amount_a_label": "Baseline Amount",
            "amount_b_label": "Forecast Amount",
            "key_rates_only": False,
        },
        "key_rates_assessment": {
            "title": "Key Rates Assessment",
            "subtitle": "Compares new and old amount based on original quantities for priced items",
            "amount_a_label": "Baseline Amount",
            "amount_b_label": "New Baseline Amount",
            "key_rates_only": True,
        },
    }

    def _get_config(self):
        return self.REPORT_CONFIGS[self.kwargs["report_type"]]

    def _get_amounts(self, item, report_type):
        """Return (amount_a, amount_b) for a given item and report type."""
        contract_amt = item.contract_amount
        baseline_amt = (
            item.baseline_new_price * item.contract_quantity
            if item.baseline_new_price and item.contract_quantity
            else None
        )

        if report_type == "progress_assessment":
            return (baseline_amt, item.progress_amount)
        elif report_type == "forecast_assessment":
            return (baseline_amt, item.forecast_amount)
        else:  # baseline_assessment and key_rates_assessment
            return (contract_amt, baseline_amt)

    def get_queryset(self):
        qs = (
            BOQItem.objects.filter(project=self.get_project())
            .select_related(
                "trade_code",
                "specification",
                "labour_specification",
                "labour_specification__crew",
                "material",
            )
            .prefetch_related(
                "specification__spec_components__material",
            )
            .filter(is_section_header=False)
        )

        config = self._get_config()
        if config["key_rates_only"]:
            qs = qs.filter(
                models.Q(specification__isnull=False) | models.Q(material__isnull=False)
            )

        section = self.request.GET.get("section")
        if section:
            qs = qs.filter(section=section)

        trade_code = self.request.GET.get("trade_code")
        if trade_code:
            qs = qs.filter(trade_code__id=trade_code)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = self._get_config()
        report_type = self.kwargs["report_type"]

        context["report_title"] = config["title"]
        context["report_subtitle"] = config["subtitle"]
        context["amount_a_label"] = config["amount_a_label"]
        context["amount_b_label"] = config["amount_b_label"]

        total_a = Decimal("0")
        total_b = Decimal("0")
        report_rows = []

        for item in context["items"]:
            amount_a, amount_b = self._get_amounts(item, report_type)
            variance_amt, variance_pct = calculate_variance(amount_a, amount_b)

            mat_rate = item.new_materials_rate
            lab_rate = item.new_labour_rate
            bnp = item.baseline_new_price
            if bnp and bnp > 0:
                mat_pct = (Decimal(str(mat_rate or 0)) / bnp) * Decimal("100")
                lab_pct = (Decimal(str(lab_rate or 0)) / bnp) * Decimal("100")
            else:
                mat_pct = None
                lab_pct = None

            if amount_a:
                total_a += amount_a
            if amount_b:
                total_b += amount_b

            report_rows.append(
                {
                    "section": item.section,
                    "bill_no": item.bill_no,
                    "amount_a": amount_a,
                    "amount_b": amount_b,
                    "variance_amount": variance_amt,
                    "variance_pct": variance_pct,
                    "materials_pct": mat_pct,
                    "labour_pct": lab_pct,
                }
            )

        total_variance, total_variance_pct = calculate_variance(total_a, total_b)
        context["report_rows"] = report_rows
        context["total_a"] = total_a
        context["total_b"] = total_b
        context["total_variance"] = total_variance
        context["total_variance_pct"] = total_variance_pct

        # Filter options
        project = self.get_project()
        project_items = BOQItem.objects.filter(project=project)
        context["sections"] = (
            project_items.exclude(section="")
            .values_list("section", flat=True)
            .distinct()
            .order_by("section")
        )
        context["trade_codes"] = ProjectTradeCode.objects.filter(project=project)
        context["f_section"] = self.request.GET.get("section", "")
        context["f_trade_code"] = self.request.GET.get("trade_code", "")

        return context


class MaterialListReportView(ProjectEstimatorMixin, ListView):
    model = BOQItem
    template_name = "estimator/reports/material_list.html"
    context_object_name = "items"

    VARIANT_CONFIGS = {
        "baseline": {
            "title_new": "Baseline Material List (New Rates)",
            "title_contract": "Baseline Material List (Contract Rates)",
            "qty_field": "contract_quantity",
        },
        "progress": {
            "title_new": "Progress Material List (New Rates)",
            "title_contract": "Progress Material List (Contract Rates)",
            "qty_field": "progress_quantity",
        },
        "forecast": {
            "title_new": "Forecast Material List (New Rates)",
            "title_contract": "Forecast Material List (Contract Rates)",
            "qty_field": "forecast_quantity",
        },
    }

    def _get_config(self):
        return self.VARIANT_CONFIGS[self.kwargs["variant"]]

    def _get_rate_type(self):
        return self.kwargs.get("rate_type", "new")

    def get_queryset(self):
        qs = (
            BOQItem.objects.filter(project=self.get_project())
            .select_related(
                "trade_code",
                "specification",
                "material",
            )
            .prefetch_related(
                "specification__spec_components__material",
            )
            .filter(
                is_section_header=False,
            )
            .filter(
                models.Q(specification__isnull=False) | models.Q(material__isnull=False)
            )
        )

        section = self.request.GET.get("section")
        if section:
            qs = qs.filter(section=section)

        trade_code = self.request.GET.get("trade_code")
        if trade_code:
            qs = qs.filter(trade_code__id=trade_code)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = self._get_config()
        qty_field = config["qty_field"]
        rate_type = self._get_rate_type()

        title_key = "title_contract" if rate_type == "contract" else "title_new"
        context["report_title"] = config[title_key]
        context["rate_type"] = rate_type

        if rate_type == "contract":
            context["parent_template"] = (
                "estimator/base_baseline_estimator_materials.html"
            )
        else:
            context["parent_template"] = "estimator/base_materials_estimator.html"

        grand_total = Decimal("0")
        report_rows = []

        for item in context["items"]:
            quantity = getattr(item, qty_field) or Decimal("0")
            if rate_type == "contract":
                rate = item.contract_rate
            else:
                rate = item.new_materials_rate
            if rate and quantity:
                amount = rate * quantity
            else:
                amount = None

            material_name = ""
            unit = item.unit
            if item.specification:
                material_name = item.specification.name
            elif item.material:
                material_name = item.material.material_code
                unit = item.material.unit

            if amount:
                grand_total += amount

            report_rows.append(
                {
                    "section": item.section,
                    "bill_no": item.bill_no,
                    "material_name": material_name,
                    "unit": unit,
                    "quantity": quantity if quantity else None,
                    "rate": rate,
                    "amount": amount,
                }
            )

        # Add pct_of_total
        for row in report_rows:
            row["pct_of_total"] = calculate_pct_of_total(row["amount"], grand_total)

        context["report_rows"] = report_rows
        context["grand_total"] = grand_total

        # Chart data: cost by section
        section_totals = {}
        material_totals = {}
        for row in report_rows:
            if row["amount"]:
                s = row["section"] or "Unassigned"
                section_totals[s] = section_totals.get(s, Decimal("0")) + row["amount"]
                m = row["material_name"] or "Unknown"
                material_totals[m] = (
                    material_totals.get(m, Decimal("0")) + row["amount"]
                )

        # Sort sections by amount descending
        sorted_sections = sorted(
            section_totals.items(), key=lambda x: x[1], reverse=True
        )
        context["chart_section_labels"] = json.dumps([s[0] for s in sorted_sections])
        context["chart_section_values"] = json.dumps(
            [float(s[1]) for s in sorted_sections]
        )

        # Top 10 materials by amount
        sorted_materials = sorted(
            material_totals.items(), key=lambda x: x[1], reverse=True
        )[:10]
        context["chart_material_labels"] = json.dumps([m[0] for m in sorted_materials])
        context["chart_material_values"] = json.dumps(
            [float(m[1]) for m in sorted_materials]
        )

        # Filter options
        project = self.get_project()
        project_items = BOQItem.objects.filter(project=project)
        context["sections"] = (
            project_items.exclude(section="")
            .values_list("section", flat=True)
            .distinct()
            .order_by("section")
        )
        context["trade_codes"] = ProjectTradeCode.objects.filter(project=project)
        context["f_section"] = self.request.GET.get("section", "")
        context["f_trade_code"] = self.request.GET.get("trade_code", "")

        return context


class LabourListReportView(ProjectEstimatorMixin, ListView):
    model = BOQItem
    template_name = "estimator/reports/labour_list.html"
    context_object_name = "items"

    VARIANT_CONFIGS = {
        "baseline": {
            "title_new": "Baseline Labour List (New Rates)",
            "title_contract": "Baseline Labour List (Contract Rates)",
            "qty_field": "contract_quantity",
        },
        "progress": {
            "title_new": "Progress Labour List (New Rates)",
            "title_contract": "Progress Labour List (Contract Rates)",
            "qty_field": "progress_quantity",
        },
        "forecast": {
            "title_new": "Forecast Labour List (New Rates)",
            "title_contract": "Forecast Labour List (Contract Rates)",
            "qty_field": "forecast_quantity",
        },
    }

    def _get_config(self):
        return self.VARIANT_CONFIGS[self.kwargs["variant"]]

    def _get_rate_type(self):
        return self.kwargs.get("rate_type", "new")

    def get_queryset(self):
        qs = (
            BOQItem.objects.filter(project=self.get_project())
            .select_related(
                "trade_code",
                "labour_specification",
                "labour_specification__crew",
            )
            .filter(
                is_section_header=False,
                labour_specification__isnull=False,
            )
        )

        section = self.request.GET.get("section")
        if section:
            qs = qs.filter(section=section)

        trade_code = self.request.GET.get("trade_code")
        if trade_code:
            qs = qs.filter(trade_code__id=trade_code)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = self._get_config()
        qty_field = config["qty_field"]
        rate_type = self._get_rate_type()

        title_key = "title_contract" if rate_type == "contract" else "title_new"
        context["report_title"] = config[title_key]
        context["rate_type"] = rate_type

        if rate_type == "contract":
            context["parent_template"] = "estimator/base_baseline_estimator_labour.html"
        else:
            context["parent_template"] = "estimator/base_labour_estimator.html"

        grand_total = Decimal("0")
        report_rows = []

        for item in context["items"]:
            ls = item.labour_specification
            crew = ls.crew if ls else None
            quantity = getattr(item, qty_field) or Decimal("0")
            if rate_type == "contract":
                rate = item.contract_rate
            else:
                rate = ls.rate_per_unit if ls else None
            if rate and quantity:
                amount = rate * quantity
            else:
                amount = None

            if amount:
                grand_total += amount

            report_rows.append(
                {
                    "section": item.section,
                    "bill_no": item.bill_no,
                    "crew_type": crew.crew_type if crew else "-",
                    "no_of_crews": 1,
                    "crew_rate_per_unit": rate,
                    "quantity": quantity if quantity else None,
                    "amount": amount,
                    "skilled": crew.skilled if crew else 0,
                    "semi_skilled": crew.semi_skilled if crew else 0,
                    "general": crew.general if crew else 0,
                }
            )

        for row in report_rows:
            row["pct_of_total"] = calculate_pct_of_total(row["amount"], grand_total)

        context["report_rows"] = report_rows
        context["grand_total"] = grand_total

        # Chart data: cost by crew type
        crew_totals = {}
        crew_composition = {}
        for row in report_rows:
            ct = row["crew_type"]
            if row["amount"]:
                crew_totals[ct] = crew_totals.get(ct, Decimal("0")) + row["amount"]
            if ct not in crew_composition:
                crew_composition[ct] = {
                    "skilled": row["skilled"],
                    "semi_skilled": row["semi_skilled"],
                    "general": row["general"],
                }

        sorted_crews = sorted(crew_totals.items(), key=lambda x: x[1], reverse=True)
        context["chart_crew_labels"] = json.dumps([c[0] for c in sorted_crews])
        context["chart_crew_values"] = json.dumps([float(c[1]) for c in sorted_crews])

        # Crew composition for stacked bar
        comp_labels = sorted(crew_composition.keys())
        context["chart_comp_labels"] = json.dumps(comp_labels)
        context["chart_comp_skilled"] = json.dumps(
            [crew_composition[c]["skilled"] for c in comp_labels]
        )
        context["chart_comp_semi"] = json.dumps(
            [crew_composition[c]["semi_skilled"] for c in comp_labels]
        )
        context["chart_comp_general"] = json.dumps(
            [crew_composition[c]["general"] for c in comp_labels]
        )

        # Filter options
        project = self.get_project()
        project_items = BOQItem.objects.filter(project=project)
        context["sections"] = (
            project_items.exclude(section="")
            .values_list("section", flat=True)
            .distinct()
            .order_by("section")
        )
        context["trade_codes"] = ProjectTradeCode.objects.filter(project=project)
        context["f_section"] = self.request.GET.get("section", "")
        context["f_trade_code"] = self.request.GET.get("trade_code", "")

        return context


@method_decorator(csrf_exempt, name="dispatch")
class UpdateBoqItemView(View):
    """AJAX endpoint to update FK fields or decimal markup fields on a BOQItem."""

    ALLOWED_FIELDS = {
        "trade_code": (ProjectTradeCode, "trade_code"),
        "specification": (ProjectSpecification, "specification"),
        "labour_specification": (ProjectLabourSpecification, "labour_specification"),
    }

    DECIMAL_FIELDS = {"material_markup_pct", "labour_markup_pct", "transport_pct"}

    def post(self, request, project_pk, pk):
        item = get_object_or_404(BOQItem, pk=pk, project_id=project_pk)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        field = data.get("field")
        value = data.get("value")

        if field in self.DECIMAL_FIELDS:
            try:
                setattr(item, field, Decimal(str(value or 0)))
            except Exception:
                return JsonResponse({"error": "Invalid value"}, status=400)
            item.save()
            return self._build_response(item)

        if field not in self.ALLOWED_FIELDS:
            return JsonResponse({"error": f'Field "{field}" not allowed'}, status=400)

        model_cls, attr_name = self.ALLOWED_FIELDS[field]

        if value is None or value == "" or value == 0:
            setattr(item, attr_name, None)
        else:
            try:
                # Try ID-based lookup first, scoped to project
                related_obj = model_cls.objects.get(
                    pk=int(value), project_id=project_pk
                )
                setattr(item, attr_name, related_obj)
            except (ValueError, TypeError):
                # Name-based lookup — find the spec matching the item's section
                try:
                    related_obj = model_cls.objects.filter(
                        name=str(value),
                        section=item.section,
                        project_id=project_pk,
                    ).first()
                    if not related_obj:
                        related_obj = model_cls.objects.filter(
                            name=str(value),
                            project_id=project_pk,
                        ).first()
                    if related_obj:
                        setattr(item, attr_name, related_obj)
                    else:
                        return JsonResponse(
                            {"error": f'{field} "{value}" not found'}, status=404
                        )
                except Exception:
                    return JsonResponse(
                        {"error": f'{field} "{value}" not found'}, status=404
                    )
            except model_cls.DoesNotExist:
                return JsonResponse(
                    {"error": f"{field} with id={value} not found"}, status=404
                )

        item.save()
        return self._build_response(item)

    @staticmethod
    def _build_response(item):
        def fmt(val):
            if val is None:
                return None
            return str(round(val, 2))

        return JsonResponse(
            {
                "ok": True,
                "new_materials_rate": fmt(item.new_materials_rate),
                "new_labour_rate": fmt(item.new_labour_rate),
                "baseline_new_price": fmt(item.baseline_new_price),
                "progress_amount": fmt(item.progress_amount),
                "forecast_amount": fmt(item.forecast_amount),
                "new_materials_amount": fmt(
                    item.new_materials_rate * item.contract_quantity
                    if item.new_materials_rate and item.contract_quantity
                    else None
                ),
                "new_labour_amount": fmt(
                    item.new_labour_rate * item.contract_quantity
                    if item.new_labour_rate and item.contract_quantity
                    else None
                ),
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class BulkMarkupUpdateView(View):
    """AJAX endpoint to bulk-update a markup field on all non-header BOQItems."""

    ALLOWED_FIELDS = {"material_markup_pct", "labour_markup_pct", "transport_pct"}

    def post(self, request, project_pk):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        field = data.get("field")
        value = data.get("value")

        if field not in self.ALLOWED_FIELDS:
            return JsonResponse({"error": f'Field "{field}" not allowed'}, status=400)

        try:
            decimal_value = Decimal(str(value or 0))
        except Exception:
            return JsonResponse({"error": "Invalid value"}, status=400)

        BOQItem.objects.filter(project_id=project_pk, is_section_header=False).update(
            **{field: decimal_value}
        )
        return JsonResponse({"ok": True})


@method_decorator(csrf_exempt, name="dispatch")
class UpdateMaterialView(View):
    """AJAX endpoint to update market_rate on a ProjectMaterial."""

    def post(self, request, project_pk, pk):
        item = get_object_or_404(ProjectMaterial, pk=pk, project_id=project_pk)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        field = data.get("field")
        value = data.get("value")

        if field != "market_rate":
            return JsonResponse({"error": f'Field "{field}" not allowed'}, status=400)

        try:
            item.market_rate = Decimal(str(value))
        except Exception:
            return JsonResponse({"error": "Invalid value"}, status=400)

        item.save()
        return JsonResponse(
            {"ok": True, "market_rate": str(round(item.market_rate, 2))}
        )


@method_decorator(csrf_exempt, name="dispatch")
class UpdateSpecComponentView(View):
    """AJAX endpoint to update qty_per_unit on a ProjectSpecificationComponent."""

    def post(self, request, project_pk, pk):
        item = get_object_or_404(ProjectSpecificationComponent, pk=pk)
        # Validate project ownership
        if item.specification.project_id != int(project_pk):
            return JsonResponse({"error": "Not found"}, status=404)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        field = data.get("field")
        value = data.get("value")

        if field != "qty_per_unit":
            return JsonResponse({"error": f'Field "{field}" not allowed'}, status=400)

        try:
            item.qty_per_unit = Decimal(str(value))
        except Exception:
            return JsonResponse({"error": "Invalid value"}, status=400)

        item.save()
        spec = item.specification
        return JsonResponse(
            {
                "ok": True,
                "qty_per_unit": str(round(item.qty_per_unit, 4)),
                "spec_id": spec.id,
                "spec_rate_per_unit": str(round(spec.rate_per_unit, 2)),
            }
        )


class SystemMaterialSpecListView(ProjectEstimatorMixin, ListView):
    """List System Specifications with form to add new spec (project-scoped view)."""

    model = SystemSpecification
    template_name = "estimator/system_spec_list.html"
    context_object_name = "specs"

    def get_queryset(self):
        return (
            SystemSpecification.objects.select_related("trade_code")
            .prefetch_related("spec_components__material")
            .all()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["spec_form"] = context.get("spec_form", SystemSpecificationForm())
        context["component_formset"] = context.get(
            "component_formset", SystemSpecificationComponentFormSet()
        )
        context["names"] = (
            SystemSpecification.objects.values_list("name", flat=True)
            .distinct()
            .order_by("name")
        )
        context["f_name"] = self.request.GET.get("name", "")
        return context

    def post(self, request, *args, **kwargs):
        spec_form = SystemSpecificationForm(request.POST)
        component_formset = SystemSpecificationComponentFormSet(request.POST)
        if spec_form.is_valid():
            spec = spec_form.save()
            component_formset = SystemSpecificationComponentFormSet(
                request.POST, instance=spec
            )
            if component_formset.is_valid():
                component_formset.save()
                return redirect(
                    reverse(
                        "estimator:system_specs",
                        kwargs={"project_pk": self.kwargs["project_pk"]},
                    )
                )
            else:
                spec.delete()
        self.object_list = self.get_queryset()
        return self.render_to_response(
            self.get_context_data(
                spec_form=spec_form, component_formset=component_formset
            )
        )


class UpdateSystemSpecComponentView(View):
    """AJAX endpoint to update qty_per_unit on a SystemSpecificationComponent."""

    def post(self, request, project_pk, pk):
        item = get_object_or_404(SystemSpecificationComponent, pk=pk)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        field = data.get("field")
        value = data.get("value")

        if field != "qty_per_unit":
            return JsonResponse({"error": f'Field "{field}" not allowed'}, status=400)

        try:
            item.qty_per_unit = Decimal(str(value))
        except Exception:
            return JsonResponse({"error": "Invalid value"}, status=400)

        item.save()
        spec = item.specification
        return JsonResponse(
            {
                "ok": True,
                "qty_per_unit": str(round(item.qty_per_unit, 4)),
                "spec_id": spec.id,
                "spec_rate_per_unit": str(round(spec.rate_per_unit, 2)),
            }
        )


class SystemSpecUploadView(ProjectEstimatorMixin, FormView):
    """Upload a System Specs library from Excel template."""

    template_name = "estimator/system_spec_upload.html"
    form_class = ExcelImportForm

    def get_success_url(self):
        return reverse(
            "estimator:system_specs", kwargs={"project_pk": self.kwargs["project_pk"]}
        )

    def form_valid(self, form):
        uploaded = form.cleaned_data["file"]

        # Write uploaded file to a temp file for openpyxl
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        try:
            for chunk in uploaded.chunks():
                tmp.write(chunk)
            tmp.close()

            from .management.commands.import_excel import SystemSpecImporter

            importer = SystemSpecImporter(tmp.name)
            results = importer.run()

            specs_result = results.get("system_specs", {})
            created = specs_result.get("created", 0)
            updated = specs_result.get("updated", 0)

            msg_parts = [f"{created} created, {updated} updated"]
            messages.success(
                self.request,
                f"System Specs uploaded successfully — {', '.join(msg_parts)}",
            )
        except Exception as e:
            messages.error(self.request, f"Import failed: {str(e)}")
        finally:
            os.unlink(tmp.name)

        return redirect(self.get_success_url())


class DownloadSystemSpecTemplateView(View):
    """Download the System Specs template Excel file."""

    def get(self, request, project_pk):
        template_path = Path(__file__).parent / "data" / "SystemSpec_Template.xlsx"

        if not os.path.exists(template_path):
            messages.error(request, "Template file not found")
            return redirect(
                reverse("estimator:system_specs", kwargs={"project_pk": project_pk})
            )

        response = FileResponse(open(template_path, "rb"), as_attachment=True)
        response["Content-Disposition"] = (
            'attachment; filename="SystemSpec_Template.xlsx"'
        )
        response["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        return response


@method_decorator(csrf_exempt, name="dispatch")
class UpdateLabourSpecView(View):
    """AJAX endpoint to update daily_production on a ProjectLabourSpecification."""

    def post(self, request, project_pk, pk):
        item = get_object_or_404(
            ProjectLabourSpecification, pk=pk, project_id=project_pk
        )
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        field = data.get("field")
        value = data.get("value")

        if field != "daily_production":
            return JsonResponse({"error": f'Field "{field}" not allowed'}, status=400)

        try:
            item.daily_production = Decimal(str(value))
        except Exception:
            return JsonResponse({"error": "Invalid value"}, status=400)

        item.save()

        def fmt(val):
            if val is None:
                return None
            return str(round(val, 2))

        return JsonResponse(
            {
                "ok": True,
                "daily_output": fmt(item.daily_output),
                "rate_per_unit": fmt(item.rate_per_unit),
                "daily_cost": fmt(item.daily_cost),
                "total_cost": fmt(item.total_cost),
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class UpdateLabourCrewView(View):
    """AJAX endpoint to update fields on a ProjectLabourCrew."""

    ALLOWED_FIELDS = {
        "crew_type": "str",
        "crew_size": "int",
        "skilled": "int",
        "semi_skilled": "int",
        "general": "int",
        "skilled_rate": "decimal",
        "semi_skilled_rate": "decimal",
        "general_rate": "decimal",
    }

    def post(self, request, project_pk, pk):
        item = get_object_or_404(ProjectLabourCrew, pk=pk, project_id=project_pk)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        field = data.get("field")
        value = data.get("value")

        if field not in self.ALLOWED_FIELDS:
            return JsonResponse({"error": f'Field "{field}" not allowed'}, status=400)

        field_type = self.ALLOWED_FIELDS[field]
        try:
            if field_type == "int":
                setattr(item, field, int(value))
            elif field_type == "decimal":
                setattr(item, field, Decimal(str(value)))
            else:
                setattr(item, field, str(value))
        except Exception:
            return JsonResponse({"error": "Invalid value"}, status=400)

        item.save()
        return JsonResponse(
            {
                "ok": True,
                "crew_daily_cost": str(round(item.crew_daily_cost, 2)),
            }
        )


# ── Simple Labour Spec Definition View ────────────────────────────


class LabourSpecDefListView(ProjectEstimatorMixin, ListView):
    """Simple labour specifications view — Section, Trade Name, Name, Unit, Crew."""

    model = ProjectLabourSpecification
    template_name = "estimator/labour_spec_def_list.html"
    context_object_name = "labour_specs"

    def get_queryset(self):
        project = self.get_project()
        qs = ProjectLabourSpecification.objects.filter(project=project).select_related(
            "crew"
        )

        section = self.request.GET.get("section")
        if section:
            qs = qs.filter(section=section)

        trade_name = self.request.GET.get("trade_name")
        if trade_name:
            qs = qs.filter(trade_name=trade_name)

        name = self.request.GET.get("name")
        if name:
            qs = qs.filter(name=name)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["form"] = context.get("form", LabourSpecificationForm(project=project))

        project_lspecs = ProjectLabourSpecification.objects.filter(project=project)
        context["sections"] = (
            project_lspecs.exclude(section="")
            .values_list("section", flat=True)
            .distinct()
            .order_by("section")
        )
        context["trade_names"] = (
            project_lspecs.exclude(trade_name="")
            .values_list("trade_name", flat=True)
            .distinct()
            .order_by("trade_name")
        )
        context["names"] = (
            project_lspecs.values_list("name", flat=True).distinct().order_by("name")
        )

        context["f_section"] = self.request.GET.get("section", "")
        context["f_trade_name"] = self.request.GET.get("trade_name", "")
        context["f_name"] = self.request.GET.get("name", "")

        return context

    def post(self, request, *args, **kwargs):
        project = self.get_project()
        form = LabourSpecificationForm(request.POST, project=project)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.project = project
            obj.save()
            return redirect(
                reverse(
                    "estimator:labour_spec_defs",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                )
            )
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))


# ── Upload / Download Template Views ──────────────────────────────


def _handle_upload(request, importer_class, success_url, entity_name, project=None):
    """Shared logic for all upload views."""
    uploaded = request.FILES.get("file")
    if not uploaded:
        messages.error(request, "No file provided.")
        return redirect(success_url)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    try:
        for chunk in uploaded.chunks():
            tmp.write(chunk)
        tmp.close()

        importer = importer_class(tmp.name, project=project)
        result = importer.run()

        created = result.get("created", 0)
        updated = result.get("updated", 0)
        messages.success(
            request, f"{entity_name} uploaded — {created} created, {updated} updated"
        )
    except Exception as e:
        messages.error(request, f"Import failed: {str(e)}")
    finally:
        os.unlink(tmp.name)

    return redirect(success_url)


def _generate_template(headers, filename):
    """Generate an Excel template with headers and return a FileResponse."""
    import io

    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"

    from openpyxl.styles import Alignment, Font, PatternFill

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(
        start_color="4472C4", end_color="4472C4", fill_type="solid"
    )

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[cell.column_letter].width = max(len(header) + 4, 14)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    wb.close()

    response = FileResponse(buffer, as_attachment=True)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Content-Type"] = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    return response


# ── Trade Codes Upload/Download ───────────────────────────────────


class TradeCodeUploadView(ProjectEstimatorMixin, FormView):
    template_name = "estimator/upload_generic.html"
    form_class = ExcelImportForm

    def get_success_url(self):
        return reverse(
            "estimator:trade_codes", kwargs={"project_pk": self.kwargs["project_pk"]}
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["parent_template"] = "estimator/base_baseline_costs.html"
        ctx["upload_title"] = "Upload Trade Codes"
        ctx["upload_description"] = (
            "Upload trade code prefixes and names from an Excel template."
        )
        ctx["download_url_name"] = "estimator:download_trade_code_template"
        ctx["columns"] = [
            ("Prefix", "Trade code prefix (e.g. CFR, PLB) — required, unique key"),
            ("Trade Name", "Trade name (e.g. Concrete, Plumbing)"),
        ]
        ctx["notes"] = [
            "Prefix is the unique key — existing trade codes with the same prefix will be updated.",
        ]
        return ctx

    def form_valid(self, form):
        from .importers import TradeCodeImporter

        return _handle_upload(
            self.request,
            TradeCodeImporter,
            self.get_success_url(),
            "Trade Codes",
            project=self.get_project(),
        )


class DownloadTradeCodeTemplateView(View):
    def get(self, request, project_pk):
        return _generate_template(["Prefix", "Trade Name"], "TradeCode_Template.xlsx")


# ── Material Costs Upload/Download ────────────────────────────────


class MaterialCostUploadView(ProjectEstimatorMixin, FormView):
    template_name = "estimator/upload_generic.html"
    form_class = ExcelImportForm

    def get_success_url(self):
        return reverse(
            "estimator:materials", kwargs={"project_pk": self.kwargs["project_pk"]}
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["parent_template"] = "estimator/base_baseline_costs.html"
        ctx["upload_title"] = "Upload Material Costs"
        ctx["upload_description"] = (
            "Upload material pricing data from an Excel template."
        )
        ctx["download_url_name"] = "estimator:download_material_cost_template"
        ctx["columns"] = [
            ("Trade Name", "Trade group (e.g. CFR-Concrete)"),
            ("Material Code", "Unique material code (required)"),
            ("Unit", "Unit of measurement (e.g. Bag, m3)"),
            ("Market Rate", "Current market price"),
            ("Material Variety", "Variety description"),
            ("Market Spec", "Market specification"),
        ]
        ctx["notes"] = [
            "Material Code is the unique key — existing materials with the same code will be updated.",
            "Market Rate must be a numeric value.",
        ]
        return ctx

    def form_valid(self, form):
        from .importers import MaterialCostImporter

        return _handle_upload(
            self.request,
            MaterialCostImporter,
            self.get_success_url(),
            "Material Costs",
            project=self.get_project(),
        )


class DownloadMaterialCostTemplateView(View):
    def get(self, request, project_pk):
        return _generate_template(
            [
                "Trade Name",
                "Material Code",
                "Unit",
                "Market Rate",
                "Material Variety",
                "Market Spec",
            ],
            "MaterialCost_Template.xlsx",
        )


# ── Labour Costs Upload/Download ─────────────────────────────────


class LabourCostUploadView(ProjectEstimatorMixin, FormView):
    template_name = "estimator/upload_generic.html"
    form_class = ExcelImportForm

    def get_success_url(self):
        return reverse(
            "estimator:labour_costs", kwargs={"project_pk": self.kwargs["project_pk"]}
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["parent_template"] = "estimator/base_baseline_costs.html"
        ctx["upload_title"] = "Upload Labour Costs"
        ctx["upload_description"] = "Upload labour crew compositions and daily rates."
        ctx["download_url_name"] = "estimator:download_labour_cost_template"
        ctx["columns"] = [
            ("Crew Type", "Unique crew identifier (required)"),
            ("Crew Size", "Total crew members"),
            ("Skilled", "Number of skilled workers"),
            ("Semi Skilled", "Number of semi-skilled workers"),
            ("General", "Number of general workers"),
            ("Skilled Rate", "Daily rate for skilled workers (R)"),
            ("Semi Skilled Rate", "Daily rate for semi-skilled workers (R)"),
            ("General Rate", "Daily rate for general workers (R)"),
        ]
        ctx["notes"] = [
            "Crew Type is the unique key — existing crews with the same type will be updated.",
            "Worker counts must be whole numbers. Rates must be numeric.",
        ]
        return ctx

    def form_valid(self, form):
        from .importers import LabourCostImporter

        return _handle_upload(
            self.request,
            LabourCostImporter,
            self.get_success_url(),
            "Labour Costs",
            project=self.get_project(),
        )


class DownloadLabourCostTemplateView(View):
    def get(self, request, project_pk):
        return _generate_template(
            [
                "Crew Type",
                "Crew Size",
                "Skilled",
                "Semi Skilled",
                "General",
                "Skilled Rate",
                "Semi Skilled Rate",
                "General Rate",
            ],
            "LabourCost_Template.xlsx",
        )


# ── Material Specs Upload/Download ───────────────────────────────


class MaterialSpecUploadView(ProjectEstimatorMixin, FormView):
    template_name = "estimator/upload_generic.html"
    form_class = ExcelImportForm

    def get_success_url(self):
        return reverse(
            "estimator:material_specs", kwargs={"project_pk": self.kwargs["project_pk"]}
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["parent_template"] = "estimator/base_materials_estimator.html"
        ctx["upload_title"] = "Upload Material Specifications"
        ctx["upload_description"] = (
            "Upload material specification definitions with component breakdowns."
        )
        ctx["download_url_name"] = "estimator:download_material_spec_template"
        ctx["columns"] = [
            (
                "Spec Name",
                "Specification name (required) — rows with the same name form one spec",
            ),
            ("Section", "Section grouping"),
            ("Trade Code Prefix", "Trade code prefix to link"),
            ("Unit", "Unit of measurement (e.g. m3)"),
            ("Material Code", "Material code for this component"),
            ("Label", "Component label (defaults to material code)"),
            ("Qty per Unit", "Quantity of material per unit of spec"),
        ]
        ctx["notes"] = [
            "Multi-row format: multiple rows with the same Spec Name define one specification's components.",
            "Section, Trade Code Prefix, and Unit are taken from the first row of each spec.",
            "All referenced materials must exist in Material Costs before uploading.",
            "Existing specs with the same name will have their components replaced.",
        ]
        return ctx

    def form_valid(self, form):
        from .importers import MaterialSpecImporter

        return _handle_upload(
            self.request,
            MaterialSpecImporter,
            self.get_success_url(),
            "Material Specifications",
            project=self.get_project(),
        )


class DownloadMaterialSpecTemplateView(View):
    def get(self, request, project_pk):
        return _generate_template(
            [
                "Spec Name",
                "Section",
                "Trade Code Prefix",
                "Unit",
                "Material Code",
                "Label",
                "Qty per Unit",
            ],
            "MaterialSpec_Template.xlsx",
        )


# ── Labour Specs Upload/Download ─────────────────────────────────


class LabourSpecUploadView(ProjectEstimatorMixin, FormView):
    template_name = "estimator/upload_generic.html"
    form_class = ExcelImportForm

    def get_success_url(self):
        return reverse(
            "estimator:labour_spec_defs",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["parent_template"] = "estimator/base_labour_estimator.html"
        ctx["upload_title"] = "Upload Labour Specifications"
        ctx["upload_description"] = (
            "Upload labour specification definitions with crew assignments and factors."
        )
        ctx["download_url_name"] = "estimator:download_labour_spec_template"
        ctx["columns"] = [
            ("Section", "Section grouping"),
            ("Trade Name", "Trade name"),
            ("Name", "Specification name (required, unique key)"),
            ("Unit", "Unit of measurement (e.g. m3)"),
            ("Crew Type", "Crew type to link (must exist in Labour Costs)"),
            ("Daily Production", "Base daily production rate"),
            ("Team Mix", "Team mix factor (default 1)"),
            ("Site Factor", "Site condition factor (default 1)"),
            ("Tools Factor", "Tools & equipment factor (default 1)"),
            ("Leadership Factor", "Leadership factor (default 1)"),
        ]
        ctx["notes"] = [
            "Name is the unique key — existing specs with the same name will be updated.",
            "All referenced Crew Types must exist in Labour Costs before uploading.",
            "Factor fields default to 1 if left blank.",
        ]
        return ctx

    def form_valid(self, form):
        from .importers import LabourSpecImporter

        return _handle_upload(
            self.request,
            LabourSpecImporter,
            self.get_success_url(),
            "Labour Specifications",
            project=self.get_project(),
        )


class DownloadLabourSpecTemplateView(View):
    def get(self, request, project_pk):
        return _generate_template(
            [
                "Section",
                "Trade Name",
                "Name",
                "Unit",
                "Crew Type",
                "Daily Production",
                "Team Mix",
                "Site Factor",
                "Tools Factor",
                "Leadership Factor",
            ],
            "LabourSpec_Template.xlsx",
        )


# ── Initialize Estimator ─────────────────────────────────────────


class InitializeEstimatorView(ProjectEstimatorMixin, View):
    """Clone system library into project-scoped records."""

    def post(self, request, project_pk):
        from .services import initialize_project_estimator

        project = self.get_project()
        try:
            result = initialize_project_estimator(project)
            messages.success(
                request,
                (
                    f"Estimator initialized — "
                    f"{result['trade_codes']} trade codes, "
                    f"{result['materials']} materials, "
                    f"{result['labour_crews']} labour crews, "
                    f"{result['specifications']} specifications, "
                    f"{result['labour_specs']} labour specs"
                ),
            )
        except Exception as e:
            messages.error(request, f"Initialization failed: {e}")
        return redirect(
            reverse("estimator:dashboard", kwargs={"project_pk": project_pk})
        )


# ══════════════════════════════════════════════════════════════════════
# System Library Views
# ══════════════════════════════════════════════════════════════════════


class SystemLibraryMixin(UserPassesTestMixin, ContextMixin):
    """Mixin for system library views: requires staff."""

    def test_func(self):
        request = getattr(self, "request", None)
        return request and request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_system_view"] = True
        return context


# ── System Trade Codes ────────────────────────────────────────────────


class SystemTradeCodeListView(SystemLibraryMixin, ListView):
    model = SystemTradeCode
    template_name = "estimator/system/trade_code_list.html"
    context_object_name = "trade_codes"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = context.get("form", SystemTradeCodeForm())
        return context

    def post(self, request, *args, **kwargs):
        form = SystemTradeCodeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("estimator:sys_trade_codes"))
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))


class SystemTradeCodeUploadView(SystemLibraryMixin, FormView):
    template_name = "estimator/upload_generic.html"
    form_class = ExcelImportForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["upload_title"] = "Upload Trade Codes"
        context["upload_description"] = (
            "Upload trade code prefixes and names from an Excel template."
        )
        context["parent_template"] = "estimator/system/base_system.html"
        context["download_url_name"] = "estimator:sys_download_trade_code_template"
        return context

    def form_valid(self, form):
        from .importers import TradeCodeImporter

        return _handle_upload(
            self.request, TradeCodeImporter, "estimator:sys_trade_codes", "Trade Codes"
        )


class DownloadSystemTradeCodeTemplateView(SystemLibraryMixin, View):
    def get(self, request):
        return _generate_template(
            ["Prefix", "Trade Name"],
            "system_trade_codes_template.xlsx",
        )


# ── System Materials ──────────────────────────────────────────────────


class SystemMaterialListView(SystemLibraryMixin, ListView):
    model = SystemMaterial
    template_name = "estimator/system/material_list.html"
    context_object_name = "materials"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = context.get("form", SystemMaterialForm())
        return context

    def post(self, request, *args, **kwargs):
        form = SystemMaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("estimator:sys_materials"))
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(csrf_exempt, name="dispatch")
class UpdateSystemMaterialView(View):
    ALLOWED_FIELDS = {
        "market_rate",
        "trade_name",
        "material_code",
        "unit",
        "material_variety",
        "market_spec",
    }

    def post(self, request, pk):
        if not request.user.is_staff:
            return JsonResponse({"error": "Forbidden"}, status=403)
        mat = get_object_or_404(SystemMaterial, pk=pk)
        data = json.loads(request.body)
        field, value = data.get("field"), data.get("value")
        if field not in self.ALLOWED_FIELDS:
            return JsonResponse({"error": "Invalid field"}, status=400)
        setattr(mat, field, value)
        mat.save()
        return JsonResponse({"ok": True})


class SystemMaterialUploadView(SystemLibraryMixin, FormView):
    template_name = "estimator/upload_generic.html"
    form_class = ExcelImportForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["upload_title"] = "Upload Materials"
        context["upload_description"] = (
            "Upload material pricing data from an Excel template."
        )
        context["parent_template"] = "estimator/system/base_system.html"
        context["download_url_name"] = "estimator:sys_download_material_template"
        return context

    def form_valid(self, form):
        from .importers import MaterialCostImporter

        return _handle_upload(
            self.request, MaterialCostImporter, "estimator:sys_materials", "Materials"
        )


class DownloadSystemMaterialTemplateView(SystemLibraryMixin, View):
    def get(self, request):
        return _generate_template(
            [
                "Trade Name",
                "Material Code",
                "Unit",
                "Market Rate",
                "Material Variety",
                "Market Spec",
            ],
            "system_materials_template.xlsx",
        )


# ── System Material Specs ─────────────────────────────────────────────


class SysMaterialSpecListView(SystemLibraryMixin, ListView):
    model = SystemSpecification
    template_name = "estimator/system/material_spec_list.html"
    context_object_name = "specs"

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("trade_code")
            .prefetch_related("spec_components__material")
        )
        section = self.request.GET.get("section")
        if section:
            qs = qs.filter(section=section)
        trade_code = self.request.GET.get("trade_code")
        if trade_code:
            qs = qs.filter(trade_code__id=trade_code)
        name = self.request.GET.get("name")
        if name:
            qs = qs.filter(name=name)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .forms import SystemSpecificationComponentFormSet, SystemSpecificationForm

        context["spec_form"] = context.get("spec_form", SystemSpecificationForm())
        context["component_formset"] = context.get(
            "component_formset", SystemSpecificationComponentFormSet()
        )

        all_specs = SystemSpecification.objects.all()
        context["sections"] = (
            all_specs.exclude(section="")
            .values_list("section", flat=True)
            .distinct()
            .order_by("section")
        )
        context["trade_codes"] = SystemTradeCode.objects.all()
        context["names"] = (
            all_specs.values_list("name", flat=True).distinct().order_by("name")
        )
        context["f_section"] = self.request.GET.get("section", "")
        context["f_trade_code"] = self.request.GET.get("trade_code", "")
        context["f_name"] = self.request.GET.get("name", "")
        return context

    def post(self, request, *args, **kwargs):
        from .forms import SystemSpecificationComponentFormSet, SystemSpecificationForm

        spec_form = SystemSpecificationForm(request.POST)
        component_formset = SystemSpecificationComponentFormSet(request.POST)
        if spec_form.is_valid():
            spec = spec_form.save()
            component_formset = SystemSpecificationComponentFormSet(
                request.POST, instance=spec
            )
            if component_formset.is_valid():
                component_formset.save()
                return redirect(reverse("estimator:sys_material_specs"))
            else:
                spec.delete()
        self.object_list = self.get_queryset()
        return self.render_to_response(
            self.get_context_data(
                spec_form=spec_form, component_formset=component_formset
            )
        )


class SystemMaterialSpecUploadView(SystemLibraryMixin, FormView):
    template_name = "estimator/upload_generic.html"
    form_class = ExcelImportForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["upload_title"] = "Upload Material Specs"
        context["upload_description"] = (
            "Upload material specification definitions with component breakdowns."
        )
        context["parent_template"] = "estimator/system/base_system.html"
        context["download_url_name"] = "estimator:sys_download_material_spec_template"
        context["columns"] = [
            (
                "Spec Name",
                "Name of the material specification (rows with same name are grouped)",
            ),
            ("Section", "Section grouping"),
            ("Trade Code Prefix", "Trade code prefix for lookup"),
            ("Unit", "Unit of measure (e.g. m3, m2)"),
            ("Material Code", "Material code to link component"),
            ("Label", "Display label for component"),
            ("Qty per Unit", "Quantity of material per spec unit"),
        ]
        return context

    def form_valid(self, form):
        from .importers import MaterialSpecImporter

        return _handle_upload(
            self.request,
            MaterialSpecImporter,
            "estimator:sys_material_specs",
            "Material Specs",
        )


class DownloadSystemMaterialSpecTemplateView(SystemLibraryMixin, View):
    def get(self, request):
        return _generate_template(
            [
                "Spec Name",
                "Section",
                "Trade Code Prefix",
                "Unit",
                "Material Code",
                "Label",
                "Qty per Unit",
            ],
            "system_material_specs_template.xlsx",
        )


@method_decorator(csrf_exempt, name="dispatch")
class UpdateSysSpecComponentView(View):
    def post(self, request, pk):
        if not request.user.is_staff:
            return JsonResponse({"error": "Forbidden"}, status=403)
        comp = get_object_or_404(SystemSpecificationComponent, pk=pk)
        data = json.loads(request.body)
        field, value = data.get("field"), data.get("value")
        if field != "qty_per_unit":
            return JsonResponse({"error": "Invalid field"}, status=400)
        comp.qty_per_unit = Decimal(value)
        comp.save()
        spec = comp.specification
        return JsonResponse({"ok": True, "rate_per_unit": str(spec.rate_per_unit)})


# ── System Labour Crews ───────────────────────────────────────────────


class SystemLabourCrewListView(SystemLibraryMixin, ListView):
    model = SystemLabourCrew
    template_name = "estimator/system/labour_crew_list.html"
    context_object_name = "crews"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = context.get("form", SystemLabourCrewForm())
        return context

    def post(self, request, *args, **kwargs):
        form = SystemLabourCrewForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("estimator:sys_labour_crews"))
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(csrf_exempt, name="dispatch")
class UpdateSystemLabourCrewView(View):
    ALLOWED_FIELDS = {
        "crew_type",
        "crew_size",
        "skilled",
        "semi_skilled",
        "general",
        "daily_production",
        "skilled_rate",
        "semi_skilled_rate",
        "general_rate",
    }

    def post(self, request, pk):
        if not request.user.is_staff:
            return JsonResponse({"error": "Forbidden"}, status=403)
        crew = get_object_or_404(SystemLabourCrew, pk=pk)
        data = json.loads(request.body)
        field, value = data.get("field"), data.get("value")
        if field not in self.ALLOWED_FIELDS:
            return JsonResponse({"error": "Invalid field"}, status=400)
        setattr(crew, field, value)
        crew.save()
        return JsonResponse({"ok": True, "crew_daily_cost": str(crew.crew_daily_cost)})


class SystemLabourCrewUploadView(SystemLibraryMixin, FormView):
    template_name = "estimator/upload_generic.html"
    form_class = ExcelImportForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["upload_title"] = "Upload Labour Crews"
        context["upload_description"] = (
            "Upload labour crew compositions and daily rates."
        )
        context["parent_template"] = "estimator/system/base_system.html"
        context["download_url_name"] = "estimator:sys_download_labour_crew_template"
        return context

    def form_valid(self, form):
        from .importers import LabourCostImporter

        return _handle_upload(
            self.request,
            LabourCostImporter,
            "estimator:sys_labour_crews",
            "Labour Crews",
        )


class DownloadSystemLabourCrewTemplateView(SystemLibraryMixin, View):
    def get(self, request):
        return _generate_template(
            [
                "Crew Type",
                "Crew Size",
                "Skilled",
                "Semi Skilled",
                "General",
                "Daily Production",
                "Skilled Rate",
                "Semi Skilled Rate",
                "General Rate",
            ],
            "system_labour_crews_template.xlsx",
        )


# ── System Labour Specs ───────────────────────────────────────────────


class SystemLabourSpecListView(SystemLibraryMixin, ListView):
    model = SystemLabourSpecification
    template_name = "estimator/system/labour_spec_list.html"
    context_object_name = "labour_specs"

    def get_queryset(self):
        qs = super().get_queryset().select_related("crew")
        section = self.request.GET.get("section")
        if section:
            qs = qs.filter(section=section)
        trade_name = self.request.GET.get("trade_name")
        if trade_name:
            qs = qs.filter(trade_name=trade_name)
        name = self.request.GET.get("name")
        if name:
            qs = qs.filter(name=name)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = context.get("form", SystemLabourSpecificationForm())
        all_specs = SystemLabourSpecification.objects.all()
        context["sections"] = (
            all_specs.exclude(section="")
            .values_list("section", flat=True)
            .distinct()
            .order_by("section")
        )
        context["trade_names"] = (
            all_specs.exclude(trade_name="")
            .values_list("trade_name", flat=True)
            .distinct()
            .order_by("trade_name")
        )
        context["names"] = (
            all_specs.values_list("name", flat=True).distinct().order_by("name")
        )
        context["f_section"] = self.request.GET.get("section", "")
        context["f_trade_name"] = self.request.GET.get("trade_name", "")
        context["f_name"] = self.request.GET.get("name", "")
        return context

    def post(self, request, *args, **kwargs):
        form = SystemLabourSpecificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("estimator:sys_labour_specs"))
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(csrf_exempt, name="dispatch")
class UpdateSystemLabourSpecView(View):
    ALLOWED_FIELDS = {
        "daily_production",
        "team_mix",
        "site_factor",
        "tools_factor",
        "leadership_factor",
    }

    def post(self, request, pk):
        if not request.user.is_staff:
            return JsonResponse({"error": "Forbidden"}, status=403)
        ls = get_object_or_404(SystemLabourSpecification, pk=pk)
        data = json.loads(request.body)
        field, value = data.get("field"), data.get("value")
        if field not in self.ALLOWED_FIELDS:
            return JsonResponse({"error": "Invalid field"}, status=400)
        setattr(ls, field, Decimal(value))
        ls.save()
        return JsonResponse(
            {
                "ok": True,
                "daily_output": str(ls.daily_output),
                "daily_cost": str(ls.daily_cost),
                "rate_per_unit": str(ls.rate_per_unit),
            }
        )


class SystemLabourSpecUploadView(SystemLibraryMixin, FormView):
    template_name = "estimator/upload_generic.html"
    form_class = ExcelImportForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["upload_title"] = "Upload Labour Specifications"
        context["upload_description"] = (
            "Upload labour specification definitions with crew assignments and factors."
        )
        context["parent_template"] = "estimator/system/base_system.html"
        context["download_url_name"] = "estimator:sys_download_labour_spec_template"
        return context

    def form_valid(self, form):
        from .importers import LabourSpecImporter

        return _handle_upload(
            self.request,
            LabourSpecImporter,
            "estimator:sys_labour_specs",
            "Labour Specifications",
        )


class DownloadSystemLabourSpecTemplateView(SystemLibraryMixin, View):
    def get(self, request):
        return _generate_template(
            [
                "Section",
                "Trade Name",
                "Name",
                "Unit",
                "Crew Type",
                "Daily Production",
                "Team Mix",
                "Site Factor",
                "Tools Factor",
                "Leadership Factor",
            ],
            "system_labour_specs_template.xlsx",
        )
