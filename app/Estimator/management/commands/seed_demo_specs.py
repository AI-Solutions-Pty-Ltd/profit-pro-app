"""Seed material specifications and labour specifications for all trades.

Creates demonstration data for trades that currently have no specs,
so that every BoQ bill category has associated rate calculations.

Usage:
    python manage.py seed_demo_specs          # dry-run
    python manage.py seed_demo_specs --apply  # write to DB
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from app.Estimator.models import (
    SystemLabourCrew as LabourCrew,
)
from app.Estimator.models import (
    SystemLabourSpecification as LabourSpecification,
)
from app.Estimator.models import (
    SystemMaterial as Material,
)
from app.Estimator.models import (
    SystemSpecification as Specification,
)
from app.Estimator.models import (
    SystemSpecificationComponent as SpecificationComponent,
)
from app.Estimator.models import (
    SystemTradeCode as TradeCode,
)


def _mat(code):
    """Look up a material by code prefix (case-insensitive partial match)."""
    return Material.objects.filter(material_code__icontains=code).first()


def _tc(prefix):
    return TradeCode.objects.filter(prefix=prefix).first()


def _crew(name_fragment):
    return LabourCrew.objects.filter(crew_type__icontains=name_fragment).first()


# ── Specification definitions ───────────────────────────────────────
# Each entry: (section, trade_prefix, name, unit, components)
#   components: list of (material_code_fragment, qty_per_unit)

MATERIAL_SPECS = [
    # ── Roofing (ROF) ──────────────────────────────────────────
    (
        "Section 1",
        "ROF-",
        "Roof Sheeting - IBR 0.5mm",
        "m2",
        [
            ("SKN-COR762", Decimal("1.10")),
            ("FIX-BOL-M12", Decimal("0.15")),
        ],
    ),
    (
        "Section 1",
        "ROF-",
        "Roof Sheeting - Corrugated 0.5mm",
        "m2",
        [
            ("SKN-COR762", Decimal("1.10")),
            ("FIX-BOL-M12", Decimal("0.10")),
        ],
    ),
    (
        "Section 1",
        "ROF-",
        "Roof Insulation - 135mm",
        "m2",
        [
            ("ACC-INS", Decimal("1.05")),
        ],
    ),
    (
        "Section 1",
        "ROF-",
        "Ridge Capping",
        "Lm",
        [
            ("ACC-RIDG", Decimal("1.05")),
            ("FIX-BOL-M12", Decimal("0.10")),
        ],
    ),
    (
        "Section 1",
        "ROF-",
        "Roof Flashing - Aluminium",
        "Lm",
        [
            ("FLA-AL", Decimal("1.10")),
        ],
    ),
    # ── Carpentry & Joinery (CRJ) ─────────────────────────────
    (
        "Section 1",
        "CRJ-",
        "Timber Roof Truss",
        "Each",
        [
            ("TIM-TRS-W", Decimal("1.00")),
        ],
    ),
    (
        "Section 1",
        "CRJ-",
        "Timber Battens - 38x38mm",
        "Lm",
        [
            ("TIM-BAT-FLR", Decimal("1.05")),
            ("Nails - 100mm", Decimal("0.01")),
        ],
    ),
    (
        "Section 1",
        "CRJ-",
        "Timber Fascia Board",
        "Lm",
        [
            ("TIM-FAS-FIB", Decimal("1.05")),
            ("Nails - 75mm", Decimal("0.02")),
        ],
    ),
    (
        "Section 1",
        "CRJ-",
        "Door Frame - Hardwood",
        "Each",
        [
            ("DR-FRM-MER", Decimal("1.00")),
        ],
    ),
    (
        "Section 1",
        "CRJ-",
        "Hollow Core Door",
        "Each",
        [
            ("DR-HLO-INT", Decimal("1.00")),
        ],
    ),
    # ── Ceilings & Partitions (CPA) ───────────────────────────
    (
        "Section 1",
        "CPA-",
        "Gypsum Ceiling Board - 9.5mm",
        "m2",
        [
            ("CEL-GYP-9.5", Decimal("1.10")),
            ("CEL-JNT-CMP", Decimal("0.30")),
        ],
    ),
    (
        "Section 1",
        "CPA-",
        "Gypsum Ceiling Board - 12.5mm",
        "m2",
        [
            ("CEL-FR-12.5", Decimal("1.10")),
            ("CEL-JNT-CMP", Decimal("0.30")),
        ],
    ),
    (
        "Section 1",
        "CPA-",
        "Suspended Ceiling Grid",
        "m2",
        [
            ("GRID-MAIN-3.6", Decimal("0.85")),
            ("GRID-CRSS-1.2", Decimal("1.70")),
        ],
    ),
    (
        "Section 1",
        "CPA-",
        "Dry Wall Partition - 100mm",
        "m2",
        [
            ("PAR-STUD-64", Decimal("3.00")),
            ("PAR-BRD-MOIS", Decimal("2.20")),
            ("PAR-INS-RW", Decimal("1.05")),
        ],
    ),
    # ── Structural Steelwork (STW) ────────────────────────────
    (
        "Section 1",
        "STW-",
        "Steel Angles",
        "kg",
        [
            ("S-ANG", Decimal("1.05")),
        ],
    ),
    (
        "Section 1",
        "STW-",
        "Steel Channels",
        "kg",
        [
            ("S-CHN", Decimal("1.05")),
        ],
    ),
    (
        "Section 1",
        "STW-",
        "Steel IPE Beams",
        "kg",
        [
            ("S-IPE", Decimal("1.05")),
        ],
    ),
    # ── Metalwork (MTW) ──────────────────────────────────────
    (
        "Section 1",
        "MTW-",
        "Steel Door Frame",
        "Each",
        [
            ("MS-FLT", Decimal("15.00")),
            ("FIN-GAL-HOT", Decimal("1.00")),
        ],
    ),
    (
        "Section 1",
        "MTW-",
        "Steel Window Frame",
        "Each",
        [
            ("MS-ANG", Decimal("12.00")),
            ("FIN-PDR", Decimal("1.00")),
        ],
    ),
    (
        "Section 1",
        "MTW-",
        "Burglar Bars",
        "m2",
        [
            ("MS-ANG", Decimal("6.00")),
            ("FIN-GAL", Decimal("1.00")),
        ],
    ),
    (
        "Section 1",
        "MTW-",
        "Balustrade - Mild Steel",
        "Lm",
        [
            ("STR-BAL-PIN", Decimal("1.00")),
            ("FIN-GAL-HOT", Decimal("1.00")),
        ],
    ),
    # ── Floor Coverings (FLR) ────────────────────────────────
    (
        "Section 1",
        "FLR-",
        "Ceramic Floor Tiles - 300x300",
        "m2",
        [
            ("CER-FLR", Decimal("1.10")),
            ("ADH-CER-STD", Decimal("0.25")),
            ("GRT-FLR-GRY", Decimal("0.15")),
        ],
    ),
    (
        "Section 1",
        "FLR-",
        "Porcelain Floor Tiles - 600x600",
        "m2",
        [
            ("POR-MAT", Decimal("1.10")),
            ("ADH-CER-STD", Decimal("0.30")),
            ("GRT-FLR-GRY", Decimal("0.15")),
        ],
    ),
    (
        "Section 1",
        "FLR-",
        "Vinyl Sheet Flooring",
        "m2",
        [
            ("VIN-SHT", Decimal("1.10")),
            ("ADH-BND-LIQ", Decimal("0.20")),
        ],
    ),
    (
        "Section 1",
        "FLR-",
        "Carpet Tiles",
        "m2",
        [
            ("CPT-TILE-C", Decimal("1.10")),
            ("CPT-UND-PRM", Decimal("1.10")),
        ],
    ),
    # ── Plastering (PLA) ─────────────────────────────────────
    (
        "Section 1",
        "PLA-",
        "Plaster Coat - 12mm Internal",
        "m2",
        [
            ("PLR-MIX-PRE", Decimal("0.50")),
            ("Building Sand", Decimal("0.02")),
        ],
    ),
    (
        "Section 1",
        "PLA-",
        "Plaster Coat - 15mm External",
        "m2",
        [
            ("PLR-MIX-PRE", Decimal("0.65")),
            ("Building Sand", Decimal("0.03")),
        ],
    ),
    (
        "Section 1",
        "PLA-",
        "Plaster Screed - 40mm",
        "m2",
        [
            ("GYP-CRT-40", Decimal("1.05")),
            ("Building Sand", Decimal("0.05")),
        ],
    ),
    # ── Plumbing & Drainage (PLD) ────────────────────────────
    (
        "Section 1",
        "PLD-",
        "PVC Waste Pipe - 50mm",
        "Lm",
        [
            ("PIP-HDPE-50", Decimal("1.10")),
            ("PIP-FIX-BKT", Decimal("0.50")),
        ],
    ),
    (
        "Section 1",
        "PLD-",
        "Copper Pipe - 15mm",
        "Lm",
        [
            ("PIP-COP-15", Decimal("1.10")),
            ("PIP-FIX-BKT", Decimal("0.50")),
        ],
    ),
    (
        "Section 1",
        "PLD-",
        "Wash Basin - Pedestal",
        "Each",
        [
            ("SAN-BAS-PED", Decimal("1.00")),
        ],
    ),
    (
        "Section 1",
        "PLD-",
        "Geyser - 150L",
        "Each",
        [
            ("SAN-GEY-150", Decimal("1.00")),
        ],
    ),
    # ── Glazing (GLZ) ───────────────────────────────────────
    (
        "Section 1",
        "GLZ-",
        "Float Glass - 4mm",
        "m2",
        [
            ("TSG-4MM", Decimal("1.05")),
            ("SIL-300", Decimal("0.40")),
        ],
    ),
    (
        "Section 1",
        "GLZ-",
        "Float Glass - 6mm",
        "m2",
        [
            ("TSG-6MM", Decimal("1.05")),
            ("SIL-300", Decimal("0.40")),
        ],
    ),
    (
        "Section 1",
        "GLZ-",
        "Laminated Safety Glass - 6.38mm",
        "m2",
        [
            ("LAM-6.38", Decimal("1.05")),
            ("SIL-300", Decimal("0.40")),
        ],
    ),
    (
        "Section 1",
        "GLZ-",
        "Aluminium Window - Standard",
        "m2",
        [
            ("ALU-SF-STD", Decimal("1.00")),
        ],
    ),
    # ── Ironmongery (IRM) ───────────────────────────────────
    (
        "Section 1",
        "IRM-",
        "Butt Hinges - 100mm",
        "Pair",
        [
            ("HNG-BUTT", Decimal("1.00")),
        ],
    ),
    (
        "Section 1",
        "IRM-",
        "Cylinder Lock - 3 Lever",
        "Each",
        [
            ("LCK-CYL-3L", Decimal("1.00")),
        ],
    ),
    (
        "Section 1",
        "IRM-",
        "Lever Handle Set",
        "Each",
        [
            ("HND-LEV", Decimal("1.00")),
        ],
    ),
    (
        "Section 1",
        "IRM-",
        "Door Closer - Hydraulic",
        "Each",
        [
            ("DR-ARC-MER", Decimal("1.00")),
        ],
    ),
    # ── Paintwork (PAW) ─────────────────────────────────────
    (
        "Section 1",
        "PAW-",
        "PVA Internal Paint - 2 Coats",
        "m2",
        [
            ("PVA-INT", Decimal("0.30")),
            ("PRE-PRM", Decimal("0.15")),
        ],
    ),
    (
        "Section 1",
        "PAW-",
        "Acrylic External Paint - 2 Coats",
        "m2",
        [
            ("ACR-EXT", Decimal("0.35")),
            ("PRE-PRM", Decimal("0.15")),
        ],
    ),
    (
        "Section 1",
        "PAW-",
        "Enamel Paint on Metalwork",
        "m2",
        [
            ("ENM-GLS", Decimal("0.30")),
            ("PRM-MTL-ETC", Decimal("0.15")),
        ],
    ),
    (
        "Section 1",
        "PAW-",
        "Wood Varnish - 2 Coats",
        "m2",
        [
            ("VNS-CLR", Decimal("0.25")),
            ("SND-PLR-WSH", Decimal("0.05")),
        ],
    ),
    # ── Electrical (ELW) ────────────────────────────────────
    (
        "Section 1",
        "ELW-",
        "PVC Conduit - 20mm",
        "Lm",
        [
            ("CON-ACC-SAD", Decimal("0.50")),
            ("CON-BOX-42", Decimal("0.10")),
        ],
    ),
    (
        "Section 1",
        "ELW-",
        "Cable - 2.5mm Twin & Earth",
        "Lm",
        [
            ("CAB-S2.5", Decimal("1.10")),
        ],
    ),
    (
        "Section 1",
        "ELW-",
        "Distribution Board - 20A",
        "Each",
        [
            ("DB-BRK-20A", Decimal("1.00")),
        ],
    ),
    (
        "Section 1",
        "ELW-",
        "LED Light Fitting - 4ft",
        "Each",
        [
            ("LUM-LED-4FT", Decimal("1.00")),
        ],
    ),
    # ── Tiling (TIL) ────────────────────────────────────────
    (
        "Section 1",
        "TIL-",
        "Ceramic Wall Tiles - 200x300",
        "m2",
        [
            ("CER-WHL", Decimal("1.10")),
            ("ADH-CER-STD", Decimal("0.25")),
            ("GRT-FLR-GRY", Decimal("0.10")),
        ],
    ),
    # ── External Work (EXT) ─────────────────────────────────
    (
        "Section 1",
        "EXT-",
        "Concrete Paving - 50mm",
        "m2",
        [
            ("Paving - Concrete 50mm", Decimal("1.05")),
            ("Building Sand", Decimal("0.05")),
        ],
    ),
    (
        "Section 1",
        "EXT-",
        "Palisade Fencing - 1.8m",
        "Lm",
        [
            ("FEN-PAL-1.8", Decimal("1.00")),
        ],
    ),
    (
        "Section 1",
        "EXT-",
        "Kikuyu Grass",
        "m2",
        [
            ("LND-GRS-KIK", Decimal("1.10")),
            ("LND-FER-LAN", Decimal("0.10")),
        ],
    ),
    (
        "Section 1",
        "EXT-",
        "Concrete Kerbing - Fig 10",
        "Lm",
        [
            ("KERB-FIG10", Decimal("1.05")),
        ],
    ),
    # ── Precast Concrete (PRC) ──────────────────────────────
    (
        "Section 1",
        "PRC-",
        "Precast Lintels",
        "Lm",
        [
            ("Sill - Precast 175mm", Decimal("1.00")),
        ],
    ),
]

# ── Labour Specification definitions ─────────────────────────────────
# Each entry: (section, trade_name, name, unit, crew_fragment, daily_prod,
#              team_mix, site_factor, tools_factor, leadership_factor)

LABOUR_SPECS = [
    # ── Masonry (MAN) ─────────────────────────────────────────
    (
        "Section 1",
        "MAN-Masonry",
        "Brickwork - Half Brick",
        "m2",
        "Crew 1",
        Decimal("6.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "MAN-Masonry",
        "Brickwork - One Brick",
        "m2",
        "Crew 1",
        Decimal("4.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "MAN-Masonry",
        "Blockwork - 140mm",
        "m2",
        "Crew 1",
        Decimal("8.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "MAN-Masonry",
        "Blockwork - 90mm",
        "m2",
        "Crew 1",
        Decimal("10.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "MAN-Masonry",
        "Damp Proof Course",
        "Lm",
        "Crew 4",
        Decimal("40.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Roofing (ROF) ────────────────────────────────────────
    (
        "Section 1",
        "ROF-Roofing Coverings",
        "Roof Sheeting",
        "m2",
        "Crew 4",
        Decimal("25.00"),
        Decimal("1"),
        Decimal("0.9"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "ROF-Roofing Coverings",
        "Roof Insulation",
        "m2",
        "Crew 4",
        Decimal("40.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "ROF-Roofing Coverings",
        "Ridge & Flashing",
        "Lm",
        "Crew 4",
        Decimal("15.00"),
        Decimal("1"),
        Decimal("0.9"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Carpentry & Joinery (CRJ) ────────────────────────────
    (
        "Section 1",
        "CRJ-Carpentry and Joinery",
        "Roof Trusses",
        "Each",
        "Crew 5",
        Decimal("8.00"),
        Decimal("1"),
        Decimal("0.9"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "CRJ-Carpentry and Joinery",
        "Timber Battens",
        "Lm",
        "Crew 4",
        Decimal("60.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "CRJ-Carpentry and Joinery",
        "Door Hanging",
        "Each",
        "Crew 4",
        Decimal("4.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "CRJ-Carpentry and Joinery",
        "Door Frame Installation",
        "Each",
        "Crew 4",
        Decimal("6.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Ceilings & Partitions (CPA) ──────────────────────────
    (
        "Section 1",
        "CPA-Ceilings, Partitions & Access Flooring",
        "Ceiling Boarding",
        "m2",
        "Crew 4",
        Decimal("20.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "CPA-Ceilings, Partitions & Access Flooring",
        "Suspended Ceiling",
        "m2",
        "Crew 4",
        Decimal("15.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "CPA-Ceilings, Partitions & Access Flooring",
        "Dry Wall Partitions",
        "m2",
        "Crew 4",
        Decimal("12.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Structural Steelwork (STW) ───────────────────────────
    (
        "Section 1",
        "STW-Structural Steelwork",
        "Steel Erection",
        "kg",
        "Crew 5",
        Decimal("200.00"),
        Decimal("1"),
        Decimal("0.9"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "STW-Structural Steelwork",
        "Steel Connections",
        "Each",
        "Crew 5",
        Decimal("12.00"),
        Decimal("1"),
        Decimal("0.9"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Metalwork (MTW) ──────────────────────────────────────
    (
        "Section 1",
        "MTW-Metalwork",
        "Steel Frame Installation",
        "Each",
        "Crew 4",
        Decimal("6.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "MTW-Metalwork",
        "Burglar Bar Installation",
        "m2",
        "Crew 4",
        Decimal("8.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "MTW-Metalwork",
        "Balustrade Installation",
        "Lm",
        "Crew 4",
        Decimal("6.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Floor Coverings (FLR) ────────────────────────────────
    (
        "Section 1",
        "FLR-Floor Coverings, Wall Linings, Etc",
        "Floor Tiling",
        "m2",
        "Crew 4",
        Decimal("12.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "FLR-Floor Coverings, Wall Linings, Etc",
        "Vinyl Flooring",
        "m2",
        "Crew 4",
        Decimal("25.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "FLR-Floor Coverings, Wall Linings, Etc",
        "Carpet Laying",
        "m2",
        "Crew 4",
        Decimal("30.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Plastering (PLA) ─────────────────────────────────────
    (
        "Section 1",
        "PLA-Plastering",
        "Internal Plastering",
        "m2",
        "Crew 1",
        Decimal("10.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "PLA-Plastering",
        "External Plastering",
        "m2",
        "Crew 1",
        Decimal("8.00"),
        Decimal("1"),
        Decimal("0.9"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "PLA-Plastering",
        "Floor Screeding",
        "m2",
        "Crew 1",
        Decimal("15.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Plumbing & Drainage (PLD) ────────────────────────────
    (
        "Section 1",
        "PLD-Plumbing & Drainage",
        "Pipe Installation",
        "Lm",
        "Crew 4",
        Decimal("15.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "PLD-Plumbing & Drainage",
        "Sanitary Fittings",
        "Each",
        "Crew 4",
        Decimal("4.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "PLD-Plumbing & Drainage",
        "Geyser Installation",
        "Each",
        "Crew 4",
        Decimal("2.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Glazing (GLZ) ───────────────────────────────────────
    (
        "Section 1",
        "GLZ-Glazing",
        "Glass Installation",
        "m2",
        "Crew 4",
        Decimal("10.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "GLZ-Glazing",
        "Aluminium Window Fitting",
        "m2",
        "Crew 4",
        Decimal("6.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Ironmongery (IRM) ───────────────────────────────────
    (
        "Section 1",
        "IRM-Ironmongery",
        "Ironmongery Fitting",
        "Each",
        "Crew 4",
        Decimal("16.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Paintwork (PAW) ─────────────────────────────────────
    (
        "Section 1",
        "PAW-Paintwork",
        "Internal Painting",
        "m2",
        "Crew 4",
        Decimal("30.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "PAW-Paintwork",
        "External Painting",
        "m2",
        "Crew 4",
        Decimal("25.00"),
        Decimal("1"),
        Decimal("0.9"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "PAW-Paintwork",
        "Metalwork Painting",
        "m2",
        "Crew 4",
        Decimal("15.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "PAW-Paintwork",
        "Timber Varnishing",
        "m2",
        "Crew 4",
        Decimal("20.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Electrical (ELW) ────────────────────────────────────
    (
        "Section 1",
        "ELW-Electrical Work",
        "Conduit Installation",
        "Lm",
        "Crew 4",
        Decimal("25.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "ELW-Electrical Work",
        "Cable Installation",
        "Lm",
        "Crew 4",
        Decimal("40.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "ELW-Electrical Work",
        "Light Fitting Installation",
        "Each",
        "Crew 4",
        Decimal("8.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "ELW-Electrical Work",
        "DB Board Installation",
        "Each",
        "Crew 4",
        Decimal("2.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Tiling (TIL) ────────────────────────────────────────
    (
        "Section 1",
        "TIL-Tiling",
        "Wall Tiling",
        "m2",
        "Crew 4",
        Decimal("10.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Waterproofing (WPR) ─────────────────────────────────
    (
        "Section 1",
        "WPR-Waterproofing",
        "Waterproofing Membrane",
        "m2",
        "Crew 4",
        Decimal("20.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "WPR-Waterproofing",
        "DPC Installation",
        "Lm",
        "Crew 4",
        Decimal("40.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── External Work (EXT) ─────────────────────────────────
    (
        "Section 1",
        "EXT-External Work",
        "Paving",
        "m2",
        "Crew 1",
        Decimal("15.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "EXT-External Work",
        "Fencing",
        "Lm",
        "Crew 4",
        Decimal("10.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "EXT-External Work",
        "Landscaping",
        "m2",
        "Crew 3",
        Decimal("50.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    (
        "Section 1",
        "EXT-External Work",
        "Kerbing",
        "Lm",
        "Crew 1",
        Decimal("12.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
    # ── Precast Concrete (PRC) ──────────────────────────────
    (
        "Section 1",
        "PRC-Precast Concrete",
        "Precast Element Installation",
        "Lm",
        "Crew 5",
        Decimal("15.00"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
        Decimal("1"),
    ),
]


class Command(BaseCommand):
    help = "Seed material and labour specifications for all trades"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write to DB (default is dry-run)",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        if not apply:
            self.stdout.write(self.style.WARNING("DRY-RUN — use --apply to save\n"))

        mat_created = 0
        mat_skipped = 0
        for section, trade_prefix, name, unit, components in MATERIAL_SPECS:
            exists = Specification.objects.filter(name=name).exists()
            if exists:
                mat_skipped += 1
                continue

            tc = _tc(trade_prefix)
            if apply:
                spec = Specification.objects.create(
                    section=section,
                    trade_code=tc,
                    unit_label=unit,
                    name=name,
                )
                for i, (mat_code, qty) in enumerate(components):
                    mat = _mat(mat_code)
                    SpecificationComponent.objects.create(
                        specification=spec,
                        material=mat,
                        label=mat_code,
                        qty_per_unit=qty,
                        sort_order=i,
                    )
                    if not mat:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  Material not found for "{mat_code}" in spec "{name}"'
                            )
                        )

            mat_created += 1
            self.stdout.write(f"  + Mat Spec: {name} ({trade_prefix})")

        self.stdout.write(
            f"\nMaterial Specs: {mat_created} created, {mat_skipped} skipped (exist)"
        )

        lab_created = 0
        lab_skipped = 0
        for (
            section,
            trade_name,
            name,
            unit,
            crew_frag,
            daily_prod,
            team_mix,
            site_f,
            tools_f,
            lead_f,
        ) in LABOUR_SPECS:
            exists = LabourSpecification.objects.filter(
                name=name, trade_name=trade_name
            ).exists()
            if exists:
                lab_skipped += 1
                continue

            crew = _crew(crew_frag)
            if apply:
                LabourSpecification.objects.create(
                    section=section,
                    trade_name=trade_name,
                    name=name,
                    unit=unit,
                    crew=crew,
                    daily_production=daily_prod,
                    team_mix=team_mix,
                    site_factor=site_f,
                    tools_factor=tools_f,
                    leadership_factor=lead_f,
                )

            lab_created += 1
            self.stdout.write(f"  + Lab Spec: {name} ({trade_name})")

        self.stdout.write(
            f"\nLabour Specs: {lab_created} created, {lab_skipped} skipped (exist)"
        )

        if apply:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nDone. Run auto_populate_fks --apply to link BoQ items."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING("\nDry-run complete. Use --apply to save.")
            )
