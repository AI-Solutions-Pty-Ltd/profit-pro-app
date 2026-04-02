import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project

from ..forms.production_forms import (
    DailyProductionForm,
    ProductionPlanForm,
    ProductionResourceForm,
)
from ..models.production_models import (
    DailyActivityEntry,
    DailyActivityReport,
    DailyLabourUsage,
    DailyProduction,
    ProductionPlan,
    ProductionResource,
)
from .utils import (
    get_activity_detail_data,
    get_dashboard_data,
    get_forecasting_dashboard_data,
    get_plan_productivity_data,
)


class ProductionDashboardView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, ListView
):
    """Summarizes daily logs, cumulative progress vs budget."""

    model = DailyProduction
    template_name = "production_progress/dashboard.html"
    context_object_name = "productions"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        return DailyProduction.objects.filter(
            project_id=self.kwargs["project_pk"],
            # archived plans should probably be excluded from main lists
        ).select_related("project")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])

        # Get filter parameters
        activity_filter = self.request.GET.get("activity", "").strip()
        start_date_filter = self.request.GET.get("start_date", "").strip()
        finish_date_filter = self.request.GET.get("finish_date", "").strip()

        # Build queryset with filters
        plans = ProductionPlan.objects.filter(
            project_id=self.kwargs["project_pk"], is_archived=False
        ).prefetch_related("resources")

        if activity_filter:
            plans = plans.filter(activity__icontains=activity_filter)

        if start_date_filter:
            plans = plans.filter(start_date__gte=start_date_filter)

        if finish_date_filter:
            plans = plans.filter(finish_date__lte=finish_date_filter)

        context["plans"] = plans
        context["activity_filter"] = activity_filter
        context["start_date_filter"] = start_date_filter
        context["finish_date_filter"] = finish_date_filter

        return context


class ProductionProgressDashboardView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """
    Electronic Production Progress Dashboard.
    Provides a high-level overview of all production activities.
    """

    template_name = "production_progress/production_progress_dashboard.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        # Filters
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        status_filter = self.request.GET.get("status")

        # Get data from utils
        dashboard_data = get_dashboard_data(project_pk, start_date, end_date)

        # Filter item cards by status if requested
        if status_filter:
            dashboard_data["item_cards"] = [
                card
                for card in dashboard_data["item_cards"]
                if card["status_text"] == status_filter
            ]

        context.update(
            {
                "project": project,
                **dashboard_data,
                "start_date": start_date,
                "end_date": end_date,
                "status_filter": status_filter,
            }
        )
        return context


class ProductionActivityDetailView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """
    Detailed Electronic Progress Dashboard for a single activity.
    """

    model = ProductionPlan
    template_name = "production_progress/plan_progress_detail.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        # Get detailed metrics from utils
        activity_data = get_activity_detail_data(self.object.pk)

        context.update(
            {
                "project": project,
                **activity_data,
            }
        )
        return context


class ProductionPlanningView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, CreateView
):
    """Provides a schedule dashboard to plan daily production targets."""

    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = "production_progress/planning.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

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
    template_name = "production_progress/plan_detail.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        return ProductionPlan.objects.filter(project_id=self.kwargs["project_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.get_object()
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])

        # Prepare structured resource categories for the template
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
    template_name = "production_progress/planning.html"
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
    template_name = "production_progress/plan_confirm_delete.html"
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

    template_name = "production_progress/cost_breakdown.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = Project.objects.get(pk=self.kwargs["project_pk"])
        context["project"] = project

        # Selection logic: get specific plan if plan_id is provided
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
        # If a plan is selected, only pass that one to the 'plans' context for display
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
    template_name = "production_progress/production_resource_form.html"
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

        # Determine which fields should be read-only based on query parameters
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

        # In Django, if a field is disabled, it must be provided in initial
        # so that it holds its value during validation/POST re-rendering.
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

        # Try to get plan_id from GET and then from POST (e.g. on validation error)
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


class DailyProductionCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, CreateView
):
    """Form to log daily quantities."""

    model = DailyProduction
    form_class = DailyProductionForm
    template_name = "production_progress/production_form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_success_url(self):
        return reverse_lazy(
            "project:production-dashboard",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def form_valid(self, form):
        form.instance.project_id = self.kwargs["project_pk"]
        return super().form_valid(form)


class DailyProductivityCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """View to handle the composite Daily Productivity Form."""

    template_name = "production_progress/productivity_form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, post_data=None, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        context["project"] = project
        context["all_plans"] = ProductionPlan.objects.filter(
            project=project, is_archived=False
        )

        selected_plans_ids = self.request.POST.getlist("selected_plans")
        if not selected_plans_ids:
            selected_plans_ids = self.request.GET.getlist("selected_plans")

        selected_plans = (
            ProductionPlan.objects.filter(
                id__in=selected_plans_ids, project=project
            ).order_by("id")
            if selected_plans_ids
            else ProductionPlan.objects.none()
        )
        context["selected_plans"] = selected_plans
        context["selected_plans_ids"] = [
            int(sid) for sid in selected_plans_ids if str(sid).isdigit()
        ]

        from ..forms.production_forms import (
            AggregatedLabourFormSet,
            DailyActivityReportForm,
            DailyPlantUsageFormSet,
        )

        plan_resources = {}
        plant_formsets = {}

        for plan in selected_plans:
            resources = ProductionResource.objects.filter(production_plan=plan)
            plan_resources[plan.id] = {
                "skilled": resources.filter(
                    resource_type="LABOUR", skill_type__name__icontains="skilled"
                ).exists(),
                "semi_skilled": resources.filter(
                    resource_type="LABOUR", skill_type__name__icontains="semi"
                ).exists(),
                "unskilled": resources.filter(
                    resource_type="LABOUR", skill_type__name__icontains="unskilled"
                ).exists(),
                "plant": resources.filter(resource_type="PLANT").exists(),
            }

            planned_plants = resources.filter(resource_type="PLANT")
            plant_initial = [
                {"resource": res.id, "number": int(res.number), "hours": 8.0}
                for res in planned_plants
            ]

            p_prefix = f"plant_{plan.id}"
            if post_data:
                p_formset = DailyPlantUsageFormSet(
                    post_data, prefix=p_prefix, form_kwargs={"activity_id": plan.id}
                )
            else:
                p_formset = DailyPlantUsageFormSet(
                    prefix=p_prefix,
                    initial=plant_initial,
                    form_kwargs={"activity_id": plan.id},
                )

            for f in p_formset.forms:
                f.fields["resource"].queryset = planned_plants  # type: ignore[attr]
                # Ensure activity hidden field is set
                f.fields["activity"].initial = plan.id
                f.fields["activity"].queryset = ProductionPlan.objects.filter(  # type: ignore[attr]
                    id=plan.id
                )
            plant_formsets[plan.id] = p_formset

        context["plan_resources"] = plan_resources
        context["plant_formsets"] = plant_formsets

        # Labour Formset
        labour_initial = [{"activity": plan.id} for plan in selected_plans]
        if post_data:
            labour_formset = AggregatedLabourFormSet(
                post_data, prefix="labour", form_kwargs={"project_id": project.id}
            )
        else:
            labour_formset = AggregatedLabourFormSet(
                prefix="labour",
                initial=labour_initial,
                form_kwargs={"project_id": project.id},
            )

        for form, plan in zip(labour_formset.forms, selected_plans, strict=False):
            form.fields["activity"].queryset = ProductionPlan.objects.filter(id=plan.id)  # type: ignore[attr]
            res_info = plan_resources[plan.id]
            if not res_info["skilled"]:
                form.fields["skilled_number"].disabled = True
            if not res_info["semi_skilled"]:
                form.fields["semi_skilled_number"].disabled = True
            if not res_info["unskilled"]:
                form.fields["unskilled_number"].disabled = True

        context["labour_formset"] = labour_formset
        context["labour_forms_with_plans"] = list(
            zip(labour_formset.forms, selected_plans, strict=False)
        )
        context["plant_formset"] = next(
            iter(plant_formsets.values()), None
        ) or DailyPlantUsageFormSet(prefix="plant")

        if post_data:
            context["report_form"] = DailyActivityReportForm(post_data)
        else:
            context["report_form"] = DailyActivityReportForm(
                initial={"date": timezone.now().date()}
            )

        return context

    def post(self, request, *args, **kwargs):
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        from ..forms.production_forms import (
            AggregatedLabourFormSet,
            DailyActivityReportForm,
            DailyPlantUsageFormSet,
        )

        # 1. Initialize forms
        report_form = DailyActivityReportForm(request.POST)
        labour_formset = AggregatedLabourFormSet(
            request.POST, prefix="labour", form_kwargs={"project_id": project.id}
        )

        selected_plans_ids = request.POST.getlist("selected_plans")
        selected_plans = ProductionPlan.objects.filter(
            id__in=selected_plans_ids, project=project
        ).order_by("id")
        plan_map = {str(p.id): p for p in selected_plans}

        # Populate labour querysets
        for form in labour_formset.forms:
            act_id = form.data.get(
                f"labour-{form.prefix}-activity"
            ) or form.initial.get("activity")
            if str(act_id) in plan_map:
                form.fields["activity"].queryset = ProductionPlan.objects.filter(  # type: ignore[attr]
                    id=act_id
                )

        # Initialize Plant Formsets
        plant_formsets = {}
        plant_valid = True
        for plan in selected_plans:
            p_prefix = f"plant_{plan.id}"
            # Safety check: skip if management data is missing
            if f"{p_prefix}-TOTAL_FORMS" not in request.POST:
                continue

            p_formset = DailyPlantUsageFormSet(
                request.POST, prefix=p_prefix, form_kwargs={"activity_id": plan.id}
            )

            planned_plants = ProductionResource.objects.filter(
                production_plan=plan, resource_type="PLANT"
            )
            for f in p_formset.forms:
                f.fields["resource"].queryset = planned_plants  # type: ignore[attr]
                f.fields["activity"].queryset = ProductionPlan.objects.filter(  # type: ignore[attr]
                    id=plan.id
                )

            plant_formsets[plan.id] = p_formset
            if not p_formset.is_valid():
                plant_valid = False

        # 2. Comprehensive Validation
        if report_form.is_valid() and labour_formset.is_valid() and plant_valid:
            try:
                with transaction.atomic():
                    report, _ = DailyActivityReport.objects.get_or_create(
                        project=project, date=report_form.cleaned_data["date"]
                    )

                    entries = {}

                    # Save Labour
                    for form in labour_formset:
                        if form.cleaned_data:
                            plan = form.cleaned_data["activity"]
                            entry, _ = DailyActivityEntry.objects.update_or_create(
                                report=report,
                                production_plan=plan,
                                defaults={
                                    "quantity": form.cleaned_data.get("quantity") or 0.0
                                },
                            )
                            entries[plan.id] = entry

                            entry.labour_usage.all().delete()

                            for name_part, number in [
                                ("skilled", form.cleaned_data.get("skilled_number")),
                                ("semi", form.cleaned_data.get("semi_skilled_number")),
                                (
                                    "unskilled",
                                    form.cleaned_data.get("unskilled_number"),
                                ),
                            ]:
                                if number and number > 0:
                                    res = ProductionResource.objects.filter(
                                        production_plan=plan,
                                        resource_type="LABOUR",
                                        skill_type__name__icontains=name_part,
                                    ).first()
                                    if res:
                                        DailyLabourUsage.objects.create(
                                            entry=entry,
                                            resource=res,
                                            number=number,
                                            hours=form.cleaned_data.get("total_hours")
                                            or 0.0,
                                        )

                    # Save Plants
                    for plan_id, p_fs in plant_formsets.items():
                        entry = entries.get(plan_id)
                        if not entry:
                            plan = plan_map.get(str(plan_id))
                            entry, _ = DailyActivityEntry.objects.update_or_create(
                                report=report,
                                production_plan=plan,
                                defaults={"quantity": 0},
                            )
                            entries[plan_id] = entry

                        for p_form in p_fs:
                            if p_form.cleaned_data:
                                if p_form.cleaned_data.get("DELETE", False):
                                    if p_form.instance.pk:
                                        p_form.instance.delete()
                                else:
                                    usage = p_form.save(commit=False)
                                    usage.entry = entry
                                    usage.save()

                    messages.success(
                        request, "Daily productivity logs saved successfully."
                    )
                    return redirect(
                        "project:production-dashboard", project_pk=project_pk
                    )

            except Exception as e:
                messages.error(request, f"Error during save: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form.")

        # 3. Fallback - Render with error state
        context = self.get_context_data(post_data=request.POST)
        context.update(
            {
                "report_form": report_form,
                "labour_formset": labour_formset,
                "plant_formsets": plant_formsets,
            }
        )
        return self.render_to_response(context)


class ProductivityLogsView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """Consolidated view for Labour Log, Plant Log, and Productivity Table."""

    template_name = "production_progress/productivity_logs.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        context["project"] = project

        # Get all plans for this project
        plans = ProductionPlan.objects.filter(project=project)

        # Get all entries for this project
        entries = DailyActivityEntry.objects.filter(report__project=project).order_by(
            "report__date"
        )

        # Organize data for Table 2C (Labour Log) and 2D (Plant Log)
        # We need to map dates to D1, D2 etc.
        # For simplicity, let's group by plan and then by day.

        logs_data = []
        for plan in plans:
            plan_entries = entries.filter(production_plan=plan)
            if not plan_entries.exists():
                continue

            labour_resources = ProductionResource.objects.filter(
                production_plan=plan, resource_type="LABOUR"
            )
            plant_resources = ProductionResource.objects.filter(
                production_plan=plan, resource_type="PLANT"
            )

            # Get unique day numbers from entries
            day_identifiers = sorted(
                {entry.day_number for entry in plan_entries},
                key=lambda x: int(x[1:]) if x[1:].isdigit() else 0,
            )

            day_data = {}
            for day_id in day_identifiers:
                # Find the entry that matches the day_id (D1, D2 etc)
                entry = next((e for e in plan_entries if e.day_number == day_id), None)
                if not entry:
                    continue

                labour_usage_map = {
                    usage.resource.id: usage.number
                    for usage in entry.labour_usage.all()
                }
                plant_usage_map = {
                    usage.resource.id: usage.number for usage in entry.plant_usage.all()
                }

                day_data[day_id] = {
                    "entry": entry,
                    "labour_usage": labour_usage_map,
                    "plant_usage": plant_usage_map,
                    "total_labourers": sum(
                        usage.number for usage in entry.labour_usage.all()
                    ),
                    "total_labour_cost": entry.total_labour_cost,
                    "avg_hours": sum(usage.hours for usage in entry.labour_usage.all())
                    / entry.labour_usage.count()
                    if entry.labour_usage.exists()
                    else 0,
                    "man_hours": entry.man_hours,
                    "total_plant_cost": entry.total_plant_cost,
                    "production": entry.quantity,
                    "total_cost": entry.total_cost,
                    "productivity": entry.work_productivity,
                    "cost_per_item": entry.cost_per_item,
                }

            logs_data.append(
                {
                    "plan": plan,
                    "days_list": day_identifiers,
                    "day_data": day_data,
                    "labour_resources": labour_resources,
                    "plant_resources": plant_resources,
                }
            )

        context["logs_data"] = logs_data
        return context


class ProgressTrackingView(ProductivityLogsView):
    """View to display the data from the analysis view, with daily breakdowns."""

    template_name = "production_progress/progress_tracking.html"


class PlanProductivityDashboardView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """
    Plan Productivity Dashboard.
    Compares planned production targets against actual performance.
    """

    template_name = "production_progress/plan_productivity_dashboard.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        # Filters
        plan_id = self.request.GET.get("plan_id")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        all_plans = ProductionPlan.objects.filter(project=project).order_by("activity")

        # Default to first plan if none selected
        selected_plan = None
        if plan_id:
            selected_plan = all_plans.filter(pk=plan_id).first()
        if not selected_plan and all_plans.exists():
            selected_plan = all_plans.first()

        # Get data from utils
        dashboard_data = get_plan_productivity_data(
            selected_plan.pk if selected_plan else None, start_date, end_date
        )

        context.update(
            {
                "project": project,
                "all_plans": all_plans,
                "selected_plan": selected_plan,
                "start_date": start_date,
                "end_date": end_date,
                **dashboard_data,
            }
        )
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

        from ..forms.production_forms import (
            AggregatedLabourFormSet,
            DailyPlantUsageFormSet,
        )

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
                f.fields["resource"].queryset = planned_plants  # type: ignore[att]
                f.fields["activity"].queryset = ProductionPlan.objects.filter(  # type: ignore[att]
                    id=plan.id
                )
            plant_formsets[plan.id] = plant_formset

        labour_initial = [{"activity": plan.id} for plan in selected_plans]
        labour_formset = AggregatedLabourFormSet(
            prefix="labour", initial=labour_initial
        )

        for form, plan in zip(labour_formset.forms, selected_plans, strict=True):
            form.fields["activity"].queryset = ProductionPlan.objects.filter(id=plan.id)  # type: ignore[att]
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


class ProductionForecastDashboardView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """
    Costing Forecasting Dashboard.
    Provides predictive analytics on project completion timelines and budget outcomes.
    """

    template_name = "production_progress/forecast_dashboard.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        # Filters
        plan_id = self.request.GET.get("plan_id")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        all_plans = ProductionPlan.objects.filter(project=project).order_by("activity")

        # Default to first plan if none selected
        selected_plan = None
        if plan_id:
            try:
                selected_plan = all_plans.filter(pk=plan_id).first()
            except (ValueError, TypeError):
                pass

        if not selected_plan and all_plans.exists():
            selected_plan = all_plans.first()

        # Get forecasting data from utils
        forecast_data = {}
        if selected_plan:
            forecast_data = get_forecasting_dashboard_data(
                selected_plan.pk, start_date, end_date
            )

        # Serialize chart data for JS
        charts_json = "{}"
        if "charts" in forecast_data:
            # We use a custom encoder or just ensure types are good in utils.py
            # Since I already updated utils.py to use floats/strings,
            # simple json.dumps should work.
            charts_json = json.dumps(forecast_data["charts"])

        context.update(
            {
                "project": project,
                "all_plans": all_plans,
                "selected_plan": selected_plan,
                "start_date": start_date,
                "end_date": end_date,
                **forecast_data,
                "charts_json": charts_json,
            }
        )
        return context
