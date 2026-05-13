from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from app.core.Utilities.models import BaseModel
from app.Project.models import Project

if TYPE_CHECKING:
    from django.db.models import Manager as RelatedManager


class DailyProduction(BaseModel):
    """Tracks notes for a project."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="daily_productions"
    )
    notes = models.TextField(blank=True, help_text="Optional remarks/notes")

    class Meta:
        verbose_name = "Daily Production"
        verbose_name_plural = "Daily Productions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project.name} - Note ({self.pk})"


class ProductionPlan(BaseModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="production_plans"
    )
    activity = models.CharField(max_length=255, blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        related_name="children",
        help_text="Parent activity for nesting",
    )
    NODE_TYPES = [
        ("SECTION", "Section Header"),
        ("BILL", "Bill Header"),
        ("ACTIVITY", "Work Activity"),
    ]
    node_type = models.CharField(max_length=20, choices=NODE_TYPES, default="ACTIVITY")
    is_leaf = models.BooleanField(
        default=True,
        help_text="True if this is a work activity, False for structural headers.",
    )
    section = models.CharField(
        max_length=200,
        blank=True,
        help_text="Manual section or inherited from Activity",
    )
    bill_no = models.CharField(
        max_length=200,
        blank=True,
        help_text="Manual bill no or inherited from Activity",
    )
    labour_activity = models.ForeignKey(
        "estimator.ProjectLabourSpecification",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="production_plans",
        help_text="The Labor Specification this plan belongs to",
    )
    plant_specification = models.ForeignKey(
        "estimator.ProjectPlantSpecification",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="production_plans",
        help_text="Optional Plant Specification for this plan",
    )
    plant_types = models.JSONField(
        default=list, blank=True, help_text="Cached list of plant types from BOQ"
    )
    start_date = models.DateField(null=True, blank=True)
    finish_date = models.DateField(null=True, blank=True)
    quantity = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(0)]
    )
    unit = models.CharField(max_length=50)
    daily_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Daily production rate"
    )
    crew_count = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1,
        blank=True,
        help_text="Number of crews/resources assigned (multiplier)",
    )
    duration = models.IntegerField(default=0, help_text="Duration in days")
    is_archived = models.BooleanField(default=False)

    if TYPE_CHECKING:
        resources: QuerySet["ProductionResource"]

    class Meta:
        verbose_name = "Production Plan"
        verbose_name_plural = "Production Plans"
        ordering = ["start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "section", "bill_no", "activity", "start_date"],
                name="unique_plan_activity_date",
            )
        ]

    def __str__(self):
        return f"{self.project.name} - {self.activity}"

    @property
    def unit_display(self):
        """Returns the shorthand unit if available, otherwise just the unit."""
        if not self.unit:
            return ""
        # Handle "Name (shorthand)" format
        if "(" in self.unit and ")" in self.unit:
            return self.unit.split("(")[-1].split(")")[0]
        return self.unit

    def save(self, *args, **kwargs):
        if self.is_leaf:
            if self.start_date:
                if self.finish_date and (
                    not self.duration
                    or (
                        kwargs.get("update_fields") is None
                        and (self.finish_date - self.start_date).days != self.duration
                    )
                    or "finish_date" in kwargs.get("update_fields", [])
                ):
                    # Dates are the driver if finish_date is provided and either duration is missing,
                    # or we're doing a full save and they're inconsistent, or finish_date was explicitly updated.
                    self.duration = (self.finish_date - self.start_date).days
                elif self.duration:
                    # Duration is the driver
                    self.finish_date = self.start_date + timedelta(days=self.duration)

        # 2. Track changes for propagation
        is_new = self.pk is None
        old_start = None
        old_finish = None
        if not is_new:
            try:
                old_instance = ProductionPlan.objects.get(pk=self.pk)
                old_start = old_instance.start_date
                old_finish = old_instance.finish_date
            except ProductionPlan.DoesNotExist:
                pass

        # 3. Handle automatic hierarchy generation for ANY leaf item (Spec linked)
        is_leaf_item = (
            self.labour_activity or self.plant_specification
        ) and self.is_leaf

        if self.is_leaf:
            self.refresh_plant_types()

        if is_leaf_item and not self.parent and (self.section or self.bill_no):
            self._ensure_hierarchy()

        # 4. Standard Save
        super().save(*args, **kwargs)

        # 5. Trigger Successor Propagation and Parent Sync
        deleted_changed = not is_new and self.deleted and not old_instance.deleted
        if (
            is_new
            or self.start_date != old_start
            or self.finish_date != old_finish
            or deleted_changed
        ):
            # We delay successors slightly to ensure this instance is fully committed
            # though in a single request, update_successor_dates is fine.
            self.update_successor_dates()

            if self.parent:
                self.parent.sync_parent_metrics()

    def refresh_plant_types(self):
        """Updates plant_types field from BoQ allocations for list view display."""
        # Use the BoQ-driven rows which match the logic in activity_views.py
        rows = self.get_boq_driven_plant_rows()
        names = sorted({row["plant_name"] for row in rows})
        self.plant_types = names

    def sync_parent_metrics(self):
        """
        Recalculates this node's metrics based on its children.
        Includes dates, quantity (child count), and unit.
        Then, bubbles the update up to its own parent.
        """
        if self.is_leaf or self.deleted:
            return  # Activities and deleted nodes don't aggregate.

        # 1. Aggregate children
        children_qs = self.children.filter(deleted=False)
        stats = children_qs.aggregate(
            min_start=models.Min("start_date"),
            max_finish=models.Max("finish_date"),
            child_count=models.Count("id"),
        )

        # 2. Handle empty parents
        if not children_qs.exists():
            # If no children remain, this header is no longer needed
            self.soft_delete()
            return

        # 3. Calculate and Update self if changed (bypass save() to avoid recursion)
        start = stats["min_start"]
        finish = stats["max_finish"]
        qty = Decimal(str(stats["child_count"]))
        unit = "Items"
        duration = 0
        if start and finish:
            duration = (finish - start).days

        # Check if anything changed to avoid redundant updates
        if (
            self.start_date != start
            or self.finish_date != finish
            or self.quantity != qty
            or self.unit != unit
            or self.duration != duration
        ):
            ProductionPlan.objects.filter(pk=self.pk).update(
                start_date=start,
                finish_date=finish,
                quantity=qty,
                unit=unit,
                duration=duration,
            )
            # Sync local instance for the current session
            self.start_date = start
            self.finish_date = finish
            self.quantity = qty
            self.unit = unit
            self.duration = duration

            # 4. Trigger successor updates for the parent itself
            self.update_successor_dates()

            # 5. Bubble up to grandparent
            if self.parent:
                self.parent.sync_parent_metrics()

    def get_predecessor_end_date(self):
        """Returns the latest finish_date of all predecessors."""
        predecessors = [
            p.predecessor for p in self.predecessors.all() if p.predecessor.finish_date
        ]
        if not predecessors:
            return None
        return max(p.finish_date for p in predecessors)

    def update_successor_dates(self):
        """Recursively updates start/finish dates for all successors based on dependencies."""
        for dependency in self.successors.all():
            successor = dependency.successor
            latest_pred_end = successor.get_predecessor_end_date()

            if latest_pred_end and successor.start_date != latest_pred_end:
                # Update start date to match latest predecessor end date (Finish-to-Start)
                successor.start_date = latest_pred_end
                if successor.duration:
                    successor.finish_date = successor.start_date + timedelta(
                        days=successor.duration
                    )

                # Use update() to bypass full save signals but keep recursion
                ProductionPlan.objects.filter(pk=successor.pk).update(
                    start_date=successor.start_date, finish_date=successor.finish_date
                )

                # Recurse to update this successor's own successors
                successor.update_successor_dates()

    def _ensure_hierarchy(self):
        """Automatically creates Section and Bill levels if they don't exist."""
        if not self.section or not self.is_leaf:
            return

        # 1. Ensure Section Level exists
        section_parent = (
            ProductionPlan.objects.filter(
                project=self.project,
                section=self.section,
                node_type="SECTION",
                deleted=False,
            )
            .order_by("created_at")
            .first()
        )

        if not section_parent:
            section_parent = ProductionPlan.objects.create(
                project=self.project,
                section=self.section,
                bill_no="",
                node_type="SECTION",
                is_leaf=False,
                activity=self.section,
                start_date=self.start_date or timezone.now().date(),
                finish_date=self.finish_date or timezone.now().date(),
                quantity=1,
                unit="SUM",
            )

        if not self.bill_no:
            if self != section_parent:
                self.parent = section_parent
            return

        # 2. Ensure Bill Level exists under Section
        bill_parent = (
            ProductionPlan.objects.filter(
                project=self.project,
                section=self.section,
                bill_no=self.bill_no,
                node_type="BILL",
                deleted=False,
            )
            .order_by("created_at")
            .first()
        )

        if not bill_parent:
            bill_parent = ProductionPlan.objects.create(
                project=self.project,
                section=self.section,
                bill_no=self.bill_no,
                node_type="BILL",
                is_leaf=False,
                activity=f"Bill {self.bill_no}",
                parent=section_parent,
                start_date=self.start_date or timezone.now().date(),
                finish_date=self.finish_date or timezone.now().date(),
                quantity=1,
                unit="SUM",
            )

        if self != bill_parent and self != section_parent:
            self.parent = bill_parent

    def soft_delete(self):
        """Override soft_delete to prevent deleting if children exist."""
        from django.core.exceptions import ValidationError

        if self.children.filter(deleted=False).exists():  # ty:ignore[unresolved-attribute]
            raise ValidationError(
                "Cannot delete an activity that has children. Please delete them first."
            )
        super().soft_delete()

    @property
    def hourly_labour_rate(self) -> Decimal:
        """Calculates total crew hourly rate based on (Count * Rate) for each skill."""
        if not self.labour_activity or not self.labour_activity.crew:
            return Decimal("0")

        crew = self.labour_activity.crew
        # Formula: (Count * Rate) summed across all 3 levels
        total_daily = (
            Decimal(str(crew.skilled)) * crew.skilled_rate
            + Decimal(str(crew.semi_skilled)) * crew.semi_skilled_rate
            + Decimal(str(crew.general)) * crew.general_rate
        )
        # Convert daily crew cost to hourly (assuming 8h day)
        return total_daily / Decimal("8.0")

    @property
    def hourly_plant_rate(self) -> Decimal:
        """Sums hourly_rate for each physical plant assigned to this activity via BOQItems."""
        from app.Estimator.models import BOQItem

        # Get all BOQ items contributing to this activity
        items = BOQItem.objects.filter(
            project=self.project,
            section=self.section,
            bill_no=self.bill_no,
            labour_specification=self.labour_activity,
            plant_specification__isnull=False,
        ).prefetch_related("plant_specification__components__plant_type")

        # Sum hourly rate for each item (physical plant unit)
        total_hourly = Decimal("0")
        for item in items:
            if item.plant_specification:
                # Sum all components of this spec
                for comp in item.plant_specification.components.all():
                    if comp.plant_type:
                        total_hourly += comp.plant_type.hourly_rate

        return total_hourly

    @property
    def daily_labour_cost(self) -> Decimal:
        return self.hourly_labour_rate * Decimal("8.0")

    @property
    def daily_plant_cost(self) -> Decimal:
        return self.hourly_plant_rate * Decimal("8.0") * (self.crew_count or 1)

    @property
    def is_active(self):
        """A plan is active between start and finish dates and if not archived."""
        if self.is_archived:
            return False
        today = timezone.now().date()
        if not self.start_date or not self.finish_date:
            return False
        return self.start_date <= today <= self.finish_date

    @property
    def total_labour_cost(self):
        # For structural nodes (SECTION/BILL), aggregate from leaf children.
        if not self.is_leaf:
            return sum(
                child.total_labour_cost for child in self.children.filter(deleted=False)
            )

        # Manual resources cost
        manual_cost = (
            self.resources.filter(resource_type="LABOUR").aggregate(
                total=models.Sum("total_cost")
            )["total"]
            or 0
        )

        # Crew-based specification cost
        spec_cost = 0
        if self.labour_activity and self.labour_activity.crew:
            # Use crew_count * daily_cost (excluding duration)
            spec_cost = self.labour_activity.crew.crew_daily_cost * (
                self.crew_count or 1
            )

        return manual_cost + spec_cost

    def get_plant_allocations(self):
        """Returns a list of granular plant allocations for this plan based on duration."""
        allocations = []
        unique_specs = {}

        if self.plant_specification:
            unique_specs[self.plant_specification.name] = self.plant_specification
        else:
            # Fallback: Pull from related BOQItems
            from app.Estimator.models import BOQItem, ProjectPlantSpecification

            spec_ids = list(
                BOQItem.objects.filter(
                    project=self.project,
                    section=self.section,
                    bill_no=self.bill_no,
                    labour_specification=self.labour_activity,
                    plant_specification__isnull=False,
                )
                .values_list("plant_specification", flat=True)
                .distinct()
            )

            if spec_ids:
                specs = ProjectPlantSpecification.objects.filter(
                    pk__in=spec_ids
                ).prefetch_related("components__plant_type")
                for spec in specs:
                    # Get all type names from components
                    type_names = [
                        c.plant_type.name for c in spec.components.all() if c.plant_type
                    ]
                    name = (
                        ", ".join(sorted(set(type_names))) if type_names else spec.name
                    )
                    if name not in unique_specs:
                        unique_specs[name] = spec

        # Expand unique specs into components
        duration = Decimal(str(self.duration or 0))
        for display_name, spec in unique_specs.items():
            for comp in spec.components.all():
                if not comp.plant_type:
                    continue

                hours_per_day = comp.hours
                total_hours = hours_per_day * duration
                rate = comp.plant_type.hourly_rate or Decimal("0")
                total_cost = total_hours * rate

                allocations.append(
                    {
                        "id": comp.plant_type_id,
                        "name": comp.plant_type.name,
                        "hours_per_day": hours_per_day,
                        "total_hours": total_hours,
                        "rate": rate,
                        "total_cost": total_cost,
                        "source_name": spec.name,
                        "display_name": display_name,
                        "is_fallback": not self.plant_specification,
                    }
                )

        return allocations

    @staticmethod
    def calculate_boq_driven_plant_rows(
        project, section, bill_no, activity, labour_activity_id=None
    ):
        """
        Calculates granular plant rows driven by BOQItem specifications.
        Returns a list of dictionaries with plant info and costs.
        """
        from decimal import Decimal

        from django.db import models as db_models

        from app.Estimator.models import BOQItem

        # Normalize strings for matching
        s_key = str(section or "").strip()
        b_key = str(bill_no or "").strip()
        a_key = str(activity or "").strip()

        # Filter BOQItems for the project
        boq_qs = BOQItem.objects.filter(
            project=project,
            is_section_header=False,
            plant_specification__isnull=False,
        )

        # Apply flexible matching including spec names and description
        # Use icontains to handle trailing spaces or minor variations
        boq_qs = boq_qs.filter(
            db_models.Q(labour_specification_id=labour_activity_id)
            | db_models.Q(description__icontains=a_key)
            | db_models.Q(labour_specification__name__icontains=a_key)
            | db_models.Q(plant_specification__name__icontains=a_key)
        )

        # Apply section/bill filters with normalization
        if s_key:
            boq_qs = boq_qs.filter(section__icontains=s_key)
        if b_key:
            boq_qs = boq_qs.filter(bill_no__icontains=b_key)

        from collections import OrderedDict

        spec_groups = OrderedDict()
        for boq in boq_qs.select_related("plant_specification").order_by(
            "plant_specification__name"
        ):
            spec = boq.plant_specification
            if not spec:
                continue
            if spec.pk not in spec_groups:
                spec_groups[spec.pk] = {"spec": spec, "boq_qty": Decimal("0")}
            if boq.contract_quantity:
                spec_groups[spec.pk]["boq_qty"] += boq.contract_quantity

        rows = []
        for group in spec_groups.values():
            spec = group["spec"]
            boq_qty = group["boq_qty"]
            for comp in spec.components.all().select_related("plant_type"):
                if not comp.plant_type:
                    continue
                hours = comp.hours or Decimal("0")
                rate = comp.plant_type.hourly_rate or Decimal("0")
                rows.append(
                    {
                        "id": comp.plant_type_id,
                        "plant_name": comp.plant_type.name,
                        "hours": hours,
                        "unit": spec.unit,
                        "rate": rate,
                        "boq_qty": boq_qty,
                        "plant_hours_boq": hours * boq_qty,
                        "total_cost": hours * boq_qty * rate,
                        "source_spec": spec.name,
                    }
                )
        return rows

    def get_boq_driven_plant_rows(self):
        """Instance method wrapper for calculate_boq_driven_plant_rows."""
        return self.calculate_boq_driven_plant_rows(
            self.project,
            self.section,
            self.bill_no,
            self.activity,
            self.labour_activity_id,
        )

    @property
    def total_plant_cost(self):
        # For structural nodes (SECTION/BILL), aggregate from leaf children.
        if not self.is_leaf:
            return sum(
                child.total_plant_cost for child in self.children.filter(deleted=False)
            )

        # Manual resources cost (legacy/fallback)
        manual_cost = (
            self.resources.filter(resource_type="PLANT").aggregate(
                total=models.Sum("total_cost")
            )["total"]
            or 0
        )

        # Specification-based plant cost (Standard)
        allocs = self.get_plant_allocations()
        spec_cost = sum(a["total_cost"] for a in allocs)

        return manual_cost + spec_cost

    @property
    def total_other_cost(self):
        return (
            self.resources.filter(resource_type="RESOURCE").aggregate(
                total=models.Sum("total_cost")
            )["total"]
            or 0
        )

    @property
    def progress_percentage(self):
        """Calculates total progress percentage based on actual entries vs quantity."""
        actual_produced = (
            self.daily_entries.aggregate(total=models.Sum("quantity"))["total"] or 0
        )
        if self.quantity > 0:
            return min(100, round((actual_produced / self.quantity) * 100, 1))
        return 0


