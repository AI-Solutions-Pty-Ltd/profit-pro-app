from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models import Manager

from app.BillOfQuantities.models.structure_models import LineItem
from app.Estimator.calculations import (
    calculate_contract_amount,
    calculate_forecast_amount,
    calculate_materials_rate,
    calculate_progress_amount,
    calculate_rate_per_unit,
    calculate_total_quantity,
)

# ═══════════════════════════════════════════════════════════════════
# System-Level Library Models (admin-managed, importable)
# ═══════════════════════════════════════════════════════════════════


class SystemTradeCode(models.Model):
    prefix = models.CharField(max_length=20)
    trade_name = models.CharField(max_length=100)

    class Meta:
        db_table = "estimator_tradecode"
        ordering = ["prefix"]

    def __str__(self):
        return self.trade_code

    @property
    def trade_code(self):
        return f"{self.prefix}{self.trade_name}"


class SystemMaterial(models.Model):
    trade_name = models.CharField(max_length=200, blank=True)
    material_code = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=20, blank=True)
    market_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    material_variety = models.CharField(max_length=100, blank=True)
    market_spec = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "estimator_material"
        ordering = ["material_code"]

    def __str__(self):
        return self.material_code


class SystemSpecification(models.Model):
    section = models.CharField(max_length=100, blank=True)
    trade_code = models.ForeignKey(
        SystemTradeCode,
        on_delete=models.CASCADE,
        related_name="specifications",
        null=True,
        blank=True,
    )
    unit_label = models.CharField(max_length=20, default="m3")
    name = models.CharField(max_length=100)
    boq_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    system_spec = models.ForeignKey(
        "SystemMaterialSpec",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_specs",
    )

    class Meta:
        db_table = "estimator_specification"
        ordering = ["section", "name"]

    if TYPE_CHECKING:
        spec_components: "Manager[SystemSpecificationComponent]"

    def __str__(self):
        return self.name

    @property
    def components(self):
        comps = []
        for sc in self.spec_components.select_related("material").all():
            comps.append(
                {
                    "name": sc.label,
                    "qty_per_unit": sc.qty_per_unit,
                    "market_rate": sc.material.market_rate if sc.material else 0,
                    "unit": sc.material.unit if sc.material else "",
                }
            )
        return comps

    @property
    def rate_per_unit(self):
        if self.spec_components.exists():
            return calculate_rate_per_unit(self.components)
        elif self.system_spec:
            return self.system_spec.rate_per_unit
        return Decimal("0")

    @property
    def baseline_boq_quantity(self):
        return self.boq_quantity or Decimal("0")

    def component_totals(self):
        results = []
        for sc in self.spec_components.select_related("material").all():
            results.append(
                {
                    "id": sc.pk,
                    "label": sc.label,
                    "qty_per_unit": sc.qty_per_unit,
                    "total_quantity": calculate_total_quantity(
                        self.baseline_boq_quantity, sc.qty_per_unit
                    ),
                    "unit": sc.material.unit if sc.material else "",
                }
            )
        return results


class SystemSpecificationComponent(models.Model):
    specification = models.ForeignKey(
        SystemSpecification, on_delete=models.CASCADE, related_name="spec_components"
    )
    material = models.ForeignKey(
        SystemMaterial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spec_components",
    )
    label = models.CharField(max_length=100)
    qty_per_unit = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "estimator_specificationcomponent"
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.specification.name} - {self.label}"


class SystemLabourCrew(models.Model):
    crew_type = models.CharField(max_length=100, unique=True)
    crew_size = models.IntegerField(default=0)
    skilled = models.IntegerField(default=0)
    semi_skilled = models.IntegerField(default=0)
    general = models.IntegerField(default=0)
    daily_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    skilled_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    semi_skilled_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    general_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "estimator_labourcrew"
        ordering = ["crew_type"]
        verbose_name = "System Labour Crew"

    def __str__(self):
        return self.crew_type

    @property
    def crew_daily_cost(self):
        return (
            Decimal(str(self.skilled)) * self.skilled_rate
            + Decimal(str(self.semi_skilled)) * self.semi_skilled_rate
            + Decimal(str(self.general)) * self.general_rate
        )


