import json
from collections import OrderedDict
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models as db_models
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
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
from app.Estimator.models import BOQItem, ProjectLabourSpecification
from app.Project.models import Project

from ..production_forms import (
    PlanDependencyFormSet,
    ProductionPlanForm,
    ProductionResourceForm,
)
from ..production_models import (
    ProductionPlan,
    ProductionResource,
)
from ..utils.production_utils import get_project_performance_summary


class ProductionPlanGanttView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """Renders a Gantt chart of all production plan activities."""

    template_name = "production_progress/reports/schedule_report.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {
                "title": "Production Planning",
                "url": reverse_lazy(
                    "project:production-planning", kwargs={"project_pk": project_pk}
                ),
            },
            {"title": "Schedule Report", "url": None},
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _flatten_tree(plans, parent_id=None, depth=0):
        """Return activities in pre-order (parent then children), with depth."""
        rows = []
        for plan in plans:
            if plan.parent_id == parent_id:
                rows.append((plan, depth))
                rows.extend(
                    ProductionPlanGanttView._flatten_tree(plans, plan.pk, depth + 1)
                )
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        context["project"] = project
        today = timezone.now().date()

        # Fetch basic performance data (PPI etc) for forecasting
        perf_data = get_project_performance_summary(project_pk)
        ppi = perf_data.get("ppi", 1.0)

        from django.db.models import Prefetch

        all_plans = list(
            ProductionPlan.objects.filter(
                project=project,
                is_archived=False,
                start_date__isnull=False,
                finish_date__isnull=False,
            )
            .select_related("labour_activity", "parent")
            .prefetch_related(
                "predecessors",
                "predecessors__predecessor",
                Prefetch(
                    "children",
                    queryset=ProductionPlan.objects.filter(deleted=False).order_by(
                        "start_date", "activity"
                    ),
                ),
                "daily_entries",
            )
            .order_by("start_date", "activity")
        )

        context["plans"] = all_plans
        context["root_plans"] = [p for p in all_plans if not p.parent_id]

        # Build flat ordered list with depth for the Gantt canvas
        ordered = self._flatten_tree(all_plans)
        edit_url_name = "project:production-plan-edit"

        gantt_data = []
        for plan, depth in ordered:
            # Forecasting Logic
            progress_pct = plan.progress_percentage
            forecast_finish_date = plan.finish_date

            if progress_pct > 0 and plan.is_leaf:
                total_produced = (
                    plan.daily_entries.aggregate(total=Sum("quantity"))["total"] or 0
                )
                remaining_qty = max(0, plan.quantity - total_produced)

                if remaining_qty > 0:
                    current_rate = float(plan.daily_rate) * float(ppi)
                    if current_rate > 0:
                        days_left = int(float(remaining_qty) / current_rate)
                        forecast_finish_date = today + timedelta(days=days_left)

            predecessor_ids = [dep.predecessor_id for dep in plan.predecessors.all()]
            predecessor_names = [
                dep.predecessor.activity for dep in plan.predecessors.all()
            ]

            gantt_data.append(
                {
                    "id": plan.pk,
                    "activity": plan.activity,
                    "start_date": plan.start_date.isoformat(),
                    "finish_date": plan.finish_date.isoformat(),
                    "forecast_finish_date": forecast_finish_date.isoformat()
                    if forecast_finish_date
                    else None,
                    "duration": plan.duration,
                    "progress_pct": progress_pct,
                    "depth": depth,
                    "has_children": plan.children.exists(),
                    "is_leaf": plan.is_leaf,
                    "predecessors": predecessor_ids,
                    "predecessor_names": predecessor_names,
                    "parent_id": plan.parent_id,
                    "edit_url": reverse_lazy(
                        edit_url_name,
                        kwargs={"project_pk": project_pk, "pk": plan.pk},
                    ),
                }
            )

        context.update(
            {
                "company": project.contractor,
                "gantt_data_json": json.dumps(gantt_data, default=str),
                "summary": perf_data,
                "tab": "schedule_report",
            }
        )
        return context


