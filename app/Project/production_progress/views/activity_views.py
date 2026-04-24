from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (
    Case,
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Estimator.models import (
    BOQItem,
    ProjectLabourSpecification,
)
from app.Project.models import Project


class LaborActivityListView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, ListView
):
    """
    Groups BOQItems by Labour Specification, Section, and Bill No to form 'Activities'.
    Provides aggregated metrics for each activity group.
    """

    model = BOQItem
    template_name = "production_progress/activities/list.html"
    context_object_name = "activities"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        project_pk = self.kwargs["project_pk"]
        self.f_section = self.request.GET.get("section", "")
        self.f_bill = self.request.GET.get("bill_no", "")
        self.f_activity = self.request.GET.get("activity", "")

        queryset = BOQItem.objects.filter(
            Q(labour_specification__isnull=False)
            | Q(plant_specification__isnull=False),
            project_id=project_pk,
        ).annotate(
            act_name=Coalesce(
                "labour_specification__name", "plant_specification__name"
            ),
            act_unit=Coalesce(
                "labour_specification__unit", "plant_specification__unit"
            ),
        )

        if self.f_section:
            queryset = queryset.filter(section=self.f_section)
        if self.f_bill:
            queryset = queryset.filter(bill_no=self.f_bill)
        if self.f_activity:
            queryset = queryset.filter(act_name__icontains=self.f_activity)

        return (
            queryset.values(
                "section",
                "bill_no",
                "act_name",
                "act_unit",
                "labour_specification",  # Still useful for crew lookup if present
                "labour_specification__crew__crew_type",
            )
            .annotate(
                num_items=Count("id"),
                plant_count=Count(
                    "plant_specification__components__plant_type", distinct=True
                ),
                total_tracker=Sum(
                    Case(
                        When(
                            unit=F("act_unit"),
                            then=F("contract_quantity"),
                        ),
                        default=Value(0),
                        output_field=DecimalField(),
                    )
                ),
                total_amount=Sum(
                    F("contract_quantity") * F("contract_rate"),
                    output_field=DecimalField(),
                ),
                # Confirmed Formula: (skilled * rate + semi * rate + general * rate)
                daily_labour_cost=ExpressionWrapper(
                    Coalesce(F("labour_specification__crew__skilled"), 0)
                    * Coalesce(F("labour_specification__crew__skilled_rate"), 0)
                    + Coalesce(F("labour_specification__crew__semi_skilled"), 0)
                    * Coalesce(F("labour_specification__crew__semi_skilled_rate"), 0)
                    + Coalesce(F("labour_specification__crew__general"), 0)
                    * Coalesce(F("labour_specification__crew__general_rate"), 0),
                    output_field=DecimalField(),
                ),
                # Confirmed Formula: Sum(plant_rate) for all units in group (no longer * 8.0)
                daily_plant_cost=Sum(
                    Coalesce(
                        F("plant_specification__components__plant_type__hourly_rate"), 0
                    ),
                    output_field=DecimalField(),
                ),
            )
            .annotate(total_daily_cost=F("daily_labour_cost") + F("daily_plant_cost"))
            .order_by("section", "bill_no", "act_name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        context["project"] = project
        context["project_pk"] = project_pk

        # Add filters to context for the template
        context["f_section"] = self.f_section
        context["f_bill"] = self.f_bill
        context["f_activity"] = self.f_activity

        # Get unique values for filter dropdowns
        all_items = BOQItem.objects.filter(
            Q(labour_specification__isnull=False)
            | Q(plant_specification__isnull=False),
            project_id=project_pk,
        ).annotate(
            act_name=Coalesce("labour_specification__name", "plant_specification__name")
        )

        context["sections"] = (
            all_items.order_by("section").values_list("section", flat=True).distinct()
        )
        context["bills"] = (
            all_items.order_by("bill_no").values_list("bill_no", flat=True).distinct()
        )

        # Add rate information to activities
        activities = context["activities"]
        labour_specs = ProjectLabourSpecification.objects.filter(project_id=project_pk)
        spec_map = {spec.id: spec for spec in labour_specs}

        # Map plant types in bulk to avoid N+1 queries
        plant_mapping_data = (
            all_items.filter(plant_specification__components__plant_type__isnull=False)
            .values(
                "section",
                "bill_no",
                "act_name",
                "plant_specification__components__plant_type__name",
            )
            .distinct()
        )

        plant_map = {}
        for row in plant_mapping_data:
            key = (row["section"], row["bill_no"], row["act_name"])
            if key not in plant_map:
                plant_map[key] = []
            plant_map[key].append(
                row["plant_specification__components__plant_type__name"]
            )

        for activity in activities:
            spec_id = activity.get("labour_specification")
            spec = spec_map.get(spec_id) if spec_id else None
            activity["daily_production"] = spec.daily_production if spec else 0

            # Set aggregated plant types from map
            key = (activity["section"], activity["bill_no"], activity["act_name"])
            types = sorted(plant_map.get(key, []))
            activity["plant_types"] = ", ".join(types) if types else "None"

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
            {"title": "Labor Activities", "url": "#"},
        ]


class LaborActivityDetailView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, ListView
):
    """
    Detailed breakdown of a specific activity group.
    Filters BOQItems by the specific Act Name, Section, and Bill No.
    """

    model = BOQItem
    template_name = "production_progress/activities/detail.html"
    context_object_name = "items"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_queryset(self):
        self.project_pk = self.kwargs["project_pk"]
        self.act_name = self.request.GET.get("act_name", "")
        self.section = self.request.GET.get("section", "")
        self.bill_no = self.request.GET.get("bill_no", "")

        return (
            BOQItem.objects.filter(
                project_id=self.project_pk,
                section=self.section,
                bill_no=self.bill_no,
            )
            .annotate(
                act_name_annotated=Coalesce(
                    "labour_specification__name", "plant_specification__name"
                )
            )
            .filter(act_name_annotated=self.act_name)
            .prefetch_related("plant_specification__components__plant_type")
            .order_by("id")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, pk=self.project_pk)

        group_items = self.get_queryset()
        # Find the representative spec (Labour first, then Plant)
        first_item = group_items.first()
        labour_spec = first_item.labour_specification if first_item else None
        plant_spec = first_item.plant_specification if first_item else None

        act_unit = (
            labour_spec.unit
            if labour_spec
            else (plant_spec.unit if plant_spec else "-")
        )

        context["project"] = project
        context["project_pk"] = self.project_pk
        context["labour_spec"] = labour_spec  # Still useful for crew details
        context["act_name"] = self.act_name
        context["act_unit"] = act_unit
        context["section"] = self.section
        context["bill_no"] = self.bill_no

        # Calculate total tracker and total amount for this specific view
        metrics = group_items.aggregate(
            total_tracker=Sum(
                Case(
                    When(unit=act_unit, then=F("contract_quantity")),
                    default=Value(0),
                    output_field=DecimalField(),
                )
            ),
            total_amount=Sum(
                F("contract_quantity") * F("contract_rate"), output_field=DecimalField()
            ),
        )
        context["total_tracker"] = metrics["total_tracker"] or 0
        context["total_amount"] = metrics["total_amount"] or 0

        # Unique plant types summary
        plant_types = sorted(
            group_items.exclude(plant_specification__components__plant_type__name=None)
            .values_list("plant_specification__components__plant_type__name", flat=True)
            .distinct()
        )
        context["plant_types_summary"] = (
            ", ".join(plant_types) if plant_types else "None"
        )

        # Calculate daily costs for the "Budgeted Daily Cost" card
        context["daily_labour_cost"] = (
            labour_spec.crew.crew_daily_cost if labour_spec and labour_spec.crew else 0
        )

        # Plant cost (Sum of hourly rates, no longer * 8.0)
        plant_metrics = group_items.aggregate(
            plant_cost=Sum(
                Coalesce(
                    F("plant_specification__components__plant_type__hourly_rate"), 0
                ),
                output_field=DecimalField(),
            )
        )
        context["daily_plant_cost"] = plant_metrics["plant_cost"] or 0
        context["total_daily_cost"] = (
            context["daily_labour_cost"] + context["daily_plant_cost"]
        )

        return context

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Labor Activities",
                "url": reverse_lazy(
                    "project:labor-activity-list", kwargs={"project_pk": project_pk}
                ),
            },
            {"title": "Activity Details", "url": "#"},
        ]


