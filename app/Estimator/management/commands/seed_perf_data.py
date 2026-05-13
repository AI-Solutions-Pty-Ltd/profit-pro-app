"""Seed a project with large volumes of perf-test data using bulk_create.

Usage:
    python manage.py seed_perf_data                                  # defaults
    python manage.py seed_perf_data --num-projects=50
    python manage.py seed_perf_data --project-id=3
    python manage.py seed_perf_data --boq-items=50000 --specs=2000
    python manage.py seed_perf_data --clear                          # wipe prior seed first

All seeded rows are tagged with the marker "[PERF]" in a recognizable text field
(name/section/description/etc.) so --clear can identify and remove them without
touching real data. When --num-projects is used, the [PERF] projects own all
their seeded data via FK cascade — deleting the projects sweeps everything.

Covers:
  * Project fields (dates, contract, retention%, status, VAT)
  * Estimator: trade codes, materials, labour crews/specs, material specs +
    components, BoQ items, plant costs/specs + components, preliminary costs +
    specs
  * BillOfQuantities: Structure, Bill, Package, LineItem
  * Cost: per-bill cost rows
"""

import random
import time
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from app.BillOfQuantities.models import Bill, LineItem, Package, Structure
from app.Cost.models import Cost
from app.Estimator.models import (
    BOQItem,
    ProjectLabourCrew,
    ProjectLabourSpecification,
    ProjectMaterial,
    ProjectPlantCost,
    ProjectPlantSpecification,
    ProjectPlantSpecificationComponent,
    ProjectPreliminaryCost,
    ProjectPreliminarySpecification,
    ProjectSpecification,
    ProjectSpecificationComponent,
    ProjectTradeCode,
    SystemPreliminaryCost,
)
from app.Project.models import Project

MARKER = "[PERF]"

UNITS = ["m", "m2", "m3", "kg", "t", "no", "sum", "hr", "day"]
TRADE_PREFIXES = [
    "PRE", "EAR", "CFR", "MAN", "STR", "ROO", "FIN", "ELE",
    "PLU", "MEC", "EXT", "PAI", "TIL", "CEI", "JOI", "GLA",
    "DOO", "WIN", "FLR", "WAL",
]