class ProductionPlanListView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, ListView
):
    """Lists all production plans for a project with filtering."""

    model = ProductionPlan
    template_name = "production_progress/planning/list.html"
    context_object_name = "plans"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {"title": "Production Planning", "url": None},
        ]

    def get_queryset(self):
        return (
            ProductionPlan.objects.filter(
                project_id=self.kwargs["project_pk"], is_archived=False
            )
            .select_related("labour_activity", "parent")
            .prefetch_related(
                "children",
                "predecessors",
                "predecessors__predecessor",
                "resources",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        context["project"] = project

        # Separate root plans and build a map for children if needed
        # Although we can use plan.children.all() in template,
        # root_plans provides the starting point for the tree.
        plans = context["plans"]
        context["root_plans"] = [p for p in plans if p.parent_id is None]

        # Pass filters back to template
        context["activity_filter"] = self.request.GET.get("activity", "").strip()
        context["start_date_filter"] = self.request.GET.get("start_date", "").strip()
        context["finish_date_filter"] = self.request.GET.get("finish_date", "").strip()

        return context


class ProductionPlanCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, CreateView
):
    """Provides a schedule dashboard to plan daily production targets."""

    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = "production_progress/planning/form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project_id"] = self.kwargs["project_pk"]
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get("parent"):
            initial["parent"] = self.request.GET.get("parent")
        if self.request.GET.get("section"):
            initial["section"] = self.request.GET.get("section")
        if self.request.GET.get("bill_no"):
            initial["bill_no"] = self.request.GET.get("bill_no")
        if self.request.GET.get("labour_activity"):
            initial["labour_activity"] = self.request.GET.get("labour_activity")
        return initial

    def get_success_url(self):
        return reverse_lazy(
            "project:production-planning",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs.get("project_pk")
        context["project"] = get_object_or_404(Project, pk=project_pk)
        context["plans"] = ProductionPlan.objects.filter(
            project_id=project_pk, is_archived=False
        ).prefetch_related("resources")

        if self.request.POST:
            context["dependency_formset"] = PlanDependencyFormSet(
                self.request.POST,
                project_id=project_pk,
                parent_id=self.request.POST.get("parent") or None,
            )
        else:
            context["dependency_formset"] = PlanDependencyFormSet(project_id=project_pk)
        return context

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {
                "title": "Production Planning",
                "url": reverse_lazy(
                    "project:production-planning", kwargs={"project_pk": project_pk}
                ),
            },
            {"title": "New Plan", "url": None},
        ]

    def form_valid(self, form):
        project_pk = self.kwargs.get("project_pk")
        project = get_object_or_404(Project, pk=project_pk)
        form.instance.project = project
        context = self.get_context_data()
        dependency_formset = context["dependency_formset"]

        if dependency_formset.is_valid():
            try:
                response = super().form_valid(form)
                dependency_formset.instance = self.object
                dependency_formset.save()
                messages.success(self.request, "Production plan saved successfully.")
                return response
            except Exception as e:
                messages.error(self.request, f"Database error: {str(e)}")
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        dependency_formset = context.get("dependency_formset")

        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Error in {field}: {error}")

        if dependency_formset and not dependency_formset.is_valid():
            for error in dependency_formset.non_form_errors():
                messages.error(self.request, f"Dependency Error: {error}")
            for form_errors in dependency_formset.errors:
                for field, field_errors in form_errors.items():
                    messages.error(
                        self.request, f"Dependency {field}: {', '.join(field_errors)}"
                    )

        return super().form_invalid(form)