class PlanDependency(BaseModel):
    """Tracks finish-to-start dependencies between production plans."""

    predecessor = models.ForeignKey(
        ProductionPlan, on_delete=models.CASCADE, related_name="successors"
    )
    successor = models.ForeignKey(
        ProductionPlan, on_delete=models.CASCADE, related_name="predecessors"
    )

    class Meta:
        verbose_name = "Plan Dependency"
        verbose_name_plural = "Plan Dependencies"
        unique_together = ["predecessor", "successor"]

    def __str__(self):
        return f"{self.predecessor.activity} -> {self.successor.activity}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.predecessor_id == self.successor_id:  # ty:ignore[unresolved-attribute]
            raise ValidationError("An activity cannot depend on itself.")

        # Check circular dependency using ancestor graph
        def is_ancestor(node, target_id, visited=None):
            if visited is None:
                visited = set()
            if node.id in visited:
                return False
            visited.add(node.id)
            if node.id == target_id:
                return True
            for pred_rel in node.predecessors.all():
                if is_ancestor(pred_rel.predecessor, target_id, visited):
                    return True
            return False

        if self.predecessor_id and self.successor_id:  # ty:ignore[unresolved-attribute]
            if is_ancestor(self.predecessor, self.successor.id):
                raise ValidationError("This dependency creates a circular reference.")


