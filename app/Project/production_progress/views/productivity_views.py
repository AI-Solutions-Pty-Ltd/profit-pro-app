import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, DecimalField, ExpressionWrapper, F, OuterRef, Subquery, Sum, Value
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
    UpdateView,
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
    DailyActivityReport,
    DailyLabourUsage,
    DailyPlantUsage,
    DailyProduction,
    ProductionPlan,
)
from ..serializers import DailyLogReportSerializer


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
        from app.Estimator.models import BOQItem

        # Subquery for summing plant rates across BOQItems linked to this plan/activity
        plant_rates = (
            BOQItem.objects.filter(
                project_id=OuterRef("production_plan__project_id"),
                section=OuterRef("production_plan__section"),
                bill_no=OuterRef("production_plan__bill_no"),
                labour_specification_id=OuterRef("production_plan__labour_activity_id"),
                plant_specification__isnull=False,
            )
            .values("labour_specification_id")
            .annotate(total_rate=Sum("plant_specification__plant_type__hourly_rate"))
            .values("total_rate")
        )

        return (
            DailyActivityEntry.objects.filter(
                report__project_id=self.kwargs["project_pk"]
            )
            .select_related(
                "report",
                "production_plan",
                "production_plan__labour_activity",
                "production_plan__labour_activity__crew",
            )
            .annotate(
                # Formula: (skilled * rate + semi * rate + general * rate) / 8.0
                hourly_labour_rate=ExpressionWrapper(
                    (
                        F("production_plan__labour_activity__crew__skilled")
                        * F("production_plan__labour_activity__crew__skilled_rate")
                        + F("production_plan__labour_activity__crew__semi_skilled")
                        * F("production_plan__labour_activity__crew__semi_skilled_rate")
                        + F("production_plan__labour_activity__crew__general")
                        * F("production_plan__labour_activity__crew__general_rate")
                    )
                    / Value(8.0),
                    output_field=DecimalField(),
                ),
                hourly_plant_rate=Coalesce(
                    Subquery(plant_rates, output_field=DecimalField()),
                    Value(0),
                    output_field=DecimalField(),
                ),
            )
            .annotate(
                acc_labour_cost=ExpressionWrapper(
                    F("hours_on_activity") * F("hourly_labour_rate"),
                    output_field=DecimalField(),
                ),
                acc_plant_cost=ExpressionWrapper(
                    F("hours_on_activity") * F("hourly_plant_rate"),
                    output_field=DecimalField(),
                ),
            )
            .annotate(
                acc_total_cost=F("acc_labour_cost") + F("acc_plant_cost"),
            )
            .order_by("-report__date", "-created_at")
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
            labour=Sum("acc_labour_cost"),
            plant=Sum("acc_plant_cost"),
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
            serializer = DailyLogReportSerializer(data=data)
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

    model = DailyActivityReport
    template_name = "production_progress/log/form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]
    context_object_name = "report"

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
        # We prefetch for efficiency
        report = self.object
        entries_data = []
        for entry in report.entries.all().select_related("production_plan"):
            # Labour
            labour_details = {
                "Skilled": {"number": 0, "hours": 0},
                "Semi-Skilled": {"number": 0, "hours": 0},
                "General": {"number": 0, "hours": 0},
            }
            for usage in entry.labour_usage.all().select_related("resource"):
                labour_details[usage.resource.name] = {
                    "number": float(usage.number),
                    "hours": float(usage.hours),
                }

            # Plant
            plant_usage = []
            for usage in entry.plant_usage.all().select_related("resource"):
                plant_usage.append(
                    {
                        "plant_name": usage.resource.name,
                        "number": float(usage.number),
                        "hours": float(usage.hours),
                        "quantity": float(usage.quantity),
                    }
                )

            entries_data.append(
                {
                    "production_plan_id": entry.production_plan_id,
                    "activity": entry.production_plan.activity or (entry.production_plan.labour_activity.name if entry.production_plan.labour_activity else f"Activity {entry.production_plan.id}"),
                    "section": entry.production_plan.section or "No Section",
                    "bill_no": entry.production_plan.bill_no or "No Bill",
                    "quantity": float(entry.quantity),
                    "hours_on_activity": float(entry.hours_on_activity),
                    "labour_details": labour_details,
                    "plant_usage": plant_usage,
                    "unit": entry.production_plan.unit_display,
                    "available_plants": list(entry.production_plan.plant_types),
                }
            )

        context["initial_data"] = json.dumps(
            {
                "date": report.date.isoformat(),
                "notes": report.notes,
                "entries": entries_data,
            }
        )

        return context

    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            instance = self.get_object()
            data = json.loads(request.body)
            data["project_id"] = self.kwargs["project_pk"]
            serializer = DailyLogReportSerializer(instance, data=data)
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

    model = DailyActivityReport
    template_name = "production_progress/log/confirm_delete.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]
    context_object_name = "report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        context["project"] = get_object_or_404(Project, pk=project_pk)
        
        # Calculate Project Totals for the current list
        queryset = self.get_queryset()
        context["totals"] = queryset.aggregate(
            hours=Coalesce(Sum("hours_on_activity"), 0, output_field=DecimalField()),
            labour=Coalesce(Sum("acc_labour_cost"), 0, output_field=DecimalField()),
            plant=Coalesce(Sum("acc_plant_cost"), 0, output_field=DecimalField()),
            total=Coalesce(Sum("acc_total_cost"), 0, output_field=DecimalField()),
            qty=Coalesce(Sum("quantity"), 0, output_field=DecimalField()),
        )
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


class ProductionDailyLogDetailView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, DetailView
):
    """Detailed view of a Daily Activity Report."""

    model = DailyActivityReport
    template_name = "production_progress/log/details.html"
    context_object_name = "report"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        # Prefetch entries and resource usage
        entries = self.object.entries.select_related(
            "production_plan"
        ).prefetch_related("labour_usage__resource", "plant_usage__resource")
        context["entries"] = entries
        
        # Calculate daily totals
        context["report_total_labour_cost"] = sum(entry.total_labour_cost for entry in entries)
        context["report_total_plant_cost"] = sum(entry.total_plant_cost for entry in entries)
        context["report_total_cost"] = context["report_total_labour_cost"] + context["report_total_plant_cost"]
        context["report_total_hours"] = sum(entry.hours_on_activity for entry in entries)
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

        # Plant types are now cached on the ProductionPlan model
        plant_types = plan.plant_types

        # Crew Info
        crew_info = {"skilled": 0, "semi_skilled": 0, "general": 0}
        if plan.labour_activity and plan.labour_activity.crew:
            crew = plan.labour_activity.crew
            crew_info = {
                "skilled": crew.skilled,
                "semi_skilled": crew.semi_skilled,
                "general": crew.general,
            }

        return JsonResponse(
            {
                "activity": plan.activity or str(plan),
                "section": plan.section or "No Section",
                "bill_no": plan.bill_no or "No Bill",
                "unit": plan.unit_display,
                "plant_types": list(plant_types),
                "crew": crew_info,
            }
        )