class SystemLabourSpecification(models.Model):
    section = models.CharField(max_length=100, blank=True)
    trade_name = models.CharField(max_length=200, blank=True)
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    crew = models.ForeignKey(
        SystemLabourCrew,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="labour_specs",
    )
    daily_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    team_mix = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    site_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    tools_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    leadership_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    boq_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "estimator_labourspecification"
        ordering = ["section", "name"]
        verbose_name = "System Labour Specification"

    def __str__(self):
        return self.name

    @property
    def daily_output(self):
        return (
            self.daily_production
            * self.team_mix
            * self.site_factor
            * self.tools_factor
            * self.leadership_factor
        )

    @property
    def daily_cost(self):
        if self.crew:
            return self.crew.crew_daily_cost
        return Decimal("0")

    @property
    def rate_per_unit(self):
        if self.daily_production and self.daily_production > 0:
            return self.daily_cost / self.daily_production
        return Decimal("0")

    @property
    def total_cost(self):
        return self.baseline_boq_quantity * self.daily_cost

    @property
    def baseline_boq_quantity(self):
        return self.boq_quantity or Decimal("0")


class SystemPlantCost(models.Model):
    """System-level plant & equipment cost library."""

    name = models.CharField(max_length=200, unique=True)
    hourly_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["name"]
        verbose_name = "System Plant Cost"

    def __str__(self):
        return self.name


class SystemPlantSpecification(models.Model):
    """System-level plant specification library."""

    section = models.CharField(max_length=100, blank=True)
    trade_name = models.CharField(max_length=200, blank=True)
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    plant_type = models.ForeignKey(
        SystemPlantCost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plant_specs",
    )
    daily_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    operator_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    site_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)

    class Meta:
        ordering = ["section", "name"]
        verbose_name = "System Plant Specification"

    def __str__(self):
        return self.name

    @property
    def daily_output(self):
        return self.daily_production * self.operator_factor * self.site_factor

    @property
    def hourly_cost(self):
        if self.plant_type:
            return self.plant_type.hourly_rate
        return Decimal("0")

    @property
    def rate_per_unit(self):
        if self.daily_production and self.daily_production > 0:
            return self.hourly_cost / self.daily_production
        return Decimal("0")


class SystemPreliminaryCost(models.Model):
    """System-level preliminaries cost library — single table with type column."""

    PRELIMINARY_TYPE_CHOICES = [
        ("fixed_contractual", "Fixed Contractual Requirements"),
        ("fixed_facilities", "Fixed Facilities"),
        ("time_contractual", "Time-Contractual Requirements"),
        ("time_facilities", "Time-Facilities"),
        ("time_small_tools", "Time-Small Tool Allowances"),
        ("time_plant_equipment", "Time-Plant and Equipment"),
        ("time_company_overheads", "Time-Company & Head Office Overheads"),
        ("time_site_personnel", "Time-Site Personnel"),
    ]

    name = models.CharField(max_length=200)
    preliminary_type = models.CharField(max_length=30, choices=PRELIMINARY_TYPE_CHOICES)
    sum_value = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Sum/lump sum value"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    number_per_month = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True
    )
    monthly_rate = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, blank=True
    )
    months = models.DecimalField(max_digits=6, decimal_places=2, default=0, blank=True)

    class Meta:
        ordering = ["preliminary_type", "name"]
        verbose_name = "System Preliminary Cost"

    def __str__(self):
        return f"{self.get_preliminary_type_display()} - {self.name}"

    @property
    def is_time_based(self):
        return self.preliminary_type.startswith("time_")

    @property
    def computed_amount(self):
        if self.is_time_based:
            return self.number_per_month * self.monthly_rate * self.months
        return self.amount


