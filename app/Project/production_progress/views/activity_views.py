import math
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (
    Case,
    DecimalField,
    F,
    Max,
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

from ..utils.production_utils import (
    get_project_activity_summary,
)


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
        self.f_section = self.request.GET.get("section", "")
        self.f_bill = self.request.GET.get("bill_no", "")
        self.f_activity = self.request.GET.get("activity", "")

        # Use the centralized activity summary utility
        return get_project_activity_summary(
            project_id=self.kwargs["project_pk"],
            f_section=self.f_section,
            f_bill=self.f_bill,
            f_activity=self.f_activity,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        context["project"] = project
        context["project_pk"] = project_pk

        # Add filters to context for the template

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
        # Fetch plant mapping data for tooltips
        # We must use logic consistent with get_project_activity_summary's subqueries
        from app.Estimator.models import ProjectPlantSpecificationComponent

        # Map plant types in bulk using normalized keys to ensure matches
        plant_mapping_data = (
            ProjectPlantSpecificationComponent.objects.filter(
                specification__boq_items__project_id=project_pk
            )
            .values(
                "plant_type__name",
                "specification__boq_items__section",
                "specification__boq_items__bill_no",
                "specification__boq_items__labour_specification__name",
                "specification__boq_items__plant_specification__name",
            )
            .distinct()
        )

        plant_map = {}
        for p in plant_mapping_data:
            # Normalize keys to empty strings to avoid None vs "" mismatches
            section = str(p["specification__boq_items__section"] or "").strip()
            bill = str(p["specification__boq_items__bill_no"] or "").strip()
            plant_name = p["plant_type__name"]
            l_name = p["specification__boq_items__labour_specification__name"]
            p_name = p["specification__boq_items__plant_specification__name"]

            # Map to the same keys used for grouping (Section, Bill, Name)
            # We map to both names because act_name could be either
            for name in [l_name, p_name]:
                if name:
                    key = (section, bill, name.strip())
                    if key not in plant_map:
                        plant_map[key] = set()
                    plant_map[key].add(plant_name)

        for activity in activities:
            spec_id = activity.get("labour_spec_id")
            spec = spec_map.get(spec_id) if spec_id else None

            # Multiply daily production by crew count
            crew_count = activity.get("crew_count") or Decimal("1")
            activity["daily_production"] = (
                spec.daily_production if spec else 0
            ) * crew_count

            # Add crew info for display
            if spec and spec.crew:
                activity["labour_specification__crew__crew_type"] = spec.crew.crew_type
            else:
                activity["labour_specification__crew__crew_type"] = "No Crew"

            # Normalize lookup key to match the mapping logic above
            s_key = str(activity["section"] or "").strip()
            b_key = str(activity["bill_no"] or "").strip()
            n_key = str(activity["act_name"] or "").strip()

            key = (s_key, b_key, n_key)
            types = sorted(plant_map.get(key, []))
            if crew_count > 1:
                activity["plant_types"] = (
                    ", ".join([f"{int(crew_count)}x {t}" for t in types])
                    if types
                    else "None"
                )
            else:
                activity["plant_types"] = ", ".join(types) if types else "None"

            # Calculate Duration: Total Tracker / Daily Production (rounded up)
            total_tracker = activity.get("total_tracker", 0)
            daily_prod = activity.get("daily_production", 0)
            if daily_prod and daily_prod > 0:
                activity["duration"] = math.ceil(total_tracker / daily_prod)
            else:
                activity["duration"] = 0

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
                    # Rule: If item has labour, use it
                    When(
                        unit=act_unit,
                        labour_specification__isnull=False,
                        then=F("contract_quantity"),
                    ),
                    # Rule: If item has NO labour but has plant, use it
                    When(
                        unit=act_unit,
                        labour_specification__isnull=True,
                        plant_specification__isnull=False,
                        then=F("contract_quantity"),
                    ),
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

        # Multiplier for the number of crews
        crew_count = group_items.aggregate(count=Max("crew_count"))["count"] or Decimal(
            "1"
        )
        context["crew_count"] = crew_count

        # Calculate daily costs for the "Budgeted Daily Cost" card
        # Multiply daily labour cost by crew count
        base_labour_cost = (
            labour_spec.crew.crew_daily_cost if labour_spec and labour_spec.crew else 0
        )
        context["daily_labour_cost"] = base_labour_cost * crew_count

        # Daily production multiplied by crew count
        base_production = labour_spec.daily_production if labour_spec else 0
        daily_production = base_production * crew_count
        context["daily_production"] = daily_production

        # Calculate Duration: Total Tracker / Daily Production (rounded up)
        total_tracker = context.get("total_tracker", 0)
        if daily_production and daily_production > 0:
            context["duration"] = math.ceil(total_tracker / daily_production)
        else:
            context["duration"] = 0

        # Build BoQ Qty-driven plant spec rows using centralized logic
        from app.Project.production_progress.production_models import ProductionPlan

        plant_spec_rows = ProductionPlan.calculate_boq_driven_plant_rows(
            project, self.section, self.bill_no, self.act_name
        )
        plant_spec_total = sum(row["total_cost"] for row in plant_spec_rows)

        context["plant_spec_rows"] = plant_spec_rows
        context["plant_spec_total"] = plant_spec_total

        # Set plant types for tooltip (including multiplier)
        plant_names = sorted({row["plant_name"] for row in plant_spec_rows})
        if crew_count > 1:
            context["plant_types"] = ", ".join(
                [f"{int(crew_count)}x {n}" for n in plant_names]
            )
        else:
            context["plant_types"] = ", ".join(plant_names)

        # Daily plant cost for KPI card (sum of unique component hourly rates in this group)
        from app.Estimator.models import ProjectPlantSpecificationComponent

        plant_components = (
            ProjectPlantSpecificationComponent.objects.filter(
                specification__boq_items__in=group_items
            )
            .distinct()
            .aggregate(total_rate=Sum("plant_type__hourly_rate"))
        )

        daily_plant_rate = plant_components["total_rate"] or Decimal("0")
        context["daily_plant_cost"] = daily_plant_rate * Decimal("8.0") * crew_count

        # Add detailed crew composition for display
        if labour_spec and labour_spec.crew:
            context["crew_type"] = labour_spec.crew.crew_type
            context["crew_skilled"] = labour_spec.crew.skilled * crew_count
            context["crew_semi_skilled"] = labour_spec.crew.semi_skilled * crew_count
            context["crew_general"] = labour_spec.crew.general * crew_count
        else:
            context["crew_type"] = "No Crew"
            context["crew_skilled"] = 0
            context["crew_semi_skilled"] = 0
            context["crew_general"] = 0

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
    Uses the centralized activity summary utility for consistency.
    """

    def get(self, request, *args, **kwargs):
        project_id = self.kwargs.get("project_pk")

        # Use centralized utility
        activities = get_project_activity_summary(project_id)

        # Bulk fetch plant details for mapping
        all_plants = (
            BOQItem.objects.filter(
                project_id=project_id, plant_specification__isnull=False
            )
            .annotate(
                act_name=Coalesce(
                    "labour_specification__name", "plant_specification__name"
                ),
            )
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
        for item in activities:
            key = (item["section"], item["bill_no"], item["act_name"])
            label = f"[{item['section']}][{item['bill_no']}] {item['act_name']}"

            # Calculate daily output using factors if it's a labour item
            daily_output = item["daily_production_base"] or 0

            data.append(
                {
                    "id": item["labour_spec_id"],
                    "label": label,
                    "activity_name": item["act_name"],
                    "section": item["section"],
                    "bill_no": item["bill_no"],
                    "unit": item["act_unit"],
                    "quantity": str(item["total_tracker"] or 0),
                    "daily_production": str(item["daily_production_base"] or 0),
                    "daily_output": str(daily_output),
                    "crew_count": str(item["crew_count"]),
                    "daily_plant_cost": str(item["daily_plant_cost"]),
                    "plant_specs": plant_spec_map.get(key, []),
                    "plant_types": [
                        f"{int(item['crew_count'])}x {t}"
                        for t in sorted(plant_type_map.get(key, []))
                    ]
                    if item["crew_count"] > 1
                    else sorted(plant_type_map.get(key, [])),
                }
            )

        return JsonResponse({"activities": data})


class UpdateActivityCrewCountAjaxView(LoginRequiredMixin, TemplateView):
    """
    Updates the crew_count for all BOQItems in an activity group.
    """

    def post(self, request, *args, **kwargs):
        project_id = self.kwargs.get("project_pk")
        act_name = request.POST.get("act_name")
        section = request.POST.get("section")
        bill_no = request.POST.get("bill_no")
        crew_count = request.POST.get("crew_count")

        if not all([act_name, section, bill_no, crew_count]):
            return JsonResponse(
                {"status": "error", "message": "Missing parameters"}, status=400
            )

        try:
            crew_count = Decimal(crew_count)
        except Exception:
            return JsonResponse(
                {"status": "error", "message": "Invalid crew count"}, status=400
            )

        # Update all items in the group
        items = (
            BOQItem.objects.filter(
                project_id=project_id,
                section=section,
                bill_no=bill_no,
            )
            .annotate(
                act_name_annotated=Coalesce(
                    "labour_specification__name", "plant_specification__name"
                )
            )
            .filter(act_name_annotated=act_name)
        )

        updated_count = items.update(crew_count=crew_count)

        return JsonResponse(
            {
                "status": "success",
                "updated_count": updated_count,
                "crew_count": str(crew_count),
            }
        )