class ProductionPlanDetailView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """Shows a single production plan detail."""

    model = ProductionPlan
    template_name = "production_progress/planning/detail.html"
    context_object_name = "plan"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        return ProductionPlan.objects.filter(project_id=self.kwargs["project_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.get_object()
        project = plan.project
        context["project"] = project

        # Fetch children based on node type
        if plan.node_type == "SECTION":
            context["child_title"] = "Bills"
            context["children"] = plan.children.filter(
                deleted=False, node_type="BILL"
            ).order_by("bill_no")
        elif plan.node_type == "BILL":
            context["child_title"] = "Activities"
            context["children"] = plan.children.filter(
                deleted=False, node_type="ACTIVITY"
            ).order_by("start_date")
        else:
            context["child_title"] = None
            context["children"] = []

        # Resources logic (from previous version)
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

        # Provide granular plant allocations (direct or fallback)
        context["plant_allocations"] = plan.get_plant_allocations()

        # Fetch related BOQItems for the activity line items section
        if plan.labour_activity:
            items = plan.labour_activity.boq_items.all()
            if plan.section:
                items = items.filter(section=plan.section)
            if plan.bill_no:
                items = items.filter(bill_no=plan.bill_no)
            context["activity_line_items"] = items

        # Predecessors / Dependencies logic
        if self.request.POST:
            context["dependency_formset"] = PlanDependencyFormSet(
                self.request.POST,
                instance=plan,
                project_id=project.pk,
                plan_id=plan.pk,
            )
        else:
            context["dependency_formset"] = PlanDependencyFormSet(
                instance=plan,
                project_id=project.pk,
                plan_id=plan.pk,
            )

        return context

    def post(self, request, *args, **kwargs):
        """Handle predecessor/dependency updates from the detail page."""
        self.object = self.get_object()
        context = self.get_context_data()
        dependency_formset = context["dependency_formset"]

        if dependency_formset.is_valid():
            dependency_formset.save()

            # After saving, trigger date propagation
            self.object.update_successor_dates()

            messages.success(request, "Dependencies updated successfully.")
            return redirect(
                "project:production-plan-detail",
                project_pk=self.object.project.pk,
                pk=self.object.pk,
            )

        return self.render_to_response(context)

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        plan = self.get_object()
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {
                "title": "Production Planning",
                "url": reverse_lazy(
                    "project:production-planning", kwargs={"project_pk": project_pk}
                ),
            },
            {"title": f"Plan: {plan.activity}", "url": None},
        ]


class ProductionPlanAutofillView(SubscriptionRequiredMixin, LoginRequiredMixin, View):
    """
    Autofills the production schedule from the Project Estimator (BOQItems).
    Groups BOQItems by section, bill_no, and labour_specification.
    """

    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])

        # Fetch BOQItems that have a labour specification and are not headers
        boq_items = (
            BOQItem.objects.filter(
                project=project,
                labour_specification__isnull=False,
                is_section_header=False,
            )
            .values("section", "bill_no", "labour_specification")
            .annotate(total_quantity=Sum("contract_quantity"))
        )

        if not boq_items.exists():
            messages.warning(
                request, "No labour-based items found in the Project Estimator."
            )
            return redirect("project:production-planning", project_pk=project.pk)

        created_count = 0
        skipped_count = 0

        # Fetch Labour Specifications for this project to get daily rates
        labour_specs = ProjectLabourSpecification.objects.filter(project=project)
        spec_rate_map = {spec.id: (spec.daily_output or 0) for spec in labour_specs}

        for item in boq_items:
            # Check if plan already exists for this grouping
            existing = ProductionPlan.objects.filter(
                project=project,
                section=item["section"],
                bill_no=item["bill_no"],
                labour_activity_id=item["labour_specification"],
                is_archived=False,
            ).exists()

            if existing:
                skipped_count += 1
                continue

            # Fetch the first BOQItem to get the unit (or look it up from spec)
            sample_item = BOQItem.objects.filter(
                project=project,
                section=item["section"],
                bill_no=item["bill_no"],
                labour_specification_id=item["labour_specification"],
            ).first()

            unit = sample_item.unit if sample_item else ""
            daily_rate = spec_rate_map.get(item["labour_specification"], 0)

            # Get the labour specification name
            labour_spec_name = ""
            if item["labour_specification"]:
                labour_spec = ProjectLabourSpecification.objects.filter(
                    id=item["labour_specification"]
                ).first()
                if labour_spec:
                    labour_spec_name = labour_spec.name

            # Create the ProductionPlan
            # Note: Save() will trigger _ensure_hierarchy() to build the tree automatically
            ProductionPlan.objects.create(
                project=project,
                section=item["section"],
                bill_no=item["bill_no"],
                activity=labour_spec_name,
                labour_activity_id=item["labour_specification"],
                quantity=item["total_quantity"] or 0,
                unit=unit,
                daily_rate=daily_rate,
                start_date=None,
                finish_date=None,
            )
            created_count += 1

        if created_count > 0:
            messages.success(
                request,
                f"Successfully created {created_count} activities from the Estimator.",
            )
        if skipped_count > 0:
            messages.info(
                request,
                f"{skipped_count} activities already existed and were skipped.",
            )

        return redirect("project:production-planning", project_pk=project.pk)


class ProductionPlanUpdateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, UpdateView
):
    """Edit an existing production plan item."""

    model = ProductionPlan
    form_class = ProductionPlanForm
    template_name = "production_progress/planning/form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project_id"] = self.kwargs["project_pk"]
        return kwargs

    def get_queryset(self):
        return ProductionPlan.objects.filter(project_id=self.kwargs["project_pk"])

    def get_success_url(self):
        return reverse_lazy(
            "project:production-planning",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        context["plans"] = ProductionPlan.objects.filter(
            project_id=self.kwargs["project_pk"], is_archived=False
        ).prefetch_related("resources")
        context["is_update"] = True

        if self.request.POST:
            context["dependency_formset"] = PlanDependencyFormSet(
                self.request.POST,
                instance=self.object,
                project_id=self.kwargs["project_pk"],
                plan_id=self.object.pk,
                parent_id=self.request.POST.get("parent") or None,
            )
        else:
            context["dependency_formset"] = PlanDependencyFormSet(
                instance=self.object,
                project_id=self.kwargs["project_pk"],
                plan_id=self.object.pk,
                parent_id=self.object.parent_id if self.object.parent else None,
            )

        return context

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        plan = self.get_object()
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {
                "title": "Production Planning",
                "url": reverse_lazy(
                    "project:production-planning", kwargs={"project_pk": project_pk}
                ),
            },
            {"title": f"Edit Plan: {plan.activity}", "url": None},
        ]

    def form_valid(self, form):
        context = self.get_context_data()
        dependency_formset = context["dependency_formset"]

        if dependency_formset.is_valid():
            try:
                response = super().form_valid(form)
                dependency_formset.instance = self.object
                dependency_formset.save()
                messages.success(self.request, "Production plan updated successfully.")
                return response
            except Exception as e:
                messages.error(self.request, f"Database error: {str(e)}")
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        dependency_formset = context.get("dependency_formset")

        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Error in {field}: {error}")

        if dependency_formset and not dependency_formset.is_valid():
            for error in dependency_formset.non_form_errors():
                messages.error(self.request, f"Dependency Error: {error}")
            for form_errors in dependency_formset.errors:
                for field, field_errors in form_errors.items():
                    messages.error(
                        self.request, f"Dependency {field}: {', '.join(field_errors)}"
                    )

        return super().form_invalid(form)


class ProductionPlanDeleteView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DeleteView
):
    """Delete an existing production plan item."""

    model = ProductionPlan
    template_name = "production_progress/planning/delete.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        return ProductionPlan.objects.filter(project_id=self.kwargs["project_pk"])

    def get_success_url(self):
        return reverse_lazy(
            "project:production-planning",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(pk=self.kwargs["project_pk"])
        return context

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        plan = self.get_object()
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {
                "title": "Production Planning",
                "url": reverse_lazy(
                    "project:production-planning", kwargs={"project_pk": project_pk}
                ),
            },
            {"title": f"Delete Plan: {plan.activity}", "url": None},
        ]

    def _archive_recursive(self, plan):
        """Recursively archive all descendants before archiving the plan itself."""
        for child in plan.children.all():
            self._archive_recursive(child)
            child.is_archived = True
            child.save(update_fields=["is_archived"])

    def delete(self, request, *args, **kwargs):
        """Archive the plan and all its descendants gracefully."""
        self.object = self.get_object()
        try:
            # Archive all children recursively so the RESTRICT FK is never triggered
            self._archive_recursive(self.object)
            self.object.is_archived = True
            self.object.save(update_fields=["is_archived"])
            messages.success(
                request,
                f"Activity \u2018{self.object.activity}\u2019 and its "
                f"children have been archived successfully.",
            )
        except db_models.RestrictedError:
            messages.error(
                request,
                f"Cannot delete \u2018{self.object.activity}\u2019 because it is "
                f"still referenced by other records. "
                f"Please remove the dependencies first.",
            )
        return redirect(str(self.get_success_url()))


class ProductionCostBreakdownView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """List view showing all production plans with cost totals. Click a row to drill in."""

    template_name = "production_progress/cost_breakdown/list.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = Project.objects.get(pk=self.kwargs["project_pk"])
        context["project"] = project

        all_plans = (
            ProductionPlan.objects.filter(
                project=project, is_archived=False, labour_activity__isnull=False
            )
            .select_related("labour_activity", "parent")
            .prefetch_related("resources")
            .order_by("activity")
        )

        context["all_plans"] = all_plans

        # Aggregate project-level totals for the footer row
        total_labour = sum(p.total_labour_cost for p in all_plans)
        total_plant = sum(p.total_plant_cost for p in all_plans)
        total_other = sum(p.total_other_cost for p in all_plans)
        context["total_labour"] = total_labour
        context["total_plant"] = total_plant
        context["total_cost"] = total_labour + total_plant + total_other
        return context

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {"title": "Cost Breakdown", "url": None},
        ]