class SystemPreliminarySpecification(models.Model):
    """System-level preliminary specification library."""

    section = models.CharField(max_length=100, blank=True)
    trade_name = models.CharField(max_length=200, blank=True)
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["section", "name"]
        verbose_name = "System Preliminary Specification"

    def __str__(self):
        return self.name


class SystemMaterialSpec(models.Model):
    """Reusable material specification library at system level."""

    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=20, default="m3")

    class Meta:
        verbose_name = "System Material Spec"
        verbose_name_plural = "System Material Specs"
        ordering = ["name"]

    if TYPE_CHECKING:
        system_spec_components: "Manager[SystemMaterialSpecComponent]"

    def __str__(self):
        return self.name

    @property
    def components(self):
        comps = []
        for sc in self.system_spec_components.select_related("material").all():
            comps.append(
                {
                    "name": sc.label,
                    "qty_per_unit": sc.qty_per_unit,
                    "market_rate": sc.material.market_rate if sc.material else 0,
                    "unit": sc.material.unit if sc.material else "",
                }
            )
        return comps

    @property
    def rate_per_unit(self):
        return calculate_rate_per_unit(self.components)


class SystemMaterialSpecComponent(models.Model):
    """Component of a system-level material specification."""

    spec = models.ForeignKey(
        SystemMaterialSpec,
        on_delete=models.CASCADE,
        related_name="system_spec_components",
    )
    material = models.ForeignKey(
        SystemMaterial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_spec_components",
    )
    label = models.CharField(max_length=100)
    qty_per_unit = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.spec.name} - {self.label}"


# ═══════════════════════════════════════════════════════════════════
# Project-Scoped Models (cloned from system library per project)
# ═══════════════════════════════════════════════════════════════════


class ProjectTradeCode(models.Model):
    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="estimator_trade_codes",
    )
    source = models.ForeignKey(
        SystemTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_copies",
    )
    prefix = models.CharField(max_length=20)
    trade_name = models.CharField(max_length=100)

    class Meta:
        ordering = ["prefix"]
        unique_together = [("project", "prefix")]

    if TYPE_CHECKING:
        boq_items: "Manager[BOQItem]"

    def __str__(self):
        return self.trade_code

    @property
    def trade_code(self):
        return f"{self.prefix}{self.trade_name}"


class ProjectMaterial(models.Model):
    project = models.ForeignKey(
        "Project.Project", on_delete=models.CASCADE, related_name="estimator_materials"
    )
    source = models.ForeignKey(
        SystemMaterial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_copies",
    )
    trade_name = models.CharField(max_length=200, blank=True)
    material_code = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, blank=True)
    market_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    material_variety = models.CharField(max_length=100, blank=True)
    market_spec = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["material_code"]
        unique_together = [("project", "material_code")]

    def __str__(self):
        return self.material_code


class ProjectSpecification(models.Model):
    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="estimator_specifications",
    )
    source = models.ForeignKey(
        SystemMaterialSpec,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_specification_copies",
    )
    section = models.CharField(max_length=100, blank=True)
    trade_code = models.ForeignKey(
        ProjectTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="specifications",
    )
    unit_label = models.CharField(max_length=20, default="m3")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["section", "name"]
        unique_together = [("project", "name")]

    if TYPE_CHECKING:
        spec_components: "Manager[ProjectSpecificationComponent]"
        boq_items: "Manager[BOQItem]"

    def __str__(self):
        return self.name

    @property
    def components(self):
        comps = []
        for sc in self.spec_components.select_related("material").all():
            comps.append(
                {
                    "name": sc.label,
                    "qty_per_unit": sc.qty_per_unit,
                    "market_rate": sc.material.market_rate if sc.material else 0,
                    "unit": sc.material.unit if sc.material else "",
                }
            )
        return comps

    @property
    def rate_per_unit(self):
        if self.spec_components.exists():
            return calculate_rate_per_unit(self.components)
        elif self.source:
            return self.source.rate_per_unit
        return Decimal("0")

    @property
    def baseline_boq_quantity(self):
        total = self.boq_items.aggregate(total=models.Sum("contract_quantity"))["total"]
        return total or Decimal("0")

    def component_totals(self):
        results = []
        for sc in self.spec_components.select_related("material").all():
            results.append(
                {
                    "id": sc.pk,
                    "label": sc.label,
                    "qty_per_unit": sc.qty_per_unit,
                    "total_quantity": calculate_total_quantity(
                        self.baseline_boq_quantity, sc.qty_per_unit
                    ),
                    "unit": sc.material.unit if sc.material else "",
                }
            )
        return results