class ProductionResource(BaseModel):
    RESOURCE_TYPES = [
        ("LABOUR", "Labour"),
        ("PLANT", "Plant/Equipment"),
        # ('RESOURCE', 'Other Resource'),
    ]

    production_plan = models.ForeignKey(
        ProductionPlan, on_delete=models.CASCADE, related_name="resources"
    )
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    skill_type = models.ForeignKey(
        "SiteManagement.SkillType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="production_resources",
    )
    plant_type = models.ForeignKey(
        "SiteManagement.PlantType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="production_resources",
    )
    name = models.CharField(max_length=255, help_text="e.g., Skilled, Bobcat, Diesel")
    number = models.DecimalField(
        max_digits=10, decimal_places=2, default=1, validators=[MinValueValidator(0)]
    )
    days = models.DecimalField(
        max_digits=10, decimal_places=2, default=1, validators=[MinValueValidator(0)]
    )
    rate = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(0)]
    )
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    class Meta:
        verbose_name = "Production Resource"
        verbose_name_plural = "Production Resources"

    def __str__(self):
        return f"{self.resource_type} - {self.name} ({self.production_plan.activity})"

    def save(self, *args, **kwargs):
        if self.skill_type:
            self.name = self.skill_type.name
            self.rate = self.skill_type.hourly_rate
        elif self.plant_type:
            self.name = self.plant_type.name
            self.rate = self.plant_type.hourly_rate

        self.total_cost = (self.number or 0) * (self.rate or 0) * (self.days or 1)
        super().save(*args, **kwargs)