class ProductionCostBreakdownDetailView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """Detail view for a single plan's resource cost breakdown."""

    template_name = "production_progress/cost_breakdown/detail.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def _get_plan(self):
        """Retrieve the production plan for this project."""
        return get_object_or_404(
            ProductionPlan,
            pk=self.kwargs["plan_pk"],
            project_id=self.kwargs["project_pk"],
            is_archived=False,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        selected_plan = self._get_plan()

        context["project"] = project
        context["selected_plan"] = selected_plan
        context["resource_form"] = ProductionResourceForm(
            project_id=project.pk, initial={"production_plan": selected_plan}
        )

        # Fetch related BOQItems for the activity line items section
        if selected_plan.labour_activity:
            items = selected_plan.labour_activity.boq_items.all()
            if selected_plan.section:
                items = items.filter(section=selected_plan.section)
            if selected_plan.bill_no:
                items = items.filter(bill_no=selected_plan.bill_no)
            context["activity_line_items"] = items

        # Build BoQ Qty-driven plant rows (mirrors Plant Calculator logic).
        # One row per plant component; grand total = sum of (rate × boq_qty) per spec.
        boq_qs = BOQItem.objects.filter(
            project=project,
            is_section_header=False,
            plant_specification__isnull=False,
        )
        if selected_plan.section:
            boq_qs = boq_qs.filter(section=selected_plan.section)
        if selected_plan.bill_no:
            boq_qs = boq_qs.filter(bill_no=selected_plan.bill_no)
        if selected_plan.labour_activity:
            boq_qs = boq_qs.filter(labour_specification=selected_plan.labour_activity)

        # Group BOQItems by plant_specification, accumulating BoQ qty.
        spec_groups: OrderedDict = OrderedDict()
        for boq in boq_qs.select_related(
            "plant_specification"
        ).order_by("plant_specification__name"):
            spec = boq.plant_specification
            if spec.pk not in spec_groups:
                spec_groups[spec.pk] = {"spec": spec, "boq_qty": Decimal("0")}
            if boq.contract_quantity:
                spec_groups[spec.pk]["boq_qty"] += boq.contract_quantity

        # Expand each spec into one row per component (plant type).
        plant_spec_rows = []
        plant_spec_total = Decimal("0")
        for group in spec_groups.values():
            spec = group["spec"]
            boq_qty = group["boq_qty"]
            rate = getattr(spec, "rate_per_unit", None) or Decimal("0")
            spec_amount = rate * boq_qty
            plant_spec_total += spec_amount
            for comp in spec.components.all().select_related("plant_type"):
                if not comp.plant_type:
                    continue
                hours = comp.hours or Decimal("0")
                plant_spec_rows.append(
                    {
                        "plant_name": comp.plant_type.name,
                        "hours": hours,
                        "unit": spec.unit,
                        "rate": rate,
                        "boq_qty": boq_qty,
                        "plant_hours_boq": hours * boq_qty,
                        "source_spec": spec.name,
                    }
                )

        context["plant_spec_rows"] = plant_spec_rows
        context["plant_spec_total"] = plant_spec_total

        return context

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        plan = self._get_plan()
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {
                "title": "Cost Breakdown",
                "url": reverse_lazy(
                    "project:production-cost-breakdown",
                    kwargs={"project_pk": project_pk},
                ),
            },
            {"title": plan.activity, "url": None},
        ]

    def post(self, request, *args, **kwargs):
        project_pk = self.kwargs["project_pk"]
        plan_pk = self.kwargs["plan_pk"]
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

        return redirect(
            "project:production-cost-breakdown-detail",
            project_pk=project_pk,
            plan_pk=plan_pk,
        )


class ProductionResourceCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, CreateView
):
    """Form to add a production resource."""

    model = ProductionResource
    form_class = ProductionResourceForm
    template_name = "production_progress/resource/form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_success_url(self):
        plan_id = self.request.GET.get("plan_id")
        project_pk = self.kwargs["project_pk"]
        if plan_id:
            return reverse_lazy(
                "project:production-cost-breakdown-detail",
                kwargs={"project_pk": project_pk, "plan_pk": plan_id},
            )
        return reverse_lazy(
            "project:production-cost-breakdown",
            kwargs={"project_pk": project_pk},
        )

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

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {
                "title": "Cost Breakdown",
                "url": reverse_lazy(
                    "project:production-cost-breakdown",
                    kwargs={"project_pk": project_pk},
                ),
            },
            {"title": "Add Resource", "url": None},
        ]