class ProjectSpecificationComponent(models.Model):
    specification = models.ForeignKey(
        ProjectSpecification, on_delete=models.CASCADE, related_name="spec_components"
    )
    material = models.ForeignKey(
        ProjectMaterial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spec_components",
    )
    label = models.CharField(max_length=100)
    qty_per_unit = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.specification.name} - {self.label}"


class ProjectLabourCrew(models.Model):
    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="estimator_labour_crews",
    )
    source = models.ForeignKey(
        SystemLabourCrew,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_copies",
    )
    crew_type = models.CharField(max_length=100)
    crew_size = models.IntegerField(default=0)
    skilled = models.IntegerField(default=0)
    semi_skilled = models.IntegerField(default=0)
    general = models.IntegerField(default=0)
    daily_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    skilled_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    semi_skilled_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    general_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["crew_type"]
        unique_together = [("project", "crew_type")]
        verbose_name = "Project Labour Crew"

    def __str__(self):
        return self.crew_type

    @property
    def crew_daily_cost(self):
        return (
            Decimal(str(self.skilled)) * self.skilled_rate
            + Decimal(str(self.semi_skilled)) * self.semi_skilled_rate
            + Decimal(str(self.general)) * self.general_rate
        )


class ProjectLabourSpecification(models.Model):
    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="estimator_labour_specs",
    )
    source = models.ForeignKey(
        SystemLabourSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_copies",
    )
    section = models.CharField(max_length=100, blank=True)
    trade_name = models.CharField(max_length=200, blank=True)
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    crew = models.ForeignKey(
        ProjectLabourCrew,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="labour_specs",
    )
    daily_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    team_mix = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    site_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    tools_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    leadership_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)

    class Meta:
        ordering = ["section", "name"]
        unique_together = [("project", "name")]
        verbose_name = "Project Labour Specification"

    if TYPE_CHECKING:
        boq_items: "Manager[BOQItem]"

    def __str__(self):
        return self.name

    @property
    def daily_output(self):
        return (
            self.daily_production
            * self.team_mix
            * self.site_factor
            * self.tools_factor
            * self.leadership_factor
        )

    @property
    def daily_cost(self):
        if self.crew:
            return self.crew.crew_daily_cost
        return Decimal("0")

    @property
    def rate_per_unit(self):
        if self.daily_production and self.daily_production > 0:
            return self.daily_cost / self.daily_production
        return Decimal("0")

    @property
    def total_cost(self):
        return self.baseline_boq_quantity * self.daily_cost

    @property
    def baseline_boq_quantity(self):
        total = self.boq_items.aggregate(total=models.Sum("contract_quantity"))["total"]  # type: ignore[unresolved-attribute]
        return total or Decimal("0")


class ProjectPlantCost(models.Model):
    """Project-scoped plant & equipment cost."""

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="estimator_plant_costs",
    )
    source = models.ForeignKey(
        SystemPlantCost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_copies",
    )
    name = models.CharField(max_length=200)
    hourly_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["name"]
        unique_together = [("project", "name")]
        verbose_name = "Project Plant Cost"

    def __str__(self):
        return self.name