class Command(BaseCommand):
    help = "Seed a project with large volumes of perf-test data using bulk_create."

    def add_arguments(self, parser):
        parser.add_argument(
            "--project-id",
            type=int,
            default=None,
            help="Target project ID. If omitted, uses the first project.",
        )
        parser.add_argument(
            "--num-projects",
            type=int,
            default=None,
            help="Create N new [PERF]-tagged projects and seed each. "
            "Overrides --project-id.",
        )
        parser.add_argument("--boq-items", type=int, default=10_000)
        parser.add_argument("--specs", type=int, default=500)
        parser.add_argument("--components-per-spec", type=int, default=10)
        parser.add_argument("--materials", type=int, default=100)
        parser.add_argument(
            "--trade-codes", type=int, default=len(TRADE_PREFIXES)
        )
        parser.add_argument("--labour-crews", type=int, default=10)
        parser.add_argument("--labour-specs", type=int, default=50)
        # Plant + preliminary
        parser.add_argument("--plant-costs", type=int, default=30)
        parser.add_argument("--plant-specs", type=int, default=50)
        parser.add_argument("--plant-comp-per-spec", type=int, default=5)
        parser.add_argument("--prelim-costs", type=int, default=20)
        parser.add_argument("--prelim-specs", type=int, default=20)
        # BillOfQuantities
        parser.add_argument("--structures", type=int, default=3)
        parser.add_argument("--bills-per-structure", type=int, default=2)
        parser.add_argument("--packages-per-bill", type=int, default=2)
        parser.add_argument("--line-items", type=int, default=500)
        # Cost
        parser.add_argument("--costs-per-bill", type=int, default=50)
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete prior [PERF]-tagged rows on this project first.",
        )
        parser.add_argument(
            "--seed", type=int, default=42, help="Random seed for reproducibility."
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="bulk_create batch size.",
        )

    def handle(self, *args, **opts):
        random.seed(opts["seed"])

        if opts["num_projects"]:
            projects = self._make_projects(opts["num_projects"])
        else:
            projects = [self._resolve_project(opts["project_id"])]

        t0 = time.perf_counter()
        for idx, project in enumerate(projects, start=1):
            self.stdout.write(
                self.style.NOTICE(
                    f"[{idx}/{len(projects)}] Seeding project {project.pk} "
                    f"({project.name!r})"
                )
            )
            if opts["clear"]:
                self._clear_perf_rows(project)
            self._seed_one_project(project, opts)
        elapsed = time.perf_counter() - t0
        self.stdout.write(
            self.style.SUCCESS(
                f"Done in {elapsed:.1f}s across {len(projects)} project(s)."
            )
        )

    def _seed_one_project(self, project, opts):
        batch = opts["batch_size"]

        self._populate_project_fields(project)

        with transaction.atomic():
            trade_codes = self._make_trade_codes(project, opts["trade_codes"], batch)
            materials = self._make_materials(project, opts["materials"], batch)
            crews = self._make_labour_crews(project, opts["labour_crews"], batch)
            labour_specs = self._make_labour_specs(
                project, opts["labour_specs"], crews, batch
            )
            specs = self._make_specs(project, opts["specs"], trade_codes, batch)
            self._make_spec_components(
                specs, materials, opts["components_per_spec"], batch
            )
            plant_costs = self._make_plant_costs(project, opts["plant_costs"], batch)
            plant_specs = self._make_plant_specs(
                project, opts["plant_specs"], batch
            )
            self._make_plant_spec_components(
                plant_specs, plant_costs, opts["plant_comp_per_spec"], batch
            )
            self._make_preliminary_costs(project, opts["prelim_costs"], batch)
            self._make_preliminary_specs(project, opts["prelim_specs"], batch)
            structures = self._make_structures(project, opts["structures"], batch)
            bills = self._make_bills(
                structures, opts["bills_per_structure"], batch
            )
            packages = self._make_packages(
                bills, opts["packages_per_bill"], batch
            )
            self._make_line_items(
                project, structures, bills, packages, opts["line_items"], batch
            )
            self._make_costs(bills, opts["costs_per_bill"], batch)
            self._make_boq_items(
                project,
                opts["boq_items"],
                specs,
                labour_specs,
                materials,
                trade_codes,
                batch,
            )

    def _make_projects(self, n):
        """Create N bare Project rows. We skip ProjectFactory because its
        user-creation chain uses Faker emails that collide at this scale, and
        for perf testing we don't need users/clients/roles wired up."""
        self.stdout.write(self.style.NOTICE(f"Creating {n} [PERF] projects…"))
        objs = [
            Project(
                name=f"{MARKER} Project {i + 1:03d}",
                description=f"Perf-test seed project {i + 1}",
            )
            for i in range(n)
        ]
        return Project.objects.bulk_create(objs)

    # ── helpers ────────────────────────────────────────────────────

    def _resolve_project(self, project_id):
        if project_id is not None:
            try:
                return Project.objects.get(pk=project_id)
            except Project.DoesNotExist as e:
                raise CommandError(f"Project {project_id} not found.") from e
        project = Project.objects.first()
        if project is None:
            raise CommandError(
                "No projects exist. Create one first (admin or app UI) "
                "or pass --project-id."
            )
        return project

    def _clear_perf_rows(self, project):
        self.stdout.write("  Clearing prior [PERF] rows…")
        deleted = {
            "boq": BOQItem.objects.filter(
                project=project, section__startswith=MARKER
            ).delete()[0],
            "spec_components": ProjectSpecificationComponent.objects.filter(
                specification__project=project,
                specification__name__startswith=MARKER,
            ).delete()[0],
            "specs": ProjectSpecification.objects.filter(
                project=project, name__startswith=MARKER
            ).delete()[0],
            "labour_specs": ProjectLabourSpecification.objects.filter(
                project=project, name__startswith=MARKER
            ).delete()[0],
            "crews": ProjectLabourCrew.objects.filter(
                project=project, crew_type__startswith=MARKER
            ).delete()[0],
            "plant_spec_components": (
                ProjectPlantSpecificationComponent.objects.filter(
                    specification__project=project,
                    specification__name__startswith=MARKER,
                ).delete()[0]
            ),
            "plant_specs": ProjectPlantSpecification.objects.filter(
                project=project, name__startswith=MARKER
            ).delete()[0],
            "plant_costs": ProjectPlantCost.objects.filter(
                project=project, name__startswith=MARKER
            ).delete()[0],
            "prelim_specs": ProjectPreliminarySpecification.objects.filter(
                project=project, name__startswith=MARKER
            ).delete()[0],
            "prelim_costs": ProjectPreliminaryCost.objects.filter(
                project=project, name__startswith=MARKER
            ).delete()[0],
            "costs": Cost.objects.filter(
                bill__structure__project=project,
                description__startswith=MARKER,
            ).delete()[0],
            "line_items": LineItem.objects.filter(
                project=project, description__startswith=MARKER
            ).delete()[0],
            "packages": Package.objects.filter(
                bill__structure__project=project, name__startswith=MARKER
            ).delete()[0],
            "bills": Bill.objects.filter(
                structure__project=project, name__startswith=MARKER
            ).delete()[0],
            "structures": Structure.objects.filter(
                project=project, name__startswith=MARKER
            ).delete()[0],
            "materials": ProjectMaterial.objects.filter(
                project=project, material_code__startswith=MARKER
            ).delete()[0],
            "trade_codes": ProjectTradeCode.objects.filter(
                project=project, prefix__startswith=MARKER
            ).delete()[0],
        }
        self.stdout.write(f"    {deleted}")

    def _make_trade_codes(self, project, n, batch):
        self.stdout.write(f"  Trade codes ({n})…")
        objs = [
            ProjectTradeCode(
                project=project,
                prefix=f"{MARKER}{TRADE_PREFIXES[i % len(TRADE_PREFIXES)]}{i:03d}-",
                trade_name=f"Perf Trade {i}",
            )
            for i in range(n)
        ]
        return ProjectTradeCode.objects.bulk_create(objs, batch_size=batch)

    def _make_materials(self, project, n, batch):
        self.stdout.write(f"  Materials ({n})…")
        objs = [
            ProjectMaterial(
                project=project,
                trade_name=f"Perf trade {i % 20}",
                material_code=f"{MARKER}MAT-{i:05d}",
                unit=random.choice(UNITS),
                pack_qty=Decimal(random.choice([1, 10, 100, 1000])),
                pack_cost=Decimal(random.randint(50, 5000)),
                material_variety=f"variety {i % 5}",
                market_spec=f"spec {i % 7}",
            )
            for i in range(n)
        ]
        return ProjectMaterial.objects.bulk_create(objs, batch_size=batch)

    def _make_labour_crews(self, project, n, batch):
        self.stdout.write(f"  Labour crews ({n})…")
        objs = [
            ProjectLabourCrew(
                project=project,
                crew_type=f"{MARKER}Crew {i}",
                crew_size=random.randint(2, 8),
                skilled=random.randint(0, 3),
                semi_skilled=random.randint(0, 3),
                general=random.randint(1, 4),
                skilled_rate=Decimal(random.randint(300, 600)),
                semi_skilled_rate=Decimal(random.randint(200, 400)),
                general_rate=Decimal(random.randint(150, 250)),
            )
            for i in range(n)
        ]
        return ProjectLabourCrew.objects.bulk_create(objs, batch_size=batch)

    def _make_labour_specs(self, project, n, crews, batch):
        self.stdout.write(f"  Labour specs ({n})…")
        objs = [
            ProjectLabourSpecification(
                project=project,
                section=f"Section {i % 10}",
                trade_name=f"Trade {i % 20}",
                name=f"{MARKER}LSpec {i}",
                unit=random.choice(UNITS),
                crew=random.choice(crews) if crews else None,
                daily_production=Decimal(random.randint(5, 100)),
                team_mix=Decimal("1"),
                site_factor=Decimal("0.9"),
                tools_factor=Decimal("0.95"),
                leadership_factor=Decimal("1"),
            )
            for i in range(n)
        ]
        return ProjectLabourSpecification.objects.bulk_create(objs, batch_size=batch)

    def _make_specs(self, project, n, trade_codes, batch):
        self.stdout.write(f"  Material specs ({n})…")
        objs = [
            ProjectSpecification(
                project=project,
                section=f"Section {i % 15}",
                trade_code=random.choice(trade_codes) if trade_codes else None,
                unit_label=random.choice(UNITS),
                name=f"{MARKER}Spec {i:04d}",
                is_active=True,
            )
            for i in range(n)
        ]
        return ProjectSpecification.objects.bulk_create(objs, batch_size=batch)

    def _make_spec_components(self, specs, materials, per_spec, batch):
        total = len(specs) * per_spec
        self.stdout.write(
            f"  Spec components ({total:,} = {len(specs)} × {per_spec})…"
        )
        objs = []
        for spec in specs:
            for j in range(per_spec):
                objs.append(
                    ProjectSpecificationComponent(
                        specification=spec,
                        material=random.choice(materials) if materials else None,
                        label=f"comp {j}",
                        qty_per_unit=Decimal(
                            f"{random.uniform(0.01, 5):.4f}"
                        ),
                        sort_order=j,
                    )
                )
        ProjectSpecificationComponent.objects.bulk_create(objs, batch_size=batch)

    # ── Project field population ─────────────────────────────────

    def _populate_project_fields(self, project):
        """Fill in the project-level fields that ProjectFactory normally sets."""
        idx = int(project.name.rsplit(" ", 1)[-1]) if project.name[-3:].isdigit() else 1
        start = date.today() - timedelta(days=random.randint(0, 365))
        duration_days = random.randint(365, 1825)
        end = start + timedelta(days=duration_days)
        project.start_date = start
        project.end_date = end
        project.contract_number = f"PERF-CN-{idx:04d}"
        project.contract_clause = "NEC4 Option C"
        project.status = "ACTIVE"
        project.vat = True
        project.contractual_start_date = start
        project.contractual_completion_date = end
        project.contract_duration_days = duration_days
        project.approved_extension_days = 0
        project.retention_percentage = Decimal("5.00")
        project.retention_limit_percentage = Decimal("5.00")
        project.retention_release_practical = Decimal("50.00")
        project.advance_payment_percentage = Decimal("10.00")
        project.advance_recovery_percentage = Decimal("10.00")
        project.defects_liability_period = 365
        project.save()

    # ── Plant costs / specs ──────────────────────────────────────

    def _make_plant_costs(self, project, n, batch):
        self.stdout.write(f"  Plant costs ({n})…")
        objs = [
            ProjectPlantCost(
                project=project,
                name=f"{MARKER} Plant {i:03d}",
                hourly_production=Decimal(random.randint(1, 50)),
                hourly_rate=Decimal(random.randint(80, 800)),
            )
            for i in range(n)
        ]
        return ProjectPlantCost.objects.bulk_create(objs, batch_size=batch)

    def _make_plant_specs(self, project, n, batch):
        self.stdout.write(f"  Plant specs ({n})…")
        objs = [
            ProjectPlantSpecification(
                project=project,
                section=f"Section {i % 10}",
                trade_name=f"Trade {i % 15}",
                name=f"{MARKER} PSpec {i:04d}",
                unit=random.choice(UNITS),
                daily_production=Decimal(random.randint(10, 200)),
                operator_factor=Decimal("0.95"),
                site_factor=Decimal("0.9"),
                is_active=True,
            )
            for i in range(n)
        ]
        return ProjectPlantSpecification.objects.bulk_create(objs, batch_size=batch)

    def _make_plant_spec_components(self, specs, plant_costs, per_spec, batch):
        total = len(specs) * per_spec
        self.stdout.write(
            f"  Plant spec components ({total:,} = {len(specs)} × {per_spec})…"
        )
        objs = []
        for spec in specs:
            for j in range(per_spec):
                objs.append(
                    ProjectPlantSpecificationComponent(
                        specification=spec,
                        plant_type=random.choice(plant_costs) if plant_costs else None,
                        hours=Decimal(f"{random.uniform(1, 10):.2f}"),
                        sort_order=j,
                    )
                )
        ProjectPlantSpecificationComponent.objects.bulk_create(objs, batch_size=batch)

    # ── Preliminary costs / specs ────────────────────────────────

    def _make_preliminary_costs(self, project, n, batch):
        self.stdout.write(f"  Preliminary costs ({n})…")
        type_choices = [c[0] for c in SystemPreliminaryCost.PRELIMINARY_TYPE_CHOICES]
        objs = []
        for i in range(n):
            ptype = type_choices[i % len(type_choices)]
            is_time = ptype.startswith("time_")
            objs.append(
                ProjectPreliminaryCost(
                    project=project,
                    name=f"{MARKER} Prelim {i:03d}",
                    preliminary_type=ptype,
                    sum_value=Decimal(random.randint(1000, 50000)),
                    amount=(
                        Decimal(0)
                        if is_time
                        else Decimal(random.randint(5000, 100000))
                    ),
                    number_per_month=(
                        Decimal(random.randint(1, 5)) if is_time else Decimal(0)
                    ),
                    monthly_rate=(
                        Decimal(random.randint(1000, 20000))
                        if is_time
                        else Decimal(0)
                    ),
                    months=Decimal(random.randint(3, 18)) if is_time else Decimal(0),
                )
            )
        return ProjectPreliminaryCost.objects.bulk_create(objs, batch_size=batch)

    def _make_preliminary_specs(self, project, n, batch):
        self.stdout.write(f"  Preliminary specs ({n})…")
        type_choices = [c[0] for c in SystemPreliminaryCost.PRELIMINARY_TYPE_CHOICES]
        objs = [
            ProjectPreliminarySpecification(
                project=project,
                section=f"Section {i % 8}",
                trade_name=f"Trade {i % 10}",
                name=f"{MARKER} PrelimSpec {i:03d}",
                unit=random.choice(UNITS),
                preliminary_type=type_choices[i % len(type_choices)],
                is_active=True,
            )
            for i in range(n)
        ]
        return ProjectPreliminarySpecification.objects.bulk_create(
            objs, batch_size=batch
        )

    # ── BillOfQuantities: Structure / Bill / Package / LineItem ──

    def _make_structures(self, project, n, batch):
        self.stdout.write(f"  Structures ({n})…")
        objs = [
            Structure(
                project=project,
                name=f"{MARKER} Structure {i + 1}",
                description=f"Perf structure {i + 1}",
            )
            for i in range(n)
        ]
        return Structure.objects.bulk_create(objs, batch_size=batch)

    def _make_bills(self, structures, per_structure, batch):
        total = len(structures) * per_structure
        self.stdout.write(f"  Bills ({total} = {len(structures)} × {per_structure})…")
        objs = []
        for s in structures:
            for i in range(per_structure):
                objs.append(Bill(structure=s, name=f"{MARKER} Bill {i + 1}"))
        return Bill.objects.bulk_create(objs, batch_size=batch)

    def _make_packages(self, bills, per_bill, batch):
        total = len(bills) * per_bill
        self.stdout.write(f"  Packages ({total} = {len(bills)} × {per_bill})…")
        objs = []
        for b in bills:
            for i in range(per_bill):
                objs.append(Package(bill=b, name=f"{MARKER} Pkg {i + 1}"))
        return Package.objects.bulk_create(objs, batch_size=batch)

    def _make_line_items(self, project, structures, bills, packages, n, batch):
        self.stdout.write(f"  Line items ({n:,})…")
        if not bills:
            return []
        objs = []
        for i in range(n):
            structure = random.choice(structures) if structures else None
            # Pick a bill that belongs to that structure (if any)
            if structure:
                struct_bills = [b for b in bills if b.structure_id == structure.id]
                bill = random.choice(struct_bills) if struct_bills else random.choice(bills)
            else:
                bill = random.choice(bills)
            # Optional package on the bill
            if packages and random.random() < 0.5:
                bill_pkgs = [p for p in packages if p.bill_id == bill.id]
                package = random.choice(bill_pkgs) if bill_pkgs else None
            else:
                package = None
            is_work = random.random() < 0.85  # ~85% work items
            unit_price = (
                Decimal(f"{random.uniform(10, 5000):.2f}")
                if is_work
                else Decimal(0)
            )
            qty = Decimal(random.randint(1, 1000)) if is_work else Decimal(0)
            objs.append(
                LineItem(
                    project=project,
                    structure=structure,
                    bill=bill,
                    package=package,
                    row_index=i,
                    item_number=f"{i + 1:04d}",
                    payment_reference=f"PR-{i + 1:04d}",
                    description=f"{MARKER} Line {i + 1}",
                    is_work=is_work,
                    unit_measurement=random.choice(UNITS) if is_work else "",
                    unit_price=unit_price,
                    budgeted_quantity=qty,
                    total_price=unit_price * qty,
                    addendum=False,
                    special_item=False,
                )
            )
        return LineItem.objects.bulk_create(objs, batch_size=batch)

    # ── Cost (per Bill) ──────────────────────────────────────────

    def _make_costs(self, bills, per_bill, batch):
        total = len(bills) * per_bill
        self.stdout.write(f"  Costs ({total:,} = {len(bills)} × {per_bill})…")
        categories = ["MATERIAL", "LABOUR", "EQUIPMENT", "PLANT", "OTHER"]
        vat_rate = settings.VAT_RATE
        objs = []
        for b in bills:
            base_date = date.today() - timedelta(days=random.randint(0, 365))
            for i in range(per_bill):
                qty = Decimal(random.randint(1, 100))
                unit_price = Decimal(f"{random.uniform(50, 2000):.2f}")
                gross = qty * unit_price
                vat = random.random() < 0.85
                vat_amount = (gross * vat_rate) if vat else Decimal(0)
                objs.append(
                    Cost(
                        bill=b,
                        date=base_date - timedelta(days=i),
                        category=random.choice(categories),
                        description=f"{MARKER} Cost {i + 1}",
                        quantity=qty,
                        unit_price=unit_price,
                        gross=gross,
                        vat=vat,
                        vat_amount=vat_amount,
                        net=gross + vat_amount,
                    )
                )
        Cost.objects.bulk_create(objs, batch_size=batch)

    # ── BoQ items (Estimator) ────────────────────────────────────

    def _make_boq_items(
        self, project, n, specs, labour_specs, materials, trade_codes, batch
    ):
        self.stdout.write(f"  BoQ items ({n:,})…")
        objs = []
        section_every = max(50, n // 100)  # ~1% section headers
        for i in range(n):
            is_header = (i % section_every) == 0
            if is_header:
                objs.append(
                    BOQItem(
                        project=project,
                        section=f"{MARKER} Section {i // section_every}",
                        bill_no=f"Bill {(i // section_every) % 5}",
                        item_no="",
                        description=f"{MARKER} Section header {i // section_every}",
                        is_section_header=True,
                    )
                )
                continue
            spec = (
                random.choice(specs)
                if specs and random.random() < 0.7
                else None
            )
            lspec = (
                random.choice(labour_specs)
                if labour_specs and random.random() < 0.4
                else None
            )
            mat = (
                random.choice(materials)
                if not spec and materials and random.random() < 0.5
                else None
            )
            tc = (
                spec.trade_code
                if spec and spec.trade_code_id
                else (random.choice(trade_codes) if trade_codes else None)
            )
            objs.append(
                BOQItem(
                    project=project,
                    section=f"{MARKER} Section {i // section_every}",
                    bill_no=f"Bill {(i // section_every) % 5}",
                    item_no=f"{i:05d}",
                    description=f"{MARKER} BoQ line {i} — "
                    f"{spec.name if spec else (mat.material_code if mat else 'misc')}",
                    unit=random.choice(UNITS),
                    contract_quantity=Decimal(random.randint(1, 1000)),
                    contract_rate=Decimal(f"{random.uniform(10, 5000):.2f}"),
                    progress_quantity=Decimal(random.randint(0, 500)),
                    forecast_quantity=Decimal(random.randint(0, 1200)),
                    trade_code=tc,
                    specification=spec,
                    labour_specification=lspec,
                    material=mat,
                    is_section_header=False,
                )
            )
        BOQItem.objects.bulk_create(objs, batch_size=batch)
