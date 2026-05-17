from decimal import Decimal
from typing import TYPE_CHECKING

from django.core.validators import MinValueValidator
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


def _compute_market_rate(pack_cost, pack_qty):
    """Effective unit rate for a material from a pack quote (e.g. 2800 / 1000
    bricks). Returns 0 when pack_qty is missing/zero to avoid div-by-zero.
    """
    cost = Decimal(pack_cost or 0)
    qty = Decimal(pack_qty or 0)
    if qty <= 0:
        return Decimal("0")
    return cost / qty


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
    material_code = models.CharField(max_length=255, unique=True)
    unit = models.CharField(max_length=20, blank=True)
    pack_qty = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    pack_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    market_rate = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    material_variety = models.CharField(max_length=100, blank=True)
    market_spec = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "estimator_material"
        ordering = ["material_code"]

    def __str__(self):
        return self.material_code

    def save(self, *args, **kwargs):
        self.market_rate = _compute_market_rate(self.pack_cost, self.pack_qty)
        super().save(*args, **kwargs)


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
    is_active = models.BooleanField(default=True)

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
        for sc in self.spec_components.all():
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
        components = self.components
        if components:
            return calculate_rate_per_unit(components)
        elif self.system_spec:
            return self.system_spec.rate_per_unit
        return Decimal("0")

    @property
    def baseline_boq_quantity(self):
        return self.boq_quantity or Decimal("0")

    def component_totals(self):
        boq_qty = self.baseline_boq_quantity
        results = []
        for sc in self.spec_components.all():
            results.append(
                {
                    "id": sc.pk,
                    "label": sc.label,
                    "qty_per_unit": sc.qty_per_unit,
                    "material_id": sc.material_id,
                    "material_code": sc.material.material_code if sc.material else "",
                    "total_quantity": calculate_total_quantity(
                        boq_qty, sc.qty_per_unit
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
    crew_size = models.IntegerField(default=0, editable=False)
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

    def save(self, *args, **kwargs):
        self.crew_size = (
            (self.skilled or 0) + (self.semi_skilled or 0) + (self.general or 0)
        )
        super().save(*args, **kwargs)

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
    trade_code = models.ForeignKey(
        SystemTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="labour_specifications",
    )
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
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "estimator_labourspecification"
        ordering = ["section", "name"]
        verbose_name = "System Labour Specification"

    def save(self, *args, **kwargs):
        # Keep the legacy free-text trade_name mirrored from the FK so
        # existing list/report/filter code keeps working.
        if self.trade_code_id:
            self.trade_name = self.trade_code.trade_name
        super().save(*args, **kwargs)

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
        output = self.daily_output
        if output and output > 0:
            return self.daily_cost / output
        return Decimal("0")

    @property
    def total_cost(self):
        return self.baseline_boq_quantity * self.rate_per_unit

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
    trade_code = models.ForeignKey(
        SystemTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plant_specifications",
    )
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    daily_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    operator_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    site_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "name"]
        verbose_name = "System Plant Specification"

    if TYPE_CHECKING:
        components: "Manager[SystemPlantSpecificationComponent]"

    def save(self, *args, **kwargs):
        # Keep the legacy free-text trade_name mirrored from the FK so
        # existing list/report/filter code keeps working.
        if self.trade_code_id:
            self.trade_name = self.trade_code.trade_name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def daily_output(self):
        return self.daily_production * self.operator_factor * self.site_factor

    @property
    def rate_per_unit(self):
        total = Decimal("0")
        for comp in self.components.select_related("plant_type").all():
            if comp.plant_type:
                total += comp.plant_type.hourly_rate * comp.hours
        return total

    @property
    def daily_cost(self):
        return self.daily_output * self.rate_per_unit


class SystemPlantSpecificationComponent(models.Model):
    """A single plant-type/hours entry attached to a system plant spec."""

    specification = models.ForeignKey(
        SystemPlantSpecification,
        on_delete=models.CASCADE,
        related_name="components",
    )
    plant_type = models.ForeignKey(
        SystemPlantCost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spec_components",
    )
    hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        name = self.plant_type.name if self.plant_type else "—"
        return f"{self.specification.name} · {name} ({self.hours}h)"


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
        return f"{self.get_preliminary_type_display()} - {self.name}"  # ty:ignore[unresolved-attribute]

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
    trade_code = models.ForeignKey(
        SystemTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preliminary_specifications",
    )
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    preliminary_type = models.CharField(
        max_length=30,
        choices=SystemPreliminaryCost.PRELIMINARY_TYPE_CHOICES,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "name"]
        verbose_name = "System Preliminary Specification"

    def save(self, *args, **kwargs):
        # Keep the legacy free-text trade_name mirrored from the FK so
        # existing list/report/filter code keeps working.
        if self.trade_code_id:
            self.trade_name = self.trade_code.trade_name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def amount(self):
        if not self.preliminary_type:
            return Decimal("0")
        total = Decimal("0")
        for cost in SystemPreliminaryCost.objects.filter(
            preliminary_type=self.preliminary_type
        ):
            total += cost.computed_amount
        return total


class SystemMaterialSpec(models.Model):
    """Reusable material specification library at system level."""

    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=20, default="m3")
    is_active = models.BooleanField(default=True)

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


class SystemItemLibraryEntry(models.Model):
    """System-level item library entry — a pre-configured BoQ template row
    that bundles a trade code, component, and the four spec FKs."""

    trade_code = models.ForeignKey(
        SystemTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    item_code = models.CharField(max_length=50, blank=True)
    accounts_code = models.CharField(max_length=50, blank=True)
    component = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500)
    unit = models.CharField(max_length=20, blank=True)
    material_spec = models.ForeignKey(
        SystemMaterialSpec,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    labour_spec = models.ForeignKey(
        SystemLabourSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    plant_spec = models.ForeignKey(
        SystemPlantSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    preliminary_spec = models.ForeignKey(
        SystemPreliminarySpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]
        verbose_name = "System Item Library Entry"
        verbose_name_plural = "System Item Library Entries"
        indexes = [
            models.Index(fields=["trade_code", "component"]),
            models.Index(fields=["trade_code", "description"]),
        ]

    def __str__(self):
        return self.description or f"{self.component} ({self.unit})"


# ═══════════════════════════════════════════════════════════════════
# Contractor-Scoped Library Models (per Company; sync-from-System,
# sync-to-Project)
# ═══════════════════════════════════════════════════════════════════


class ContractorTradeCode(models.Model):
    company = models.ForeignKey(
        "Project.Company",
        on_delete=models.CASCADE,
        related_name="estimator_trade_codes",
        limit_choices_to={"type": "CONTRACTOR"},
    )
    source = models.ForeignKey(
        SystemTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_copies",
    )
    prefix = models.CharField(max_length=20)
    trade_name = models.CharField(max_length=100)

    class Meta:
        ordering = ["prefix"]
        unique_together = [("company", "prefix")]

    def __str__(self):
        return self.trade_code

    @property
    def trade_code(self):
        return f"{self.prefix}{self.trade_name}"


class ContractorMaterial(models.Model):
    company = models.ForeignKey(
        "Project.Company",
        on_delete=models.CASCADE,
        related_name="estimator_materials",
        limit_choices_to={"type": "CONTRACTOR"},
    )
    source = models.ForeignKey(
        SystemMaterial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_copies",
    )
    trade_name = models.CharField(max_length=200, blank=True)
    material_code = models.CharField(max_length=255)
    unit = models.CharField(max_length=20, blank=True)
    pack_qty = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    pack_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    market_rate = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    material_variety = models.CharField(max_length=100, blank=True)
    market_spec = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["material_code"]
        unique_together = [("company", "material_code")]

    def __str__(self):
        return self.material_code

    def save(self, *args, **kwargs):
        self.market_rate = _compute_market_rate(self.pack_cost, self.pack_qty)
        super().save(*args, **kwargs)


class ContractorSpecification(models.Model):
    company = models.ForeignKey(
        "Project.Company",
        on_delete=models.CASCADE,
        related_name="estimator_specifications",
        limit_choices_to={"type": "CONTRACTOR"},
    )
    source = models.ForeignKey(
        SystemSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_copies",
    )
    section = models.CharField(max_length=100, blank=True)
    trade_code = models.ForeignKey(
        ContractorTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="specifications",
    )
    unit_label = models.CharField(max_length=20, default="m3")
    name = models.CharField(max_length=100)
    boq_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    contractor_spec = models.ForeignKey(
        "ContractorMaterialSpec",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_specs",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "name"]
        unique_together = [("company", "name")]

    if TYPE_CHECKING:
        spec_components: "Manager[ContractorSpecificationComponent]"

    def __str__(self):
        return self.name

    @property
    def components(self):
        comps = []
        for sc in self.spec_components.all():
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
        components = self.components
        if components:
            return calculate_rate_per_unit(components)
        elif self.contractor_spec:
            return self.contractor_spec.rate_per_unit
        return Decimal("0")

    @property
    def baseline_boq_quantity(self):
        return self.boq_quantity or Decimal("0")

    def component_totals(self):
        boq_qty = self.baseline_boq_quantity
        results = []
        for sc in self.spec_components.all():
            results.append(
                {
                    "id": sc.pk,
                    "label": sc.label,
                    "qty_per_unit": sc.qty_per_unit,
                    "material_id": sc.material_id,
                    "material_code": sc.material.material_code if sc.material else "",
                    "total_quantity": calculate_total_quantity(
                        boq_qty, sc.qty_per_unit
                    ),
                    "unit": sc.material.unit if sc.material else "",
                }
            )
        return results


class ContractorSpecificationComponent(models.Model):
    specification = models.ForeignKey(
        ContractorSpecification,
        on_delete=models.CASCADE,
        related_name="spec_components",
    )
    material = models.ForeignKey(
        ContractorMaterial,
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


class ContractorLabourCrew(models.Model):
    company = models.ForeignKey(
        "Project.Company",
        on_delete=models.CASCADE,
        related_name="estimator_labour_crews",
        limit_choices_to={"type": "CONTRACTOR"},
    )
    source = models.ForeignKey(
        SystemLabourCrew,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_copies",
    )
    crew_type = models.CharField(max_length=100)
    crew_size = models.IntegerField(default=0, editable=False)
    skilled = models.IntegerField(default=0)
    semi_skilled = models.IntegerField(default=0)
    general = models.IntegerField(default=0)
    daily_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    skilled_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    semi_skilled_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    general_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["crew_type"]
        unique_together = [("company", "crew_type")]
        verbose_name = "Contractor Labour Crew"

    def __str__(self):
        return self.crew_type

    def save(self, *args, **kwargs):
        self.crew_size = (
            (self.skilled or 0) + (self.semi_skilled or 0) + (self.general or 0)
        )
        super().save(*args, **kwargs)

    @property
    def crew_daily_cost(self):
        return (
            Decimal(str(self.skilled)) * self.skilled_rate
            + Decimal(str(self.semi_skilled)) * self.semi_skilled_rate
            + Decimal(str(self.general)) * self.general_rate
        )


class ContractorLabourSpecification(models.Model):
    company = models.ForeignKey(
        "Project.Company",
        on_delete=models.CASCADE,
        related_name="estimator_labour_specs",
        limit_choices_to={"type": "CONTRACTOR"},
    )
    source = models.ForeignKey(
        SystemLabourSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_copies",
    )
    section = models.CharField(max_length=100, blank=True)
    trade_name = models.CharField(max_length=200, blank=True)
    trade_code = models.ForeignKey(
        ContractorTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="labour_specifications",
    )
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    crew = models.ForeignKey(
        ContractorLabourCrew,
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
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "name"]
        unique_together = [("company", "name")]
        verbose_name = "Contractor Labour Specification"

    def save(self, *args, **kwargs):
        # Keep the legacy free-text trade_name mirrored from the FK so
        # existing list/report/filter code keeps working.
        if self.trade_code_id:
            self.trade_name = self.trade_code.trade_name
        super().save(*args, **kwargs)

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
        output = self.daily_output
        if output and output > 0:
            return self.daily_cost / output
        return Decimal("0")

    @property
    def total_cost(self):
        return self.baseline_boq_quantity * self.rate_per_unit

    @property
    def baseline_boq_quantity(self):
        return self.boq_quantity or Decimal("0")


class ContractorPlantCost(models.Model):
    """Contractor-scoped plant & equipment cost library."""

    company = models.ForeignKey(
        "Project.Company",
        on_delete=models.CASCADE,
        related_name="estimator_plant_costs",
        limit_choices_to={"type": "CONTRACTOR"},
    )
    source = models.ForeignKey(
        SystemPlantCost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_copies",
    )
    name = models.CharField(max_length=200)
    hourly_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["name"]
        unique_together = [("company", "name")]
        verbose_name = "Contractor Plant Cost"

    def __str__(self):
        return self.name


class ContractorPlantSpecification(models.Model):
    """Contractor-scoped plant specification library."""

    company = models.ForeignKey(
        "Project.Company",
        on_delete=models.CASCADE,
        related_name="estimator_plant_specs",
        limit_choices_to={"type": "CONTRACTOR"},
    )
    source = models.ForeignKey(
        SystemPlantSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_copies",
    )
    section = models.CharField(max_length=100, blank=True)
    trade_name = models.CharField(max_length=200, blank=True)
    trade_code = models.ForeignKey(
        ContractorTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plant_specifications",
    )
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    daily_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    operator_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    site_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "name"]
        unique_together = [("company", "name")]
        verbose_name = "Contractor Plant Specification"

    if TYPE_CHECKING:
        components: "Manager[ContractorPlantSpecificationComponent]"

    def save(self, *args, **kwargs):
        # Keep the legacy free-text trade_name mirrored from the FK so
        # existing list/report/filter code keeps working.
        if self.trade_code_id:
            self.trade_name = self.trade_code.trade_name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def daily_output(self):
        return self.daily_production * self.operator_factor * self.site_factor

    @property
    def rate_per_unit(self):
        total = Decimal("0")
        for comp in self.components.select_related("plant_type").all():
            if comp.plant_type:
                total += comp.plant_type.hourly_rate * comp.hours
        return total

    @property
    def daily_cost(self):
        return self.daily_output * self.rate_per_unit


class ContractorPlantSpecificationComponent(models.Model):
    """A single plant-type/hours entry attached to a contractor plant spec."""

    specification = models.ForeignKey(
        ContractorPlantSpecification,
        on_delete=models.CASCADE,
        related_name="components",
    )
    plant_type = models.ForeignKey(
        ContractorPlantCost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spec_components",
    )
    hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        name = self.plant_type.name if self.plant_type else "—"
        return f"{self.specification.name} · {name} ({self.hours}h)"


class ContractorPreliminaryCost(models.Model):
    """Contractor-scoped preliminaries cost — single table with type column."""

    company = models.ForeignKey(
        "Project.Company",
        on_delete=models.CASCADE,
        related_name="estimator_preliminary_costs",
        limit_choices_to={"type": "CONTRACTOR"},
    )
    source = models.ForeignKey(
        SystemPreliminaryCost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_copies",
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
        verbose_name = "Contractor Preliminary Cost"

    def __str__(self):
        return f"{self.get_preliminary_type_display()} - {self.name}"  # ty:ignore[unresolved-attribute]

    @property
    def is_time_based(self):
        return self.preliminary_type.startswith("time_")

    @property
    def computed_amount(self):
        if self.is_time_based:
            return self.number_per_month * self.monthly_rate * self.months
        return self.amount


class ContractorPreliminarySpecification(models.Model):
    """Contractor-scoped preliminary specification."""

    company = models.ForeignKey(
        "Project.Company",
        on_delete=models.CASCADE,
        related_name="estimator_preliminary_specs",
        limit_choices_to={"type": "CONTRACTOR"},
    )
    source = models.ForeignKey(
        SystemPreliminarySpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_copies",
    )
    section = models.CharField(max_length=100, blank=True)
    trade_name = models.CharField(max_length=200, blank=True)
    trade_code = models.ForeignKey(
        ContractorTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preliminary_specifications",
    )
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    preliminary_type = models.CharField(
        max_length=30,
        choices=SystemPreliminaryCost.PRELIMINARY_TYPE_CHOICES,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "name"]
        unique_together = [("company", "name")]
        verbose_name = "Contractor Preliminary Specification"

    def save(self, *args, **kwargs):
        # Keep the legacy free-text trade_name mirrored from the FK so
        # existing list/report/filter code keeps working.
        if self.trade_code_id:
            self.trade_name = self.trade_code.trade_name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def amount(self):
        if not self.preliminary_type:
            return Decimal("0")
        total = Decimal("0")
        for cost in ContractorPreliminaryCost.objects.filter(
            company_id=self.company_id,
            preliminary_type=self.preliminary_type,
        ):
            total += cost.computed_amount
        return total


class ContractorMaterialSpec(models.Model):
    """Reusable material specification library at contractor level."""

    company = models.ForeignKey(
        "Project.Company",
        on_delete=models.CASCADE,
        related_name="estimator_material_specs",
        limit_choices_to={"type": "CONTRACTOR"},
    )
    source = models.ForeignKey(
        SystemMaterialSpec,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_copies",
    )
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, default="m3")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Contractor Material Spec"
        verbose_name_plural = "Contractor Material Specs"
        ordering = ["name"]
        unique_together = [("company", "name")]

    if TYPE_CHECKING:
        contractor_spec_components: "Manager[ContractorMaterialSpecComponent]"

    def __str__(self):
        return self.name

    @property
    def components(self):
        comps = []
        for sc in self.contractor_spec_components.select_related("material").all():
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


class ContractorMaterialSpecComponent(models.Model):
    """Component of a contractor-level material specification."""

    spec = models.ForeignKey(
        ContractorMaterialSpec,
        on_delete=models.CASCADE,
        related_name="contractor_spec_components",
    )
    material = models.ForeignKey(
        ContractorMaterial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_spec_components",
    )
    label = models.CharField(max_length=100)
    qty_per_unit = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.spec.name} - {self.label}"


class ContractorItemLibraryEntry(models.Model):
    """Contractor-scoped item library entry; cloned from System."""

    company = models.ForeignKey(
        "Project.Company",
        on_delete=models.CASCADE,
        related_name="estimator_library_entries",
        limit_choices_to={"type": "CONTRACTOR"},
    )
    source = models.ForeignKey(
        SystemItemLibraryEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contractor_copies",
    )
    trade_code = models.ForeignKey(
        ContractorTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    item_code = models.CharField(max_length=50, blank=True)
    accounts_code = models.CharField(max_length=50, blank=True)
    component = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500)
    unit = models.CharField(max_length=20, blank=True)
    material_spec = models.ForeignKey(
        ContractorMaterialSpec,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    labour_spec = models.ForeignKey(
        ContractorLabourSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    plant_spec = models.ForeignKey(
        ContractorPlantSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    preliminary_spec = models.ForeignKey(
        ContractorPreliminarySpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]
        verbose_name = "Contractor Item Library Entry"
        verbose_name_plural = "Contractor Item Library Entries"
        indexes = [
            models.Index(fields=["company", "trade_code", "component"]),
            models.Index(fields=["company", "trade_code", "description"]),
        ]

    def __str__(self):
        return self.description or f"{self.component} ({self.unit})"


# ═══════════════════════════════════════════════════════════════════
# Project-Scoped Models (cloned from contractor library per project)
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
    material_code = models.CharField(max_length=255)
    unit = models.CharField(max_length=20, blank=True)
    pack_qty = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    pack_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    market_rate = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    material_variety = models.CharField(max_length=100, blank=True)
    market_spec = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["material_code"]
        unique_together = [("project", "material_code")]

    def __str__(self):
        return self.material_code

    def save(self, *args, **kwargs):
        self.market_rate = _compute_market_rate(self.pack_cost, self.pack_qty)
        super().save(*args, **kwargs)


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
    is_active = models.BooleanField(default=True)

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
        for sc in self.spec_components.all():
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
        components = self.components
        if components:
            return calculate_rate_per_unit(components)
        elif self.source:
            return self.source.rate_per_unit
        return Decimal("0")

    @property
    def baseline_boq_quantity(self):
        if hasattr(self, "_baseline_boq_qty"):
            return self._baseline_boq_qty or Decimal("0")
        total = self.boq_items.aggregate(total=models.Sum("contract_quantity"))["total"]
        return total or Decimal("0")

    def component_totals(self):
        boq_qty = self.baseline_boq_quantity
        results = []
        for sc in self.spec_components.all():
            results.append(
                {
                    "id": sc.pk,
                    "label": sc.label,
                    "qty_per_unit": sc.qty_per_unit,
                    "material_id": sc.material_id,
                    "material_code": sc.material.material_code if sc.material else "",
                    "total_quantity": calculate_total_quantity(
                        boq_qty, sc.qty_per_unit
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
    crew_size = models.IntegerField(default=0, editable=False)
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

    def save(self, *args, **kwargs):
        self.crew_size = (
            (self.skilled or 0) + (self.semi_skilled or 0) + (self.general or 0)
        )
        super().save(*args, **kwargs)

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
    trade_code = models.ForeignKey(
        ProjectTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="labour_specifications",
    )
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
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "name"]
        unique_together = [("project", "name")]
        verbose_name = "Project Labour Specification"

    if TYPE_CHECKING:
        boq_items: "Manager[BOQItem]"

    def save(self, *args, **kwargs):
        # Keep the legacy free-text trade_name mirrored from the FK so
        # existing list/report/filter code keeps working.
        if self.trade_code_id:
            self.trade_name = self.trade_code.trade_name
        super().save(*args, **kwargs)

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
        output = self.daily_output
        if output and output > 0:
            return self.daily_cost / output
        return Decimal("0")

    @property
    def total_cost(self):
        return self.baseline_boq_quantity * self.rate_per_unit

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
    trade_code = models.ForeignKey(
        ProjectTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plant_specifications",
    )
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    daily_production = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    operator_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    site_factor = models.DecimalField(max_digits=6, decimal_places=4, default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "name"]
        unique_together = [("project", "name")]
        verbose_name = "Project Plant Specification"

    if TYPE_CHECKING:
        components: "Manager[ProjectPlantSpecificationComponent]"

    def save(self, *args, **kwargs):
        # Keep the legacy free-text trade_name mirrored from the FK so
        # existing list/report/filter code keeps working.
        if self.trade_code_id:
            self.trade_name = self.trade_code.trade_name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def daily_output(self):
        return self.daily_production * self.operator_factor * self.site_factor

    @property
    def rate_per_unit(self):
        total = Decimal("0")
        for comp in self.components.select_related("plant_type").all():
            if comp.plant_type:
                total += comp.plant_type.hourly_rate * comp.hours
        return total

    @property
    def daily_cost(self):
        return self.daily_output * self.rate_per_unit


class ProjectPlantSpecificationComponent(models.Model):
    """A single plant-type/hours entry attached to a project plant spec."""

    specification = models.ForeignKey(
        ProjectPlantSpecification,
        on_delete=models.CASCADE,
        related_name="components",
    )
    plant_type = models.ForeignKey(
        ProjectPlantCost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spec_components",
    )
    hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        name = self.plant_type.name if self.plant_type else "—"
        return f"{self.specification.name} · {name} ({self.hours}h)"


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
        return f"{self.get_preliminary_type_display()} - {self.name}"  # ty:ignore[unresolved-attribute]

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
    trade_code = models.ForeignKey(
        ProjectTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preliminary_specifications",
    )
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, blank=True)
    preliminary_type = models.CharField(
        max_length=30,
        choices=SystemPreliminaryCost.PRELIMINARY_TYPE_CHOICES,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "name"]
        unique_together = [("project", "name")]
        verbose_name = "Project Preliminary Specification"

    def save(self, *args, **kwargs):
        # Keep the legacy free-text trade_name mirrored from the FK so
        # existing list/report/filter code keeps working.
        if self.trade_code_id:
            self.trade_name = self.trade_code.trade_name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def amount(self):
        if not self.preliminary_type:
            return Decimal("0")
        total = Decimal("0")
        for cost in ProjectPreliminaryCost.objects.filter(
            project_id=self.project_id,
            preliminary_type=self.preliminary_type,
        ):
            total += cost.computed_amount
        return total


class ProjectItemLibraryEntry(models.Model):
    """Project-scoped item library entry; cloned from System or Contractor."""

    project = models.ForeignKey(
        "Project.Project",
        on_delete=models.CASCADE,
        related_name="estimator_library_entries",
    )
    source_system = models.ForeignKey(
        SystemItemLibraryEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_copies",
    )
    source_contractor = models.ForeignKey(
        ContractorItemLibraryEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_copies",
    )
    trade_code = models.ForeignKey(
        ProjectTradeCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    item_code = models.CharField(max_length=50, blank=True)
    accounts_code = models.CharField(max_length=50, blank=True)
    component = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500)
    unit = models.CharField(max_length=20, blank=True)
    material_spec = models.ForeignKey(
        ProjectSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    labour_spec = models.ForeignKey(
        ProjectLabourSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    plant_spec = models.ForeignKey(
        ProjectPlantSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    preliminary_spec = models.ForeignKey(
        ProjectPreliminarySpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="library_entries",
    )
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]
        verbose_name = "Project Item Library Entry"
        verbose_name_plural = "Project Item Library Entries"
        indexes = [
            models.Index(fields=["project", "trade_code", "component"]),
            models.Index(fields=["project", "trade_code", "description"]),
        ]

    if TYPE_CHECKING:
        boq_items: "Manager[BOQItem]"

    def __str__(self):
        return self.description or f"{self.component} ({self.unit})"


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
    plant_specification = models.ForeignKey(
        ProjectPlantSpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="boq_items",
    )
    preliminary_specification = models.ForeignKey(
        ProjectPreliminarySpecification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="boq_items",
    )
    library_entry = models.ForeignKey(
        ProjectItemLibraryEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="boq_items",
    )
    component = models.CharField(max_length=200, blank=True)
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
    crew_count = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(0)],
        help_text="Multiplier for the number of crews working on this item.",
    )

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
    def _wastage_pct(self):
        if not hasattr(self, "_cached_wastage_pct"):
            try:
                self._cached_wastage_pct = (
                    self.project.estimator_assumptions.wastage_pct or Decimal("0")
                )
            except Exception:
                self._cached_wastage_pct = Decimal("0")
        return self._cached_wastage_pct

    @property
    def _wastage_factor(self):
        return Decimal("1") + self._wastage_pct / Decimal("100")

    @property
    def _material_markup_factor(self):
        markup = (self.material_markup_pct or Decimal("0")) + (
            self.transport_pct or Decimal("0")
        )
        return Decimal("1") + markup / Decimal("100")

    @property
    def _labour_markup_factor(self):
        markup = self.labour_markup_pct or Decimal("0")
        return Decimal("1") + markup / Decimal("100")

    @property
    def new_materials_rate(self):
        if self.specification and self.specification.is_active:
            base = calculate_materials_rate(None, self.specification.rate_per_unit)
        elif self.material:
            base = self.material.market_rate
        else:
            return None
        if base is None:
            return None
        return base * self._material_markup_factor

    @property
    def new_labour_rate(self):
        if self.labour_specification and self.labour_specification.is_active:
            base = self.labour_specification.rate_per_unit
            if base is None:
                return None
            return base * self._labour_markup_factor
        return None

    @property
    def new_materials_amount(self):
        rate = self.new_materials_rate
        if rate and self.contract_quantity:
            return self.contract_quantity * self._wastage_factor * rate
        return None

    @property
    def new_labour_amount(self):
        rate = self.new_labour_rate
        if rate and self.contract_quantity:
            return self.contract_quantity * rate
        return None

    @property
    def new_plant_rate(self):
        if self.plant_specification and self.plant_specification.is_active:
            return self.plant_specification.rate_per_unit
        return None

    @property
    def new_plant_amount(self):
        rate = self.new_plant_rate
        if rate and self.contract_quantity:
            return rate * self.contract_quantity
        return None

    @property
    def new_preliminary_rate(self):
        if self.preliminary_specification and self.preliminary_specification.is_active:
            return self.preliminary_specification.amount
        return None

    @property
    def new_preliminary_amount(self):
        rate = self.new_preliminary_rate
        if rate and self.contract_quantity:
            return rate * self.contract_quantity
        return None

    @property
    def baseline_new_price(self):
        mat = (self.new_materials_rate or Decimal("0")) * self._wastage_factor
        lab = self.new_labour_rate or Decimal("0")
        plant = self.new_plant_rate or Decimal("0")
        prelim = self.new_preliminary_rate or Decimal("0")
        total = mat + lab + plant + prelim
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

    @property
    def _material_base_amount(self):
        """Material amount on contract qty before markup/transport (incl. wastage)."""
        rate = self.new_materials_rate
        factor = self._material_markup_factor
        if rate is None or not self.contract_quantity or factor == 0:
            return Decimal("0")
        base_rate = rate / factor
        return base_rate * self.contract_quantity * self._wastage_factor

    @property
    def _labour_base_amount(self):
        """Labour amount on contract qty before markup."""
        rate = self.new_labour_rate
        factor = self._labour_markup_factor
        if rate is None or not self.contract_quantity or factor == 0:
            return Decimal("0")
        base_rate = rate / factor
        return base_rate * self.contract_quantity

    @property
    def markup_amount(self):
        """Money added on top of base cost by material & labour markup %
        (transport excluded — it is reported separately)."""
        mat = self._material_base_amount * (
            self.material_markup_pct or Decimal("0")
        ) / Decimal("100")
        lab = self._labour_base_amount * (
            self.labour_markup_pct or Decimal("0")
        ) / Decimal("100")
        return mat + lab

    @property
    def transport_amount(self):
        """Money added on top of base material cost by transport %."""
        return self._material_base_amount * (
            self.transport_pct or Decimal("0")
        ) / Decimal("100")


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

    assumptions = ProjectAssumptions.objects.filter(project=project).first()
    markup_defaults = (
        {
            "material_markup_pct": assumptions.material_markup_pct,
            "labour_markup_pct": assumptions.labour_markup_pct,
            "transport_pct": assumptions.transport_pct,
        }
        if assumptions
        else {}
    )

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
                **markup_defaults,
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
