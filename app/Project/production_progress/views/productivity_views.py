import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    OuterRef,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
)

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project

from ..production_forms import (
    DailyProductionForm,
)
from ..production_models import (
    DailyActivityEntry,
    DailyProduction,
    ProductionPlan,
)
from ..serializers import DailyLogBatchSerializer, DailyLogEntrySerializer


class DailyProductionCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, CreateView
):
    """Form to log daily quantities."""

    model = DailyProduction
    form_class = DailyProductionForm
    template_name = "production_progress/tracking/production_form.html"
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
            {"title": "Log Daily Quantities", "url": None},
        ]

    def get_success_url(self):
        return reverse_lazy(
            "project:production-dashboard",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        context["project"] = project
        return context

    def form_valid(self, form):
        form.instance.project_id = self.kwargs["project_pk"]
        return super().form_valid(form)


class ProductionDailyLogListView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, ListView
):
    """List view for Daily Activity Reports."""

    model = DailyActivityEntry
    template_name = "production_progress/log/list.html"
    context_object_name = "entries"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        from decimal import Decimal

        from app.Project.production_progress.production_models import (
            DailyPlantUsage,
        )

        # Subquery for plant cost sum
        plant_costs = (
            DailyPlantUsage.objects.filter(entry=OuterRef("pk"))
            .annotate(
                actual_rate=Coalesce(
                    F("plant_type__hourly_rate"),
                    F("resource__rate"),
                    Decimal("0"),
                    output_field=models.DecimalField(),
                )
            )
            .annotate(
                cost=ExpressionWrapper(
                    F("number") * F("hours") * F("actual_rate"),
                    output_field=models.DecimalField(),
                )
            )
            .values("entry")
            .annotate(total=Sum("cost"))
            .values("total")
        )

        # Annotate with actual summed costs from usage records
        return (
            DailyActivityEntry.objects.filter(project_id=self.kwargs["project_pk"])
            .select_related(
                "production_plan",
                "production_plan__labour_activity",
                "production_plan__labour_activity__crew",
            )
            .annotate(
                # Formula: (skilled * rate + semi * rate + general * rate) / 8.0
                hourly_labour_rate=ExpressionWrapper(
                    (
                        Coalesce(
                            F("production_plan__labour_activity__crew__skilled"),
                            Value(0),
                        )
                        * Coalesce(
                            F("production_plan__labour_activity__crew__skilled_rate"),
                            Value(0),
                        )
                        + Coalesce(
                            F("production_plan__labour_activity__crew__semi_skilled"),
                            Value(0),
                        )
                        * Coalesce(
                            F(
                                "production_plan__labour_activity__crew__semi_skilled_rate"
                            ),
                            Value(0),
                        )
                        + Coalesce(
                            F("production_plan__labour_activity__crew__general"),
                            Value(0),
                        )
                        * Coalesce(
                            F("production_plan__labour_activity__crew__general_rate"),
                            Value(0),
                        )
                    )
                    / Value(
                        8.0, output_field=DecimalField(max_digits=10, decimal_places=2)
                    ),
                    output_field=models.DecimalField(max_digits=10, decimal_places=2),
                ),
                actual_labour_cost=Coalesce(
                    F("hours_on_activity") * F("hourly_labour_rate"),
                    Value(0, output_field=models.DecimalField()),
                ),
                actual_plant_cost=Coalesce(
                    Subquery(plant_costs), Value(0, output_field=models.DecimalField())
                ),
            )
            .annotate(acc_total_cost=F("actual_labour_cost") + F("actual_plant_cost"))
            .order_by("-date", "-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        context["project"] = project

        # Calculate Aggregate Totals for the footer
        qs = self.get_queryset()
        context["totals"] = qs.aggregate(
            qty=Sum("quantity"),
            hours=Sum("hours_on_activity"),
            labour=Sum("actual_labour_cost"),
            plant=Sum("actual_plant_cost"),
            total=Sum("acc_total_cost"),
        )
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
            {"title": "Daily Logs", "url": None},
        ]


class ProductionDailyLogCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """Multi-activity Daily Log Form."""

    template_name = "production_progress/log/form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        context["project"] = project

        # Available activities (only those with ProductionPlans)
        context["plans"] = ProductionPlan.objects.filter(
            project=project, labour_activity__isnull=False
        ).order_by("section", "bill_no", "activity")

        return context

    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            data = json.loads(request.body)
            data["project_id"] = self.kwargs["project_pk"]
            serializer = DailyLogBatchSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(
                    {"status": "success", "message": "Log saved successfully"}
                )
            return JsonResponse(
                {"status": "error", "errors": serializer.errors}, status=400
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Daily Logs",
                "url": reverse_lazy(
                    "project:production-daily-log-list",
                    kwargs={"project_pk": project_pk},
                ),
            },
            {"title": "Capture Log", "url": None},
        ]


class ProductionDailyLogUpdateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """Multi-activity Daily Log Edit Form."""

    model = DailyActivityEntry
    template_name = "production_progress/log/form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]
    context_object_name = "entry"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        context["project"] = project

        # Available activities (only those with ProductionPlans)
        context["plans"] = ProductionPlan.objects.filter(
            project=project, labour_activity__isnull=False
        ).order_by("section", "bill_no", "activity")

        # Prepare initial data for JS
        entry = self.object
        # For the "Edit" view, we fetch the specific entry
        # and pre-fill the form with it.
        # Since it's now a flat list, we edit entries individually
        # unless we implement a batch edit (which we can do by date).

        labour_details = {
            "Skilled": {"number": 0.0, "hours": 0.0},
            "Semi-Skilled": {"number": 0.0, "hours": 0.0},
            "General": {"number": 0.0, "hours": 0.0},
        }
        for usage in entry.labour_usage.all().select_related("resource"):
            labour_details[usage.resource.name] = {
                "number": float(usage.number),
                "hours": float(usage.hours),
            }

        plant_usage = []
        for usage in entry.plant_usage.all().select_related("plant_type", "resource"):
            plant_name = "Unknown"
            if usage.plant_type:
                plant_name = usage.plant_type.name
            elif usage.resource:
                plant_name = usage.resource.name

            plant_usage.append(
                {
                    "plant_type_id": usage.plant_type_id,
                    "resource_id": usage.resource_id,
                    "plant_name": plant_name,
                    "number": float(usage.number or 0),
                    "hours": float(usage.hours or 0),
                    "quantity": float(usage.quantity or 0),
                }
            )

        available_plants = [
            {
                "id": a["id"],
                "name": a["plant_name"],
                "hours_per_day": float(
                    a["hours"]
                ),  # Defaulting to BoQ hours/unit as a starting point
            }
            for a in entry.production_plan.get_boq_driven_plant_rows()
        ]

        # Fallback to project-wide plant types if no specific allocations found
        is_generic_plant = False
        if not available_plants:
            from app.Estimator.models import ProjectPlantCost

            is_generic_plant = True
            available_plants = [
                {
                    "id": p.id,
                    "name": p.name,
                    "hours_per_day": 8.0,
                }
                for p in ProjectPlantCost.objects.filter(project_id=project_pk)
            ]

        entry_data = {
            "id": entry.id,
            "production_plan_id": entry.production_plan_id,
            "date": entry.date.isoformat(),
            "notes": entry.notes,
            "quantity": float(entry.quantity),
            "hours_on_activity": float(entry.hours_on_activity),
            "labour_details": labour_details,
            "plant_usage": plant_usage,
            "unit": entry.production_plan.unit_display,
            "available_plants": available_plants,
            "is_generic_plant": is_generic_plant,
        }

        context["initial_data"] = json.dumps({"entries": [entry_data]})

        return context

    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            instance = self.get_object()
            data = json.loads(request.body)
            # For a single entry update, we can use the DailyLogEntrySerializer
            # but usually the frontend sends a batch format.
            # If it's a batch with one entry, we'll handle it.
            if "entries" in data and len(data["entries"]) > 0:
                entry_data = data["entries"][0]
                entry_data["project_id"] = self.kwargs["project_pk"]
                serializer = DailyLogEntrySerializer(instance, data=entry_data)
            else:
                data["project_id"] = self.kwargs["project_pk"]
                serializer = DailyLogEntrySerializer(instance, data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(
                    {"status": "success", "message": "Log updated successfully"}
                )
            return JsonResponse(
                {"status": "error", "errors": serializer.errors}, status=400
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Daily Logs",
                "url": reverse_lazy(
                    "project:production-daily-log-list",
                    kwargs={"project_pk": project_pk},
                ),
            },
            {"title": "Edit Log", "url": None},
        ]


class ProductionDailyLogDeleteView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DeleteView
):
    """Deletes a Daily Activity Report."""

    model = DailyActivityEntry
    template_name = "production_progress/log/confirm_delete.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]
    context_object_name = "entry"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        context["project"] = get_object_or_404(Project, pk=project_pk)
        return context

    def get_success_url(self):
        return reverse_lazy(
            "project:production-daily-log-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {"title": "Daily Logs", "url": self.get_success_url()},
            {"title": "Delete Log", "url": None},
        ]


class DailyActivityEntryUpdateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """Granular Activity Entry Edit Form."""

    model = DailyActivityEntry
    template_name = "production_progress/log/entry_form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]
    context_object_name = "entry"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        context["project"] = project

        entry = self.object
        # Labour
        labour_details = {
            "Skilled": {"number": 0.0, "hours": 0.0},
            "Semi-Skilled": {"number": 0.0, "hours": 0.0},
            "General": {"number": 0.0, "hours": 0.0},
        }
        for usage in entry.labour_usage.all().select_related("resource"):
            labour_details[usage.resource.name] = {
                "number": float(usage.number),
                "hours": float(usage.hours),
            }

        # Plant
        plant_usage = []
        for usage in entry.plant_usage.all().select_related("resource", "plant_type"):
            name = "Unknown"
            res_id = ""
            if usage.resource:
                name = usage.resource.name
                res_id = usage.resource_id
            elif usage.plant_type:
                name = usage.plant_type.name
                res_id = usage.plant_type_id

            plant_usage.append(
                {
                    "resource_id": res_id,
                    "plant_name": name,
                    "number": float(usage.number),
                    "hours": float(usage.hours),
                    "quantity": float(usage.quantity),
                }
            )

        # Get available plants for selection (ID and Name)
        available_plants = [
            {
                "id": a["id"],
                "name": a["plant_name"],
                "hours_per_day": float(
                    a["hours"]
                ),  # Defaulting to BoQ hours/unit as a starting point
            }
            for a in entry.production_plan.get_boq_driven_plant_rows()
        ]
        is_generic_plant = not bool(available_plants)
        if is_generic_plant:
            from app.Estimator.models import ProjectPlantCost

            available_plants = [
                {
                    "id": p.id,
                    "name": p.name,
                    "hours_per_day": 8.0,
                }
                for p in ProjectPlantCost.objects.filter(project_id=project_pk)
            ]

        context["initial_data"] = json.dumps(
            {
                "production_plan_id": entry.production_plan_id,
                "activity": entry.production_plan.activity
                or (
                    entry.production_plan.labour_activity.name
                    if entry.production_plan.labour_activity
                    else f"Activity {entry.production_plan.id}"
                ),
                "section": entry.production_plan.section or "No Section",
                "bill_no": entry.production_plan.bill_no or "No Bill",
                "quantity": float(entry.quantity),
                "hours_on_activity": float(entry.hours_on_activity),
                "labour_details": labour_details,
                "plant_usage": plant_usage,
                "unit": entry.production_plan.unit_display,
                "available_plants": available_plants,
                "is_generic_plant": is_generic_plant,
            }
        )
        return context

    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            instance = self.get_object()
            data = json.loads(request.body)
            serializer = DailyLogEntrySerializer(instance, data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Activity entry updated successfully",
                    }
                )
            return JsonResponse(
                {"status": "error", "errors": serializer.errors}, status=400
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Daily Logs",
                "url": reverse_lazy(
                    "project:production-daily-log-list",
                    kwargs={"project_pk": project_pk},
                ),
            },
            {"title": "Edit Activity Log", "url": None},
        ]


class ProductionDailyLogDetailView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """Detailed view of a Daily Activity Report."""

    model = DailyActivityEntry
    template_name = "production_progress/log/details.html"
    context_object_name = "entry"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entry = self.object
        context["project"] = entry.project

        # In the detail view, we show the specific entry details.
        # If we want to show other entries on the same day, we can fetch them:
        context["sibling_entries"] = (
            DailyActivityEntry.objects.filter(project=entry.project, date=entry.date)
            .exclude(id=entry.id)
            .select_related("production_plan")
        )

        return context

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Daily Logs",
                "url": reverse_lazy(
                    "project:production-daily-log-list",
                    kwargs={"project_pk": self.object.project_id},
                ),
            },
            {"title": "Log Details", "url": None},
        ]


class DailyLogActivityDataAjaxView(LoginRequiredMixin, TemplateView):
    """Returns metadata for a specific production plan to facilitate autofill."""

    def get(self, request, *args, **kwargs):
        plan_id = request.GET.get("plan_id")
        plan = get_object_or_404(ProductionPlan, pk=plan_id)

        # Crew Info
        crew_info = {"skilled": 0, "semi_skilled": 0, "general": 0}
        if plan.labour_activity and plan.labour_activity.crew:
            crew = plan.labour_activity.crew
            crew_info = {
                "skilled": crew.skilled,
                "semi_skilled": crew.semi_skilled,
                "general": crew.general,
            }

        # Get available plants for selection (from Spec)
        available_plants = [
            {
                "id": a["id"],
                "name": a["plant_name"],
                "hours_per_day": float(a["hours"]),
            }
            for a in plan.get_boq_driven_plant_rows()
        ]

        # Fallback to project-wide plant types if no specific allocations found
        is_generic_plant = False
        if not available_plants:
            from app.Estimator.models import ProjectPlantCost

            is_generic_plant = True
            available_plants = [
                {
                    "id": p.id,
                    "name": p.name,
                    "hours_per_day": 8.0,
                }
                for p in ProjectPlantCost.objects.filter(project_id=plan.project_id)
            ]

        return JsonResponse(
            {
                "activity": plan.activity or str(plan),
                "section": plan.section or "No Section",
                "bill_no": plan.bill_no or "No Bill",
                "unit": plan.unit_display,
                "available_plants": available_plants,
                "is_generic_plant": is_generic_plant,
                "crew": crew_info,
            }
        )