class ProductionPlanAjaxDetailView(LoginRequiredMixin, TemplateView):
    """
    Returns the metadata (structure, bill, package) for a given plan as JSON.
    Used for auto-filling fields when a parent is selected.
    """

    def get(self, request, *args, **kwargs):
        plan = get_object_or_404(ProductionPlan, pk=self.kwargs["pk"])
        return JsonResponse(
            {
                "section": plan.section or "",
                "bill_no": plan.bill_no or "",
            }
        )


class GetProjectBillsAjaxView(LoginRequiredMixin, TemplateView):
    """Returns unique bill numbers for a given section/project."""

    def get(self, request, *args, **kwargs):
        project_id = self.kwargs.get("project_pk")
        section = request.GET.get("section")

        bills = (
            BOQItem.objects.filter(project_id=project_id, section=section)
            .values_list("bill_no", flat=True)
            .distinct()
            .order_by("bill_no")
        )

        return JsonResponse({"bills": list(bills)})


class GetProjectItemsAjaxView(LoginRequiredMixin, TemplateView):
    """Returns BOQItems for a given project, optionally filtered by section and bill."""

    def get(self, request, *args, **kwargs):
        project_id = self.kwargs.get("project_pk")
        section = request.GET.get("section")
        bill_no = request.GET.get("bill_no")

        items_query = BOQItem.objects.filter(project_id=project_id)

        if section:
            items_query = items_query.filter(section=section)
        if bill_no:
            items_query = items_query.filter(bill_no=bill_no)

        items = items_query.select_related("labour_specification").order_by(
            "section", "bill_no", "description"
        )

        data = [
            {
                "id": item.id,  # ty:ignore[unresolved-attribute]
                "label": f"[{item.section}][{item.bill_no}] {item.description}"
                if not (section and bill_no)
                else item.description,
                "description": item.description,
                "section": item.section,
                "bill_no": item.bill_no,
                "unit": item.unit,
                "quantity": str(item.contract_quantity or 0),
                "labour_spec": item.labour_specification.name
                if item.labour_specification
                else "",
            }
            for item in items
        ]

        return JsonResponse({"items": data})


class ProductionPlanRefreshAjaxView(LoginRequiredMixin, View):
    """Refreshes the plant_types cache for a specific production plan."""

    def post(self, request, *args, **kwargs):
        project_pk = self.kwargs.get("project_pk")
        plan_pk = self.kwargs.get("pk")
        plan = get_object_or_404(ProductionPlan, pk=plan_pk, project_id=project_pk)

        try:
            # Re-fetch specifications from BOQ
            plan.refresh_plant_types()
            plan.save()

            return JsonResponse(
                {
                    "status": "success",
                    "message": f"Resources for '{plan.activity}' refreshed successfully.",
                    "plant_types": plan.plant_types,
                }
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


class ProductionCashflowForecastView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """Renders a dedicated Cashflow Forecast Dashboard with S-Curve and KPIs."""

    template_name = "production_progress/reports/cashflow_forecast.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs.get("project_pk")

        project = get_object_or_404(Project, pk=project_pk)
        context["project"] = project

        horizon = self.request.GET.get("horizon", "month").lower()
        if horizon not in ["month", "term", "half", "year"]:
            horizon = "month"

        try:
            history = int(self.request.GET.get("history", 3))
        except (ValueError, TypeError):
            history = 3

        from ..utils.production_utils import get_project_cashflow_data

        cashflow_data = get_project_cashflow_data(
            project_pk, horizon_type=horizon, history_months=history
        )

        context["cashflow_data"] = cashflow_data
        context["cashflow_json"] = json.dumps(cashflow_data, default=str)
        context["current_horizon"] = horizon
        context["current_history"] = history

        return context

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {
                "title": "Production Planning",
                "url": reverse_lazy(
                    "project:production-planning", kwargs={"project_pk": project_pk}
                ),
            },
            {"title": "Cashflow Forecast", "url": None},
        ]