class ProjectPlantSpecification(models.Model):
    """Project-scoped plant specification."""

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="estimator_plant_specs",
    )
    source = models.ForeignKey(
        SystemPlantSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_copies",
    )
    section = models.CharField(max_length=100, blank=True)
    trade_name = models.CharField(max_length=200, blank=True)
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    plant_type = models.ForeignKey(
        ProjectPlantCost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plant_specs",
    )
    daily_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    operator_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    site_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)

    class Meta:
        ordering = ["section", "name"]
        unique_together = [("project", "name")]
        verbose_name = "Project Plant Specification"

    def __str__(self):
        return self.name

    @property
    def daily_output(self):
        return self.daily_production * self.operator_factor * self.site_factor

    @property
    def hourly_cost(self):
        if self.plant_type:
            return self.plant_type.hourly_rate
        return Decimal("0")

    @property
    def rate_per_unit(self):
        if self.daily_production and self.daily_production > 0:
            return self.hourly_cost / self.daily_production
        return Decimal("0")


class ProjectPreliminaryCost(models.Model):
    """Project-scoped preliminaries cost — single table with type column."""

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="estimator_preliminary_costs",
    )
    source = models.ForeignKey(
        SystemPreliminaryCost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_copies",
    )
    name = models.CharField(max_length=200)
    preliminary_type = models.CharField(
        max_length=30, choices=SystemPreliminaryCost.PRELIMINARY_TYPE_CHOICES
    )
    sum_value = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Sum/lump sum value"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    number_per_month = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True
    )
    monthly_rate = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, blank=True
    )
    months = models.DecimalField(max_digits=6, decimal_places=2, default=0, blank=True)

    class Meta:
        ordering = ["preliminary_type", "name"]
        verbose_name = "Project Preliminary Cost"

    def __str__(self):
        return f"{self.get_preliminary_type_display()} - {self.name}"

    @property
    def is_time_based(self):
        return self.preliminary_type.startswith("time_")

    @property
    def computed_amount(self):
        if self.is_time_based:
            return self.number_per_month * self.monthly_rate * self.months
        return self.amount


class ProjectPreliminarySpecification(models.Model):
    """Project-scoped preliminary specification."""

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="estimator_preliminary_specs",
    )
    source = models.ForeignKey(
        SystemPreliminarySpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_copies",
    )
    section = models.CharField(max_length=100, blank=True)
    trade_name = models.CharField(max_length=200, blank=True)
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["section", "name"]
        unique_together = [("project", "name")]
        verbose_name = "Project Preliminary Specification"

    def __str__(self):
        return self.name


# ═══════════════════════════════════════════════════════════════════
# ProjectAssumptions — Project-level global markups & wastage
# ═══════════════════════════════════════════════════════════════════


class ProjectAssumptions(models.Model):
    project = models.OneToOneField(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="estimator_assumptions",
    )
    material_markup_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    labour_markup_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    transport_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    wastage_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Project Assumptions"
        verbose_name_plural = "Project Assumptions"

    def __str__(self):
        return f"Assumptions for {self.project}"


# ═══════════════════════════════════════════════════════════════════
# BOQItem — Project-scoped, references Project* models
# ═══════════════════════════════════════════════════════════════════


