from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    TemplateView,
    UpdateView,
)

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project

from ..production_forms import (
    AggregatedLabourFormSet,
    DailyPlantUsageFormSet,
    ProductionPlanForm,
    ProductionResourceForm,
)
from ..production_models import (
    ProductionPlan,
    ProductionResource,
)


class ProductionPlanningView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, CreateView
):
    """Provides a schedule dashboard to plan daily production targets."""

    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = "production_progress/plan/planning.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project_id"] = self.kwargs["project_pk"]
        return kwargs

    def get_success_url(self):
        return reverse_lazy(
            "project:production-dashboard",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        context["plans"] = ProductionPlan.objects.filter(
            project_id=self.kwargs["project_pk"], is_archived=False
        ).prefetch_related("resources")
        return context

    def form_valid(self, form):
        project_pk = self.kwargs.get("project_pk")
        project = get_object_or_404(Project, pk=project_pk)
        form.instance.project = project

        try:
            response = super().form_valid(form)
            messages.success(self.request, "Production plan saved successfully.")
            return response
        except Exception as e:
            messages.error(self.request, f"Database error: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Error in {field}: {error}")
        return super().form_invalid(form)


class ProductionPlanDetailView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """Shows a single production plan detail."""

    model = ProductionPlan
    template_name = "production_progress/plan/plan_detail.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        return ProductionPlan.objects.filter(project_id=self.kwargs["project_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.get_object()
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])

        resource_categories = []
        for type_code, type_name in ProductionResource.RESOURCE_TYPES:
            resources = plan.resources.filter(resource_type=type_code)
            total_cost = 0
            if type_code == "LABOUR":
                total_cost = plan.total_labour_cost
            elif type_code == "PLANT":
                total_cost = plan.total_plant_cost
            else:
                total_cost = plan.total_other_cost

            resource_categories.append(
                {
                    "type_code": type_code,
                    "type_name": type_name,
                    "resources": resources,
                    "total_cost": total_cost,
                }
            )

        context["resource_categories"] = resource_categories
        return context


class ProductionPlanUpdateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, UpdateView
):
    """Edit an existing production plan item."""

    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = "production_progress/plan/planning.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project_id"] = self.kwargs["project_pk"]
        return kwargs

    def get_queryset(self):
        return ProductionPlan.objects.filter(project_id=self.kwargs["project_pk"])

    def get_success_url(self):
        return reverse_lazy(
            "project:production-dashboard",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        context["plans"] = ProductionPlan.objects.filter(
            project_id=self.kwargs["project_pk"], is_archived=False
        ).prefetch_related("resources")
        context["is_update"] = True
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Production plan updated successfully.")
            return response
        except Exception as e:
            messages.error(self.request, f"Database error: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Error in {field}: {error}")
        return super().form_invalid(form)


class ProductionPlanDeleteView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DeleteView
):
    """Delete an existing production plan item."""

    model = ProductionPlan
    template_name = "production_progress/plan/plan_confirm_delete.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        return ProductionPlan.objects.filter(project_id=self.kwargs["project_pk"])

    def get_success_url(self):
        return reverse_lazy(
            "project:production-dashboard",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_archived = True
        self.object.save()
        messages.success(
            request, f"Production plan '{self.object.activity}' archived successfully."
        )
        return redirect(str(self.get_success_url()))


class ProductionCostBreakdownView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """Financial analysis view showing the actual cost breakdown vs budget totals."""

    template_name = "production_progress/plan/cost_breakdown.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = Project.objects.get(pk=self.kwargs["project_pk"])
        context["project"] = project

        all_plans = ProductionPlan.objects.filter(project=project).order_by("activity")
        plan_id = self.request.GET.get("plan_id")

        selected_plan = None
        if plan_id:
            try:
                selected_plan = all_plans.get(pk=plan_id)
            except (ProductionPlan.DoesNotExist, ValueError):
                pass

        context["all_plans"] = all_plans
        context["selected_plan"] = selected_plan
        context["plans"] = [selected_plan] if selected_plan else []

        initial = {}
        if selected_plan:
            initial["production_plan"] = selected_plan

        context["resource_form"] = ProductionResourceForm(
            project_id=project.pk, initial=initial
        )
        return context

    def post(self, request, *args, **kwargs):
        project_pk = self.kwargs["project_pk"]
        action = request.POST.get("action")

        if action == "delete":
            resource_id = request.POST.get("resource_id")
            try:
                resource = ProductionResource.objects.get(id=resource_id)
                resource_name = resource.name
                resource.delete()
                messages.success(
                    request, f"Resource '{resource_name}' deleted successfully."
                )
            except ProductionResource.DoesNotExist:
                messages.error(request, "Resource not found.")

        return redirect("project:production-cost-breakdown", project_pk=project_pk)


class ProductionResourceCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, CreateView
):
    """Form to add a production resource."""

    model = ProductionResource
    form_class = ProductionResourceForm
    template_name = "production_progress/plan/production_resource_form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_success_url(self):
        url = reverse_lazy(
            "project:production-cost-breakdown",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )
        plan_id = self.request.GET.get("plan_id")
        if plan_id:
            return f"{url}?plan_id={plan_id}"
        return url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project_id"] = self.kwargs["project_pk"]

        disabled_fields = []
        if self.request.GET.get("plan_id") or (
            self.request.method == "POST" and self.request.POST.get("production_plan")
        ):
            disabled_fields.append("production_plan")
        if self.request.GET.get("type") or (
            self.request.method == "POST" and self.request.POST.get("resource_type")
        ):
            disabled_fields.append("resource_type")

        kwargs["disabled_fields"] = disabled_fields
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        plan_id = self.request.GET.get("plan_id") or self.request.POST.get(
            "production_plan"
        )
        resource_type = self.request.GET.get("type") or self.request.POST.get(
            "resource_type"
        )

        if plan_id:
            initial["production_plan"] = plan_id
        if resource_type:
            initial["resource_type"] = resource_type

        return initial

    def form_valid(self, form):
        resource = form.save()
        messages.success(
            self.request, f"Resource '{resource.name}' added successfully."
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = Project.objects.get(pk=self.kwargs["project_pk"])
        context["project"] = project

        plan_id = self.request.GET.get("plan_id")
        if not plan_id and self.request.method == "POST":
            plan_id = self.request.POST.get("production_plan")

        if plan_id:
            try:
                context["production_plan"] = ProductionPlan.objects.get(
                    pk=plan_id, project=project
                )
            except (ProductionPlan.DoesNotExist, ValueError):
                pass

        return context


class PlanResourcesAjaxView(
    SubscriptionRequiredMixin, LoginRequiredMixin, TemplateView
):
    """
    Returns the Labour and Plant formsets for given plan_ids as an AJAX fragment.
    """

    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get(self, request, *args, **kwargs):
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        plan_ids_raw = request.GET.getlist("plan_ids")
        plan_ids = []
        for item in plan_ids_raw:
            plan_ids.extend([pid.strip() for pid in item.split(",") if pid.strip()])

        selected_plans = ProductionPlan.objects.filter(
            id__in=plan_ids, project=project
        ).order_by("id")

        plan_resources = {}
        plant_formsets = {}

        for plan in selected_plans:
            has_skilled = ProductionResource.objects.filter(
                production_plan=plan,
                resource_type="LABOUR",
                skill_type__name__icontains="skilled",
            ).exists()
            has_semi_skilled = ProductionResource.objects.filter(
                production_plan=plan,
                resource_type="LABOUR",
                skill_type__name__icontains="semi",
            ).exists()
            has_unskilled = ProductionResource.objects.filter(
                production_plan=plan,
                resource_type="LABOUR",
                skill_type__name__icontains="unskilled",
            ).exists()
            has_plant = ProductionResource.objects.filter(
                production_plan=plan, resource_type="PLANT"
            ).exists()

            plan_resources[plan.id] = {
                "skilled": has_skilled,
                "semi_skilled": has_semi_skilled,
                "unskilled": has_unskilled,
                "plant": has_plant,
            }

            planned_plants = ProductionResource.objects.filter(
                production_plan=plan, resource_type="PLANT"
            )
            plant_initial = [
                {
                    "resource": res.id,
                    "number": int(res.number),
                    "hours": 8.0,
                    "activity": plan.id,
                }
                for res in planned_plants
            ]
            plant_formset = DailyPlantUsageFormSet(
                prefix=f"plant_{plan.id}", initial=plant_initial
            )
            for f in plant_formset.forms:
                f.fields["resource"].queryset = planned_plants
                f.fields["activity"].queryset = ProductionPlan.objects.filter(
                    id=plan.id
                )
            plant_formsets[plan.id] = plant_formset

        labour_initial = [{"activity": plan.id} for plan in selected_plans]
        labour_formset = AggregatedLabourFormSet(
            prefix="labour", initial=labour_initial
        )

        for form, plan in zip(labour_formset.forms, selected_plans, strict=True):
            form.fields["activity"].queryset = ProductionPlan.objects.filter(id=plan.id)
            if not plan_resources[plan.id]["skilled"]:
                form.fields["skilled_number"].disabled = True
            if not plan_resources[plan.id]["semi_skilled"]:
                form.fields["semi_skilled_number"].disabled = True
            if not plan_resources[plan.id]["unskilled"]:
                form.fields["unskilled_number"].disabled = True

        html = render_to_string(
            "production_progress/partials/resource_formsets_multi.html",
            {
                "labour_formset": labour_formset,
                "plant_formsets": plant_formsets,
                "selected_plans": selected_plans,
                "plan_resources": plan_resources,
                "labour_forms_with_plans": list(
                    zip(labour_formset.forms, selected_plans, strict=True)
                ),
            },
            request=request,
        )
        return JsonResponse({"html": html})