class DailyActivityEntry(BaseModel):
    """Specific activity performed during a daily report."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="daily_entries"
    )
    production_plan = models.ForeignKey(
        ProductionPlan, on_delete=models.CASCADE, related_name="daily_entries"
    )
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, help_text="Optional activity-specific remarks")
    quantity = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    hours_on_activity = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Total hours spent on this activity",
    )

    if TYPE_CHECKING:
        labour_usage: "RelatedManager[DailyLabourUsage]"
        plant_usage: "RelatedManager[DailyPlantUsage]"
        resource: "RelatedManager[DailyPlantUsage]"

    class Meta:
        verbose_name = "Daily Activity Entry"
        verbose_name_plural = "Daily Activity Entries"

    def __str__(self):
        return f"{self.production_plan.activity} on {self.date}"

    @property
    def day_number(self):
        """Calculates D1, D2 etc relative to the plan start date."""
        if self.date and self.production_plan.start_date:
            delta = (self.date - self.production_plan.start_date).days
            return f"D{delta + 1}"
        return "D?"

    @property
    def total_labour_cost(self):
        """Calculated labour cost based on crew spec rates and tracked hours."""
        return self.production_plan.hourly_labour_rate * Decimal(
            str(self.hours_on_activity)
        )

    @property
    def total_plant_cost(self):
        """Sum of actual plant usage costs from recorded resources."""
        return sum(usage.total_cost for usage in self.plant_usage.all())

    @property
    def man_hours(self):
        """Calculated man hours based on crew size and tracked activity duration."""
        crew_size = Decimal("0")
        if (
            self.production_plan.labour_activity
            and self.production_plan.labour_activity.crew
        ):
            crew_size = Decimal(
                str(self.production_plan.labour_activity.crew.crew_size)
            )
        return crew_size * Decimal(str(self.hours_on_activity))

    @property
    def total_cost(self):
        return self.total_labour_cost + self.total_plant_cost

    @property
    def work_productivity(self):
        mh = self.man_hours
        if mh > 0:
            return self.quantity / mh
        return 0

    @property
    def cost_per_item(self):
        if self.quantity > 0:
            return self.total_cost / self.quantity
        return 0


class DailyLabourUsage(BaseModel):
    """Tracks labour usage for a specific activity entry."""

    entry = models.ForeignKey(
        DailyActivityEntry, on_delete=models.CASCADE, related_name="labour_usage"
    )
    resource = models.ForeignKey(
        ProductionResource,
        on_delete=models.CASCADE,
        limit_choices_to={"resource_type": "LABOUR"},
    )
    number = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    hours = models.DecimalField(
        max_digits=5, decimal_places=2, default=8, validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = "Daily Labour Usage"
        verbose_name_plural = "Daily Labour Usages"

    @property
    def total_cost(self):
        return (self.number or 0) * (self.hours or 0) * (self.resource.rate or 0)

    @property
    def man_hours(self):
        return (self.number or 0) * (self.hours or 0)


class DailyPlantUsage(BaseModel):
    """Tracks plant usage for a specific activity entry."""

    entry = models.ForeignKey(
        DailyActivityEntry, on_delete=models.CASCADE, related_name="plant_usage"
    )
    plant_type = models.ForeignKey(
        "estimator.ProjectPlantCost",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usages",
        help_text="The master plant cost record from the specification.",
    )
    resource = models.ForeignKey(
        ProductionResource,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to={"resource_type": "PLANT"},
        help_text="Legacy: The specific plant resource allocated to the plan.",
    )
    number = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    hours = models.DecimalField(
        max_digits=5, decimal_places=2, default=8, validators=[MinValueValidator(0)]
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Production quantity achieved by this specific plant resource.",
    )

    class Meta:
        verbose_name = "Daily Plant Usage"
        verbose_name_plural = "Daily Plant Usages"

    @property
    def total_cost(self):
        rate = Decimal("0")
        if self.plant_type:
            rate = self.plant_type.hourly_rate
        elif self.resource:
            rate = self.resource.rate
        return (self.number or 0) * (self.hours or 0) * (rate or 0)