class GetProjectLaborActivitiesAjaxView(LoginRequiredMixin, TemplateView):
    """
    Returns unique Production Activities (Labour & Plant) for a given project.
    Groups BOQItems by (ActivityName, Section, BillNo).
    """

    def get(self, request, *args, **kwargs):
        project_id = self.kwargs.get("project_pk")

        queryset = BOQItem.objects.filter(
            Q(labour_specification__isnull=False)
            | Q(plant_specification__isnull=False),
            project_id=project_id,
        ).annotate(
            act_name=Coalesce(
                "labour_specification__name", "plant_specification__name"
            ),
            act_unit=Coalesce(
                "labour_specification__unit", "plant_specification__unit"
            ),
            act_daily_prod=Coalesce(
                "labour_specification__daily_production",
                "plant_specification__daily_production",
                0.0,
            ),
        )

        items = (
            queryset.values(
                "act_name",
                "act_unit",
                "act_daily_prod",
                "labour_specification",
                "labour_specification__team_mix",
                "labour_specification__site_factor",
                "labour_specification__tools_factor",
                "labour_specification__leadership_factor",
                "section",
                "bill_no",
            )
            .annotate(
                total_quantity=Sum(
                    Case(
                        When(
                            unit=F("act_unit"),
                            then=F("contract_quantity"),
                        ),
                        default=Value(0),
                        output_field=DecimalField(),
                    )
                ),
            )
            .order_by("section", "bill_no", "act_name")
        )

        # Map plant types in bulk
        all_plants = (
            queryset.filter(plant_specification__isnull=False)
            .values(
                "section",
                "bill_no",
                "act_name",
                "plant_specification",
                "plant_specification__name",
                "plant_specification__components__plant_type__name",
            )
            .distinct()
        )

        plant_spec_map = {}
        plant_type_map = {}
        for p in all_plants:
            key = (p["section"], p["bill_no"], p["act_name"])
            if key not in plant_spec_map:
                plant_spec_map[key] = []
                plant_type_map[key] = set()

            plant_spec_map[key].append(
                {
                    "id": p["plant_specification"],
                    "name": p["plant_specification__name"],
                    "type": p["plant_specification__components__plant_type__name"],
                }
            )
            plant_type_map[key].add(
                p["plant_specification__components__plant_type__name"]
            )

        data = []
        for item in items:
            key = (item["section"], item["bill_no"], item["act_name"])
            label = f"[{item['section']}][{item['bill_no']}] {item['act_name']}"

            data.append(
                {
                    "id": item["labour_specification"],  # Can be None
                    "label": label,
                    "activity_name": item["act_name"],
                    "section": item["section"],
                    "bill_no": item["bill_no"],
                    "unit": item["act_unit"],
                    "quantity": str(item["total_quantity"] or 0),
                    "daily_production": str(item["act_daily_prod"] or 0),
                    "daily_output": str(
                        (item["act_daily_prod"] or 0)
                        * (item["labour_specification__team_mix"] or 1)
                        * (item["labour_specification__site_factor"] or 1)
                        * (item["labour_specification__tools_factor"] or 1)
                        * (item["labour_specification__leadership_factor"] or 1)
                    ),
                    "plant_specs": plant_spec_map.get(key, []),
                    "plant_types": sorted(plant_type_map.get(key, [])),
                }
            )

        return JsonResponse({"activities": data})