class BOQItem(models.Model):
    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="estimator_boq_items",
        null=True,
        blank=True,
    )
    source_line_item = models.ForeignKey(
        LineItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estimator_boq_items",
    )
    section = models.CharField(max_length=200, blank=True)
    bill_no = models.CharField(max_length=200, blank=True)
    trade_code = models.ForeignKey(
        ProjectTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="boq_items",
    )
    specification = models.ForeignKey(
        ProjectSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="boq_items",
    )
    labour_specification = models.ForeignKey(
        ProjectLabourSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="boq_items",
    )
    item_no = models.CharField(max_length=20, blank=True)
    pay_ref = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=500, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    contract_quantity = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    contract_rate = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    progress_quantity = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    forecast_quantity = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    material = models.ForeignKey(
        ProjectMaterial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="boq_items",
        help_text="Direct material for items that don't use a specification",
    )
    is_section_header = models.BooleanField(default=False)
    material_markup_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    labour_markup_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    transport_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]
        verbose_name = "BoQ Item"
        verbose_name_plural = "BoQ Items"

    def __str__(self):
        return self.description or f"{self.section} - {self.bill_no}"

    @property
    def rate_type(self):
        if self.specification:
            return "spec"
        if self.material:
            return "material"
        return None

    @property
    def spec_display_name(self):
        if self.specification:
            return self.specification.name
        return None

    @property
    def contract_amount(self):
        return calculate_contract_amount(self.contract_quantity, self.contract_rate)

    @property
    def new_materials_rate(self):
        if self.specification:
            return calculate_materials_rate(None, self.specification.rate_per_unit)
        if self.material:
            return self.material.market_rate
        return None

    @property
    def new_labour_rate(self):
        if self.labour_specification:
            return self.labour_specification.rate_per_unit
        return None

    @property
    def new_materials_amount(self):
        rate = self.new_materials_rate
        if rate and self.contract_quantity:
            return rate * self.contract_quantity
        return None

    @property
    def new_labour_amount(self):
        rate = self.new_labour_rate
        if rate and self.contract_quantity:
            return rate * self.contract_quantity
        return None

    @property
    def baseline_new_price(self):
        mat = self.new_materials_rate or Decimal("0")
        lab = self.new_labour_rate or Decimal("0")
        total = mat + lab
        return total if total > 0 else None

    @property
    def progress_amount(self):
        return calculate_progress_amount(
            self.baseline_new_price, self.progress_quantity
        )

    @property
    def forecast_amount(self):
        return calculate_forecast_amount(
            self.baseline_new_price, self.forecast_quantity
        )


def sync_boq_from_lineitems(project):
    """
    Sync BOQItem records from BillOfQuantities LineItem records for a project.

    - Match key: source_line_item FK
    - Creates new BOQItems for new LineItems
    - Updates baseline fields on existing BOQItems (preserves user-edit fields)
    - Deletes BOQItems whose source LineItem no longer exists
    """
    line_items = (
        LineItem.objects.filter(project=project)
        .select_related("bill", "bill__structure")
        .order_by("row_index")
    )

    existing = {
        boq.source_line_item.pk: boq
        for boq in BOQItem.objects.filter(
            project=project, source_line_item__isnull=False
        )
    }

    seen_ids = set()
    created = 0
    updated = 0

    for li in line_items:
        seen_ids.add(li.pk)
        section_name = li.bill.structure.name if li.bill and li.bill.structure else ""
        bill_name = li.bill.name if li.bill else ""

        baseline_fields = {
            "section": section_name,
            "bill_no": bill_name,
            "item_no": li.item_number or "",
            "pay_ref": li.payment_reference or "",
            "description": li.description or "",
            "unit": li.unit_measurement or "",
            "contract_quantity": li.budgeted_quantity,
            "contract_rate": li.unit_price,
            "is_section_header": not li.is_work,
        }

        if li.pk in existing:
            boq = existing[li.pk]
            for field, value in baseline_fields.items():
                setattr(boq, field, value)
            boq.save()
            updated += 1
        else:
            BOQItem.objects.create(
                project=project,
                source_line_item=li,
                **baseline_fields,
            )
            created += 1

    # Delete BOQItems whose source LineItem is gone
    deleted_count, _ = (
        BOQItem.objects.filter(
            project=project,
            source_line_item__isnull=False,
        )
        .exclude(
            source_line_item_id__in=seen_ids,
        )
        .delete()
    )

    return created, updated, deleted_count
