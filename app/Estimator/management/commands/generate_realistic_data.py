"""
Generate realistic demo data for a South African school construction project.

Wipes ALL existing data and creates a complete, internally-consistent dataset
with 2024/2025 SA pricing for the Lephadimisha School Complex.

Usage:
    python manage.py generate_realistic_data --confirm
"""

import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from app.Estimator.models import (
    BOQItem,
)
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

D = Decimal
random.seed(42)  # Reproducible results


# ═══════════════════════════════════════════════════════════════════════
# TRADE CODES
# ═══════════════════════════════════════════════════════════════════════

TRADE_CODES = [
    ('PRE-', 'Preliminaries & General'),
    ('EAR-', 'Earthworks'),
    ('CFR-', 'Concrete, Formwork & Reinforcement'),
    ('MAN-', 'Masonry'),
    ('WPR-', 'Waterproofing'),
    ('ROF-', 'Roofing Coverings'),
    ('CRJ-', 'Carpentry and Joinery'),
    ('CPA-', 'Ceilings, Partitions & Access Flooring'),
    ('FLR-', 'Floor Coverings, Wall Linings, Etc'),
    ('IRM-', 'Ironmongery'),
    ('STW-', 'Structural Steelwork'),
    ('MTW-', 'Metalwork'),
    ('PLA-', 'Plastering'),
    ('PLD-', 'Plumbing & Drainage'),
    ('GLZ-', 'Glazing'),
    ('PAW-', 'Paintwork'),
    ('ELW-', 'Electrical Work'),
    ('PRC-', 'Provisional Sums'),
]


# ═══════════════════════════════════════════════════════════════════════
# MATERIALS  (code, trade_name, unit, market_rate, variety, spec)
# ═══════════════════════════════════════════════════════════════════════

MATERIALS = [
    # Earthworks
    ('EAR-TOPSOL', 'Earthworks', 'm3', 45, 'Topsoil removal', 'Stripped 150mm'),
    ('EAR-EXCV-S', 'Earthworks', 'm3', 85, 'Soft excavation', 'Manual'),
    ('EAR-EXCV-I', 'Earthworks', 'm3', 165, 'Intermediate excavation', 'Mechanical'),
    ('EAR-EXCV-H', 'Earthworks', 'm3', 320, 'Hard rock excavation', 'Breaking'),
    ('EAR-BKFIL', 'Earthworks', 'm3', 55, 'Selected backfill', 'Compacted G5'),
    ('EAR-DISP', 'Earthworks', 'm3', 95, 'Dispose surplus', 'Licensed tip'),

    # Concrete
    ('CON-10MPA', 'Concrete', 'm3', 1450, 'Readymix 10MPa', '19mm stone'),
    ('CON-15MPA', 'Concrete', 'm3', 1580, 'Readymix 15MPa', '19mm stone'),
    ('CON-20MPA', 'Concrete', 'm3', 1750, 'Readymix 20MPa', '19mm stone'),
    ('CON-25MPA', 'Concrete', 'm3', 1950, 'Readymix 25MPa', '19mm stone'),
    ('CON-30MPA', 'Concrete', 'm3', 2150, 'Readymix 30MPa', '19mm stone'),
    ('CFR-MESH395', 'Concrete', 'm2', 48.50, 'Welded mesh Ref 395', '5.6mm wire'),
    ('CFR-MESH245', 'Concrete', 'm2', 35, 'Welded mesh Ref 245', '4.5mm wire'),
    ('CFR-REBAR-Y12', 'Concrete', 't', 14500, 'Rebar Y12 high tensile', 'SABS 920'),
    ('CFR-REBAR-R8', 'Concrete', 't', 13800, 'Rebar R8 mild steel', 'SABS 920'),
    ('CFR-SHTBD-18', 'Formwork', 'm2', 185, 'Shutterboard 18mm', 'SA Pine'),
    ('CFR-PROPS', 'Formwork', 'each', 45, 'Adjustable prop', '3.6m steel'),
    ('CFR-TRNPC', 'Formwork', 'm', 32, 'Turning piece', 'Timber 228mm'),

    # Masonry
    ('MAN-BRK-NFP', 'Masonry', 'each', 4.50, 'NFP brick Class II', 'Stock 222x106x73'),
    ('MAN-BRK-FACE', 'Masonry', 'each', 7.80, 'Face brick', 'Corobrik Satin'),
    ('MAN-BRK-MAXI', 'Masonry', 'each', 6.80, 'Maxi brick Class II', '290x140x90'),
    ('MAN-BLK-M140', 'Masonry', 'each', 14.50, 'Concrete block 140mm', '7MPa'),
    ('MAN-CEM-50KG', 'Masonry', 'bag', 120, 'OPC Cement 50kg', 'CEM II 42.5N'),
    ('MAN-SAND-BLD', 'Masonry', 'm3', 380, 'Building sand washed', 'Plaster grade'),
    ('MAN-DPC-375', 'Masonry', 'm2', 28, 'DPC membrane 375um', 'Polyethylene'),
    ('MAN-DPC-150', 'Masonry', 'm', 18.50, 'DPC strip 150mm', 'Embossed Brikgrip'),
    ('MAN-LNTL-PC', 'Masonry', 'm', 125, 'Precast concrete lintel', '110x75mm'),

    # Waterproofing
    ('WPR-TORCH', 'Waterproofing', 'm2', 95, 'Torch-on membrane 4mm', 'Modified bitumen'),
    ('WPR-BTPRM', 'Waterproofing', 'm2', 22, 'Bitumen primer', 'Solvent-based'),
    ('WPR-DPM-250', 'Waterproofing', 'm2', 15, 'DPM 250 micron', 'Polyethylene'),

    # Roofing
    ('SKN-IBR580', 'Roofing', 'm2', 165, 'IBR 0.5mm Chromadek', '580mm cover'),
    ('ACC-RIDG', 'Roofing', 'm', 85, 'Ridge capping galv', 'Standard profile'),
    ('ACC-INS', 'Roofing', 'm2', 65, 'Insulation 135mm', 'Isotherm/Aerolite'),
    ('ACC-FLASH', 'Roofing', 'm', 55, 'Aluminium flashing', '0.6mm'),
    ('FIX-TEK-SCR', 'Roofing', 'each', 3.50, 'Tek screw + washer', 'Self-drilling'),

    # Carpentry & Joinery
    ('TIM-TRS-W', 'Carpentry', 'each', 1850, 'Timber roof truss', 'SA Pine 8m span'),
    ('TIM-BAT-38', 'Carpentry', 'm', 22, 'Battens 38x38mm', 'SA Pine S5'),
    ('TIM-FAS-FIB', 'Carpentry', 'm', 125, 'Fibre cement fascia', '225x6mm FC77'),
    ('DR-FRM-MER', 'Carpentry', 'each', 1250, 'Door frame meranti', '813x2032'),
    ('DR-HLO-INT', 'Carpentry', 'each', 850, 'Hollow core door', '813x2032x40'),
    ('DR-SLD-EXT', 'Carpentry', 'each', 2450, 'Solid timber door', 'Meranti external'),

    # Ceilings
    ('CEL-GYP-9.5', 'Ceilings', 'm2', 68, 'Gypsum board 9.5mm', 'Gyproc standard'),
    ('CEL-JNT-CMP', 'Ceilings', 'm2', 18, 'Jointing compound', '5kg per 10m2'),
    ('CEL-BRANCH', 'Ceilings', 'm', 28, 'Brandering 38x38', 'SA Pine S5'),
    ('CEL-COR-75', 'Ceilings', 'm', 35, 'Coved cornice 75mm', 'Gypsum'),

    # Floor Coverings
    ('CER-FLR-300', 'Floor Coverings', 'm2', 185, 'Ceramic tile 300x300', 'Grade A'),
    ('POR-FLR-600', 'Floor Coverings', 'm2', 285, 'Porcelain tile 600x600', 'Matt finish'),
    ('VIN-SHT-2MM', 'Floor Coverings', 'm2', 145, 'Vinyl sheet 2mm', 'FloorworX'),
    ('ADH-CER-STD', 'Floor Coverings', 'm2', 45, 'Tile adhesive std', '20kg bag'),
    ('GRT-FLR-GRY', 'Floor Coverings', 'm2', 22, 'Floor grout grey', '5kg bag'),

    # Plastering
    ('PLR-MIX-PRE', 'Plastering', 'bag', 95, 'Pre-mixed plaster 40kg', 'Standard'),
    ('ACC-SCR-LEV', 'Plastering', 'm2', 42, 'Screed levelling', 'Self-levelling'),
    ('COR-COVE-75', 'Plastering', 'm', 35, 'Coved cornice 75mm', 'Gypsum'),

    # Plumbing & Drainage
    ('PIP-PVC-50', 'Plumbing', 'm', 48, 'PVC waste pipe 50mm', 'SABS Class 34'),
    ('PIP-PVC-110', 'Plumbing', 'm', 85, 'PVC soil pipe 110mm', 'SABS Class 34'),
    ('PIP-COP-15', 'Plumbing', 'm', 95, 'Copper pipe 15mm', 'Type B SABS'),
    ('RWD-GUT-PVC', 'Plumbing', 'm', 78, 'PVC gutter 125mm', 'Marley'),
    ('RWD-DP-75', 'Plumbing', 'm', 65, 'PVC downpipe 75mm', 'Marley'),
    ('SAN-BAS-PED', 'Plumbing', 'each', 1850, 'Pedestal basin white', 'Vitreous china'),
    ('SAN-WC-CC', 'Plumbing', 'each', 2450, 'Close-coupled WC', 'Vitreous china'),
    ('SAN-TAP-MIX', 'Plumbing', 'each', 650, 'Basin mixer tap', 'Chrome'),

    # Glazing
    ('ALU-WIN-CSM', 'Glazing', 'each', 2800, 'Aluminium casement', '1200x1200 bronze'),
    ('ALU-WIN-SLD', 'Glazing', 'each', 3200, 'Aluminium sliding', '1800x1200 bronze'),
    ('ALU-SF-GLZ', 'Glazing', 'm2', 450, 'Laminated safety glass', '6.38mm clear'),

    # Ironmongery
    ('HRD-HNG-100', 'Ironmongery', 'pair', 85, 'Butt hinge 100mm', 'Brass'),
    ('HRD-LCK-3LV', 'Ironmongery', 'each', 285, '3-lever mortice lock', 'Chrome'),
    ('HRD-HND-LVR', 'Ironmongery', 'each', 195, 'Lever handle set', 'Chrome on brass'),
    ('HRD-CLO-HYD', 'Ironmongery', 'each', 450, 'Hydraulic door closer', 'Samson 8800'),

    # Structural Steelwork
    ('STL-IPE-200', 'Steelwork', 'kg', 18.50, 'IPE 200 beam', 'Grade 300W'),
    ('STL-ANG-65', 'Steelwork', 'kg', 16.80, 'Angle 65x65x6', 'Grade 300W'),
    ('STL-GALV', 'Steelwork', 'kg', 8.50, 'Hot-dip galvanising', 'SANS 121'),

    # Metalwork
    ('MTW-FRM-STL', 'Metalwork', 'each', 1450, 'Pressed steel door frame', '1.2mm rebated'),
    ('MTW-WIN-STL', 'Metalwork', 'each', 1850, 'Steel window frame', 'Galvanised'),
    ('MTW-SEC-GATE', 'Metalwork', 'each', 3200, 'Security gate', 'Xpanda type'),

    # Paintwork
    ('PVA-INT', 'Paintwork', 'L', 45, 'PVA interior Plascon', '20L'),
    ('ACR-EXT', 'Paintwork', 'L', 55, 'Acrylic exterior Dulux', '20L'),
    ('ENM-GLS', 'Paintwork', 'L', 75, 'Enamel gloss', '5L'),
    ('PRE-PRM', 'Paintwork', 'L', 38, 'Plaster primer alkali', '20L'),

    # Electrical
    ('CON-PVC-20', 'Electrical', 'm', 12.50, 'PVC conduit 20mm', 'Heavy gauge'),
    ('CAB-S2.5', 'Electrical', 'm', 18.50, 'Cable 2.5mm T&E', 'Surfix'),
    ('CAB-S4.0', 'Electrical', 'm', 28, 'Cable 4.0mm T&E', 'Surfix'),
    ('CAB-ECC-16', 'Electrical', 'm', 32, 'Earth conductor 16mm', 'Bare copper'),
    ('FIT-SWI-1L', 'Electrical', 'each', 85, 'Light switch 1-lever', 'Crabtree'),
    ('FIT-SOC-DBL', 'Electrical', 'each', 125, 'Double socket outlet', 'Crabtree'),
    ('FIT-LED-4FT', 'Electrical', 'each', 385, 'LED fitting 4ft', '2x18W'),
    ('DB-BRK-12W', 'Electrical', 'each', 2850, 'Distribution board 12-way', 'Pre-wired'),
]


# ═══════════════════════════════════════════════════════════════════════
# LABOUR CREWS  (type, size, skilled, semi, general, s_rate, ss_rate, g_rate)
# ═══════════════════════════════════════════════════════════════════════

LABOUR_CREWS = [
    ('Concrete Crew', 6, 1, 2, 3, 550, 380, 280),      # daily=2150
    ('Masonry Crew', 5, 1, 1, 3, 580, 400, 280),        # daily=1820
    ('General Labour', 4, 0, 1, 3, 0, 350, 280),         # daily=1190
    ('Finishing Crew', 4, 1, 1, 2, 520, 380, 280),       # daily=1460
    ('Roofing Crew', 5, 2, 1, 2, 600, 400, 280),         # daily=2160
    ('Electrical Crew', 3, 1, 1, 1, 650, 420, 280),      # daily=1350
    ('Plumbing Crew', 3, 1, 1, 1, 620, 400, 280),        # daily=1300
]


# ═══════════════════════════════════════════════════════════════════════
# SPECIFICATION TEMPLATES  (name, trade_prefix, unit, components)
#   component = (material_code, label, qty_per_unit)
# ═══════════════════════════════════════════════════════════════════════

SPEC_TEMPLATES = [
    # Concrete
    ('15MPa', 'CFR-', 'm3', [('CON-15MPA', 'Readymix 15MPa', D('1.05'))]),
    ('25MPa', 'CFR-', 'm3', [('CON-25MPA', 'Readymix 25MPa', D('1.05'))]),
    ('30MPa', 'CFR-', 'm3', [('CON-30MPA', 'Readymix 30MPa', D('1.05'))]),
    ('Mesh Reinforcement - Ref 395', 'CFR-', 'm2', [
        ('CFR-MESH395', 'Welded mesh Ref 395', D('1.10')),
    ]),
    ('Rebar - High Tensile Y12', 'CFR-', 't', [
        ('CFR-REBAR-Y12', 'Rebar Y12', D('1.05')),
    ]),
    ('Rough Formwork - 18mm', 'CFR-', 'm2', [
        ('CFR-SHTBD-18', 'Shutterboard 18mm', D('1.15')),
        ('CFR-PROPS', 'Adjustable props', D('0.50')),
    ]),

    # Masonry
    ('Half Brick Wall - Class II', 'MAN-', 'm2', [
        ('MAN-BRK-NFP', 'NFP bricks', D('55')),
        ('MAN-CEM-50KG', 'Cement 50kg', D('0.25')),
        ('MAN-SAND-BLD', 'Building sand', D('0.020')),
    ]),
    ('One Brick Wall - Class II', 'MAN-', 'm2', [
        ('MAN-BRK-NFP', 'NFP bricks', D('110')),
        ('MAN-CEM-50KG', 'Cement 50kg', D('0.50')),
        ('MAN-SAND-BLD', 'Building sand', D('0.040')),
    ]),
    ('Face Brick Wall', 'MAN-', 'm2', [
        ('MAN-BRK-FACE', 'Face bricks', D('55')),
        ('MAN-CEM-50KG', 'Cement 50kg', D('0.25')),
        ('MAN-SAND-BLD', 'Building sand', D('0.020')),
    ]),
    ('Precast Lintels', 'MAN-', 'm', [
        ('MAN-LNTL-PC', 'Precast lintel', D('1.05')),
    ]),
    ('DPC in Walls', 'MAN-', 'm', [
        ('MAN-DPC-150', 'DPC strip 150mm', D('1.10')),
    ]),
    ('DPM Under Slabs', 'MAN-', 'm2', [
        ('MAN-DPC-375', 'DPC membrane 375um', D('1.10')),
    ]),

    # Waterproofing
    ('Waterproofing Membrane', 'WPR-', 'm2', [
        ('WPR-TORCH', 'Torch-on membrane', D('1.10')),
        ('WPR-BTPRM', 'Bitumen primer', D('1.05')),
    ]),
    ('DPM 250 Micron', 'WPR-', 'm2', [
        ('WPR-DPM-250', 'DPM polyethylene', D('1.10')),
    ]),

    # Roofing
    ('IBR Roof Sheeting', 'ROF-', 'm2', [
        ('SKN-IBR580', 'IBR 0.5mm Chromadek', D('1.10')),
        ('FIX-TEK-SCR', 'Tek screws', D('8')),
    ]),
    ('Roof Insulation 135mm', 'ROF-', 'm2', [
        ('ACC-INS', 'Insulation 135mm', D('1.05')),
    ]),
    ('Ridge Capping', 'ROF-', 'm', [
        ('ACC-RIDG', 'Ridge capping galv', D('1.05')),
        ('FIX-TEK-SCR', 'Tek screws', D('4')),
    ]),

    # Carpentry & Joinery
    ('Timber Roof Truss', 'CRJ-', 'each', [
        ('TIM-TRS-W', 'Timber truss', D('1')),
    ]),
    ('Timber Battens 38x38', 'CRJ-', 'm', [
        ('TIM-BAT-38', 'Battens 38x38', D('1.10')),
    ]),
    ('Fibre Cement Fascia', 'CRJ-', 'm', [
        ('TIM-FAS-FIB', 'FC fascia board', D('1.05')),
    ]),
    ('Door Frame - Meranti', 'CRJ-', 'each', [
        ('DR-FRM-MER', 'Meranti frame', D('1')),
    ]),
    ('Hollow Core Door', 'CRJ-', 'each', [
        ('DR-HLO-INT', 'Hollow core door', D('1')),
    ]),

    # Ceilings
    ('Gypsum Ceiling 9.5mm', 'CPA-', 'm2', [
        ('CEL-GYP-9.5', 'Gypsum board', D('1.10')),
        ('CEL-JNT-CMP', 'Jointing compound', D('0.30')),
        ('CEL-BRANCH', 'Brandering', D('2.20')),
    ]),

    # Floor Coverings
    ('Ceramic Floor Tiles 300x300', 'FLR-', 'm2', [
        ('CER-FLR-300', 'Ceramic tiles', D('1.10')),
        ('ADH-CER-STD', 'Tile adhesive', D('1.05')),
        ('GRT-FLR-GRY', 'Floor grout', D('1.05')),
    ]),
    ('Vinyl Sheet Flooring', 'FLR-', 'm2', [
        ('VIN-SHT-2MM', 'Vinyl sheet 2mm', D('1.10')),
    ]),

    # Plastering
    ('Plaster Internal 12mm', 'PLA-', 'm2', [
        ('PLR-MIX-PRE', 'Pre-mixed plaster', D('0.50')),
        ('MAN-SAND-BLD', 'Building sand', D('0.020')),
    ]),
    ('Plaster External 15mm', 'PLA-', 'm2', [
        ('PLR-MIX-PRE', 'Pre-mixed plaster', D('0.65')),
        ('MAN-SAND-BLD', 'Building sand', D('0.030')),
    ]),
    ('Screed 40mm', 'PLA-', 'm2', [
        ('ACC-SCR-LEV', 'Screed levelling', D('1.10')),
    ]),

    # Plumbing
    ('PVC Waste Pipe 50mm', 'PLD-', 'm', [
        ('PIP-PVC-50', 'PVC pipe 50mm', D('1.10')),
    ]),
    ('PVC Gutter & Downpipe', 'PLD-', 'm', [
        ('RWD-GUT-PVC', 'PVC gutter', D('1.05')),
    ]),

    # Glazing
    ('Aluminium Casement Window', 'GLZ-', 'each', [
        ('ALU-WIN-CSM', 'Casement window', D('1')),
    ]),
    ('Aluminium Sliding Window', 'GLZ-', 'each', [
        ('ALU-WIN-SLD', 'Sliding window', D('1')),
    ]),

    # Paintwork
    ('PVA Internal 2 Coats', 'PAW-', 'm2', [
        ('PVA-INT', 'PVA interior', D('0.30')),
        ('PRE-PRM', 'Plaster primer', D('0.15')),
    ]),
    ('Acrylic External 2 Coats', 'PAW-', 'm2', [
        ('ACR-EXT', 'Acrylic exterior', D('0.35')),
        ('PRE-PRM', 'Plaster primer', D('0.15')),
    ]),
    ('Enamel on Metalwork', 'PAW-', 'm2', [
        ('ENM-GLS', 'Enamel gloss', D('0.20')),
        ('PRE-PRM', 'Primer', D('0.15')),
    ]),

    # Electrical
    ('PVC Conduit 20mm', 'ELW-', 'm', [
        ('CON-PVC-20', 'PVC conduit', D('1.10')),
    ]),
    ('Cable 2.5mm T&E', 'ELW-', 'm', [
        ('CAB-S2.5', 'Cable 2.5mm', D('1.10')),
    ]),
    ('LED Light Fitting', 'ELW-', 'each', [
        ('FIT-LED-4FT', 'LED 4ft fitting', D('1')),
    ]),
    ('Distribution Board', 'ELW-', 'each', [
        ('DB-BRK-12W', 'DB 12-way', D('1')),
    ]),

    # Ironmongery
    ('Butt Hinges 100mm', 'IRM-', 'pair', [
        ('HRD-HNG-100', 'Butt hinge', D('1')),
    ]),
    ('3-Lever Mortice Lock', 'IRM-', 'each', [
        ('HRD-LCK-3LV', '3-lever lock', D('1')),
    ]),
    ('Lever Handle Set', 'IRM-', 'each', [
        ('HRD-HND-LVR', 'Lever handles', D('1')),
    ]),
    ('Door Closer', 'IRM-', 'each', [
        ('HRD-CLO-HYD', 'Hydraulic closer', D('1')),
    ]),

    # Metalwork
    ('Pressed Steel Door Frame', 'MTW-', 'each', [
        ('MTW-FRM-STL', 'Steel frame', D('1')),
    ]),
    ('Steel Window Frame', 'MTW-', 'each', [
        ('MTW-WIN-STL', 'Steel window', D('1')),
    ]),

    # Structural Steelwork
    ('Structural Steel IPE', 'STW-', 'kg', [
        ('STL-IPE-200', 'IPE 200 beam', D('1.05')),
        ('STL-GALV', 'Hot-dip galvanising', D('1.05')),
    ]),
]


# ═══════════════════════════════════════════════════════════════════════
# LABOUR SPEC TEMPLATES  (name, trade_prefix, unit, crew_type, daily_prod)
# ═══════════════════════════════════════════════════════════════════════

LABOUR_TEMPLATES = [
    ('Site Preparation', 'EAR-', 'm2', 'General Labour', 40),
    ('Trench Excavation', 'EAR-', 'm3', 'General Labour', 4),
    ('Backfill & Compact', 'EAR-', 'm3', 'General Labour', 8),
    ('Concrete Placement', 'CFR-', 'm3', 'Concrete Crew', 6),
    ('Blinding Layer', 'CFR-', 'm3', 'Concrete Crew', 8),
    ('Formwork Erection', 'CFR-', 'm2', 'Concrete Crew', 12),
    ('Mesh Laying', 'CFR-', 'm2', 'Concrete Crew', 25),
    ('Rebar Fixing', 'CFR-', 't', 'Concrete Crew', 0.15),
    ('Brickwork - Half Brick', 'MAN-', 'm2', 'Masonry Crew', 12),
    ('Brickwork - One Brick', 'MAN-', 'm2', 'Masonry Crew', 8),
    ('DPC Installation', 'MAN-', 'm', 'Masonry Crew', 30),
    ('Waterproofing Membrane', 'WPR-', 'm2', 'Finishing Crew', 20),
    ('Roof Sheeting', 'ROF-', 'm2', 'Roofing Crew', 25),
    ('Roof Insulation', 'ROF-', 'm2', 'Roofing Crew', 35),
    ('Truss Erection', 'CRJ-', 'each', 'Roofing Crew', 6),
    ('Timber Battens', 'CRJ-', 'm', 'Roofing Crew', 60),
    ('Door Hanging', 'CRJ-', 'each', 'Finishing Crew', 4),
    ('Ceiling Boarding', 'CPA-', 'm2', 'Finishing Crew', 20),
    ('Floor Tiling', 'FLR-', 'm2', 'Finishing Crew', 12),
    ('Internal Plastering', 'PLA-', 'm2', 'Finishing Crew', 14),
    ('External Plastering', 'PLA-', 'm2', 'Finishing Crew', 12),
    ('Screeding', 'PLA-', 'm2', 'Finishing Crew', 18),
    ('Pipe Installation', 'PLD-', 'm', 'Plumbing Crew', 15),
    ('Sanitary Fittings', 'PLD-', 'each', 'Plumbing Crew', 3),
    ('Glass Installation', 'GLZ-', 'each', 'Finishing Crew', 6),
    ('Ironmongery Fitting', 'IRM-', 'each', 'Finishing Crew', 10),
    ('Internal Painting', 'PAW-', 'm2', 'Finishing Crew', 30),
    ('External Painting', 'PAW-', 'm2', 'Finishing Crew', 25),
    ('Enamel Painting', 'PAW-', 'm2', 'Finishing Crew', 15),
    ('Conduit Installation', 'ELW-', 'm', 'Electrical Crew', 25),
    ('Cable Pulling', 'ELW-', 'm', 'Electrical Crew', 40),
    ('Light Fitting Install', 'ELW-', 'each', 'Electrical Crew', 8),
    ('DB Board Installation', 'ELW-', 'each', 'Electrical Crew', 0.5),
    ('Steel Erection', 'STW-', 'kg', 'Concrete Crew', 150),
    ('Steel Frame Install', 'MTW-', 'each', 'Finishing Crew', 4),
    ('Demolition', 'EAR-', 'm3', 'General Labour', 3),
]


# ═══════════════════════════════════════════════════════════════════════
# SECTION DEFINITIONS  (bills per section and BOQ items)
# ═══════════════════════════════════════════════════════════════════════

SECTION_PROGRESS = {
    'Section 1 - Preliminaries': 1.00,
    'Section 2 - Media Centre': 0.75,
    'Section 3 - Admin Block': 0.55,
    'Section 4 - Kitchen Conversion': 0.40,
    'Section 5 - Classroom Refurbishment': 0.25,
    'Section 6 - Demolition': 0.95,
}

# Trade progress offset from section base (early trades ahead, late behind)
TRADE_PROGRESS_OFFSET = {
    'EAR-': 0.20,
    'CFR-': 0.15,
    'MAN-': 0.10,
    'WPR-': 0.05,
    'ROF-': 0.00,
    'CRJ-': 0.00,
    'STW-': 0.00,
    'MTW-': -0.05,
    'CPA-': -0.05,
    'FLR-': -0.10,
    'PLA-': -0.05,
    'PLD-': -0.05,
    'GLZ-': -0.10,
    'IRM-': -0.10,
    'PAW-': -0.15,
    'ELW-': -0.10,
    'PRC-': 0.00,
    'PRE-': 0.00,
}


def _build_section_items():
    """Return dict of section → list of (bill_name, trade_prefix, items)."""
    # Each item: (description, unit, qty, spec_name, labour_name, markup_pct)
    # spec_name=None and labour_name=None for prelims/provisional items

    sections = {}

    # ── Section 1: Preliminaries ──
    sections['Section 1 - Preliminaries'] = [
        ('Bill No. 1 - Preliminaries: Fixed Charges', 'PRE-', [
            ('Site establishment and mobilisation', 'sum', 1, None, None, 0),
            ('Site offices, stores and ablutions', 'sum', 1, None, None, 0),
            ('Temporary water supply and reticulation', 'sum', 1, None, None, 0),
            ('Temporary electrical supply', 'sum', 1, None, None, 0),
            ('Safety requirements, PPE and first aid', 'sum', 1, None, None, 0),
            ('Setting out the works', 'sum', 1, None, None, 0),
            ('Environmental management plan', 'sum', 1, None, None, 0),
        ]),
        ('Bill No. 2 - Preliminaries: Time Related', 'PRE-', [
            ('Site management (12 months)', 'month', 12, None, None, 0),
            ('Security services (12 months)', 'month', 12, None, None, 0),
            ('Temporary fencing and hoarding (12 months)', 'month', 12, None, None, 0),
            ('Plant and equipment (12 months)', 'month', 12, None, None, 0),
            ('Water and electricity charges (12 months)', 'month', 12, None, None, 0),
        ]),
    ]

    # Prelim rates (contract_rate set directly, no spec/labour)
    prelim_rates = {
        'Site establishment and mobilisation': 380000,
        'Site offices, stores and ablutions': 280000,
        'Temporary water supply and reticulation': 75000,
        'Temporary electrical supply': 110000,
        'Safety requirements, PPE and first aid': 125000,
        'Setting out the works': 60000,
        'Environmental management plan': 48000,
        'Site management (12 months)': 140000,
        'Security services (12 months)': 38000,
        'Temporary fencing and hoarding (12 months)': 14000,
        'Plant and equipment (12 months)': 55000,
        'Water and electricity charges (12 months)': 20000,
    }

    # ── Section 2: Media Centre (850m², new build) ──
    sections['Section 2 - Media Centre'] = _new_build_bills(
        floor_area=850, wall_perim=130, wall_height=3.2,
        num_doors=22, num_windows_csm=30, num_windows_sld=12,
        roof_area=980, num_trusses=36, ridge_length=50,
        num_basins=6, num_wcs=6,
    )

    # ── Section 3: Admin Block (1500m², new build) ──
    sections['Section 3 - Admin Block'] = _new_build_bills(
        floor_area=1500, wall_perim=240, wall_height=3.2,
        num_doors=46, num_windows_csm=54, num_windows_sld=18,
        roof_area=1700, num_trusses=64, ridge_length=90,
        num_basins=14, num_wcs=16,
    )

    # ── Section 4: Kitchen Conversion ──
    sections['Section 4 - Kitchen Conversion'] = _conversion_bills(
        floor_area=350, wall_perim=82, wall_height=3.0,
        num_doors=12, num_windows_csm=10,
    )

    # ── Section 5: Classroom Refurbishment ──
    sections['Section 5 - Classroom Refurbishment'] = _refurb_bills(
        floor_area=1200, wall_perim=440, wall_height=3.0,
        num_doors=30,
    )

    # ── Section 6: Demolition ──
    sections['Section 6 - Demolition'] = [
        ('Bill No. 1 - Earthworks: Demolition', 'EAR-', [
            ('Demolish brick/block walls', 'm3', 650, None, 'Demolition', 0.15),
            ('Demolish concrete floor slabs 150mm thick', 'm3', 180, None, 'Demolition', 0.15),
            ('Demolish and remove roof structures', 'm2', 520, None, 'Demolition', 0.15),
            ('Remove existing electrical and plumbing services', 'sum', 1, None, None, 0),
            ('Load and cart away rubble', 'm3', 820, None, 'Demolition', 0.15),
            ('Dispose at licensed landfill', 'm3', 820, None, None, 0),
            ('Grub tree stumps and remove', 'No', 25, None, None, 0),
            ('Level and compact site after demolition', 'm2', 1200, None, 'Site Preparation', 0.15),
        ]),
    ]

    return sections, prelim_rates


def _new_build_bills(floor_area, wall_perim, wall_height,
                     num_doors, num_windows_csm, num_windows_sld,
                     roof_area, num_trusses, ridge_length,
                     num_basins, num_wcs):
    """Generate full bill sequence for a new build section."""
    wall_area = wall_perim * wall_height
    ext_wall_area = wall_area * 0.6
    _ = wall_area * 0.4  # int_wall_area reserved for future use
    window_area = (num_windows_csm * 1.44 + num_windows_sld * 2.16)
    net_wall = wall_area - window_area - (num_doors * 1.65)

    bills = []

    # Bill 1: Earthworks
    bills.append(('Bill No. 1 - Earthworks', 'EAR-', [
        ('Remove topsoil average 150mm deep, stockpile', 'm2', round(floor_area * 1.3), None, 'Site Preparation', 0.15),
        ('Excavate for strip footings in soft material', 'm3', round(wall_perim * 0.6 * 0.8), None, 'Trench Excavation', 0.15),
        ('Extra-over for intermediate excavation', 'm3', round(wall_perim * 0.1), None, 'Trench Excavation', 0.15),
        ('Backfill with selected material, compact to 93% Mod AASHTO', 'm3', round(wall_perim * 0.3), None, 'Backfill & Compact', 0.15),
        ('Dispose surplus excavated material off site', 'm3', round(wall_perim * 0.25), None, None, 0),
    ]))

    # Bill 2: Concrete
    slab_vol = round(floor_area * 0.10, 1)
    footing_vol = round(wall_perim * 0.6 * 0.3, 1)
    bills.append(('Bill No. 2 - Concrete, Formwork & Reinforcement', 'CFR-', [
        ('Blinding 10MPa under footings 50mm thick', 'm3', round(wall_perim * 0.6 * 0.05, 1), '15MPa', 'Blinding Layer', 0.15),
        ('Strip footings in 20MPa concrete', 'm3', footing_vol, '25MPa', 'Concrete Placement', 0.15),
        ('Surface bed 100mm thick in 25MPa concrete', 'm3', slab_vol, '25MPa', 'Concrete Placement', 0.15),
        ('Reinforced lintels in 25MPa concrete', 'm3', round(num_doors * 0.08 + (num_windows_csm + num_windows_sld) * 0.06, 1), '25MPa', 'Concrete Placement', 0.15),
        ('Mesh Ref 395 in surface bed', 'm2', round(floor_area * 1.05), 'Mesh Reinforcement - Ref 395', 'Mesh Laying', 0.15),
        ('Rebar Y12 to footings and lintels', 't', round(footing_vol * 0.08, 2), 'Rebar - High Tensile Y12', 'Rebar Fixing', 0.15),
        ('Rough formwork to sides of footings', 'm2', round(wall_perim * 0.6 * 2, 1), 'Rough Formwork - 18mm', 'Formwork Erection', 0.15),
        ('Power float finish to surface bed', 'm2', floor_area, None, None, 0),
        ('10mm Expansion joints in surface bed', 'm', round(floor_area ** 0.5 * 4), None, None, 0),
        ('Test cubes 150x150x150mm', 'No', 12, None, None, 0),
    ]))

    # Bill 3: Masonry
    half_brick_area = round(net_wall * 0.55)
    one_brick_area = round(net_wall * 0.15)
    face_brick_area = round(ext_wall_area * 0.20)
    bills.append(('Bill No. 3 - Masonry', 'MAN-', [
        ('Half brick walls in NFP bricks Class II mortar', 'm2', half_brick_area, 'Half Brick Wall - Class II', 'Brickwork - Half Brick', 0.15),
        ('One brick walls in NFP bricks Class II mortar', 'm2', one_brick_area, 'One Brick Wall - Class II', 'Brickwork - One Brick', 0.15),
        ('Face brick external walls, recessed pointing', 'm2', face_brick_area, 'Face Brick Wall', 'Brickwork - Half Brick', 0.15),
        ('Precast concrete lintels 110x75mm', 'm', round((num_doors + num_windows_csm + num_windows_sld) * 1.2), 'Precast Lintels', 'DPC Installation', 0.15),
        ('DPC 150mm wide in walls', 'm', round(wall_perim * 1.1), 'DPC in Walls', 'DPC Installation', 0.15),
        ('DPM 375 micron under surface bed', 'm2', round(floor_area * 1.05), 'DPM Under Slabs', 'DPC Installation', 0.15),
    ]))

    # Bill 4: Waterproofing
    bills.append(('Bill No. 4 - Waterproofing', 'WPR-', [
        ('Torch-on waterproofing to wet areas (toilets, kitchenette)', 'm2', round(floor_area * 0.15), 'Waterproofing Membrane', 'Waterproofing Membrane', 0.15),
        ('DPM 250 micron under screed in wet areas', 'm2', round(floor_area * 0.15), 'DPM 250 Micron', 'Waterproofing Membrane', 0.15),
    ]))

    # Bill 5: Roofing
    bills.append(('Bill No. 5 - Roof Coverings', 'ROF-', [
        ('IBR 0.5mm Chromadek roof sheeting', 'm2', roof_area, 'IBR Roof Sheeting', 'Roof Sheeting', 0.15),
        ('Ridge capping galvanised', 'm', ridge_length, 'Ridge Capping', 'Roof Sheeting', 0.15),
        ('Insulation 135mm Isotherm/Aerolite', 'm2', round(roof_area * 0.85), 'Roof Insulation 135mm', 'Roof Insulation', 0.15),
        ('Aluminium flashing to parapets and abutments', 'm', round(wall_perim * 0.3), None, None, 0),
    ]))

    # Bill 6: Carpentry & Joinery
    bills.append(('Bill No. 6 - Carpentry and Joinery', 'CRJ-', [
        ('Timber roof trusses, SA Pine, treated', 'each', num_trusses, 'Timber Roof Truss', 'Truss Erection', 0.15),
        ('Battens 38x38mm SA Pine at 450mm centres', 'm', round(roof_area * 2.2), 'Timber Battens 38x38', 'Timber Battens', 0.15),
        ('Fibre cement fascia board 225x6mm', 'm', round(wall_perim * 0.8), 'Fibre Cement Fascia', 'Timber Battens', 0.15),
        ('Meranti door frames 813x2032mm', 'each', num_doors, 'Door Frame - Meranti', 'Door Hanging', 0.15),
        ('Hollow core doors 813x2032x40mm', 'each', num_doors, 'Hollow Core Door', 'Door Hanging', 0.15),
    ]))

    # Bill 7: Ceilings
    bills.append(('Bill No. 7 - Ceilings', 'CPA-', [
        ('9.5mm Gypsum ceiling board on 38x38 brandering', 'm2', floor_area, 'Gypsum Ceiling 9.5mm', 'Ceiling Boarding', 0.15),
        ('75mm Gypsum coved cornice', 'm', round(wall_perim * 1.5), None, 'Ceiling Boarding', 0.15),
    ]))

    # Bill 8: Floor Coverings
    bills.append(('Bill No. 8 - Floor Coverings', 'FLR-', [
        ('Ceramic floor tiles 300x300mm on adhesive bed', 'm2', round(floor_area * 0.3), 'Ceramic Floor Tiles 300x300', 'Floor Tiling', 0.15),
        ('Vinyl sheet flooring 2mm thick', 'm2', round(floor_area * 0.6), 'Vinyl Sheet Flooring', 'Floor Tiling', 0.15),
    ]))

    # Bill 9: Ironmongery
    bills.append(('Bill No. 9 - Ironmongery', 'IRM-', [
        ('100mm Butt hinges, 3 per door', 'pair', num_doors * 3, 'Butt Hinges 100mm', 'Ironmongery Fitting', 0.15),
        ('3-lever mortice lock', 'each', num_doors, '3-Lever Mortice Lock', 'Ironmongery Fitting', 0.15),
        ('Lever handle sets chrome', 'each', num_doors, 'Lever Handle Set', 'Ironmongery Fitting', 0.15),
        ('Hydraulic door closers to external doors', 'each', max(2, num_doors // 3), 'Door Closer', 'Ironmongery Fitting', 0.15),
    ]))

    # Bill 10: Structural Steelwork
    steel_kg = round(roof_area * 3.5)
    bills.append(('Bill No. 10 - Structural Steelwork', 'STW-', [
        ('Structural steel roof members, hot-dip galvanised', 'kg', steel_kg, 'Structural Steel IPE', 'Steel Erection', 0.15),
    ]))

    # Bill 11: Metalwork
    bills.append(('Bill No. 11 - Metalwork', 'MTW-', [
        ('Pressed steel door frames 1.2mm rebated', 'each', max(2, num_doors // 3), 'Pressed Steel Door Frame', 'Steel Frame Install', 0.15),
        ('Steel window frames galvanised', 'each', max(2, num_windows_csm // 3), 'Steel Window Frame', 'Steel Frame Install', 0.15),
    ]))

    # Bill 12: Plastering
    bills.append(('Bill No. 12 - Plastering', 'PLA-', [
        ('12mm Cement plaster on internal brick walls', 'm2', round(net_wall * 0.7), 'Plaster Internal 12mm', 'Internal Plastering', 0.15),
        ('15mm Cement plaster on external brick walls', 'm2', round(ext_wall_area * 0.75), 'Plaster External 15mm', 'External Plastering', 0.15),
        ('40mm Cement screed to floors', 'm2', floor_area, 'Screed 40mm', 'Screeding', 0.15),
    ]))

    # Bill 13: Plumbing & Drainage
    plumb_length = round(wall_perim * 0.4)
    bills.append(('Bill No. 13 - Plumbing and Drainage', 'PLD-', [
        ('50mm PVC waste pipes including fittings', 'm', plumb_length, 'PVC Waste Pipe 50mm', 'Pipe Installation', 0.15),
        ('PVC gutters and downpipes', 'm', round(wall_perim * 0.5), 'PVC Gutter & Downpipe', 'Pipe Installation', 0.15),
        ('Pedestal wash basins complete', 'each', num_basins, None, 'Sanitary Fittings', 0.15),
        ('Close-coupled WC suites complete', 'each', num_wcs, None, 'Sanitary Fittings', 0.15),
    ]))

    # Bill 14: Glazing
    bills.append(('Bill No. 14 - Glazing', 'GLZ-', [
        ('Aluminium casement windows 1200x1200mm', 'each', num_windows_csm, 'Aluminium Casement Window', 'Glass Installation', 0.15),
        ('Aluminium sliding windows 1800x1200mm', 'each', num_windows_sld, 'Aluminium Sliding Window', 'Glass Installation', 0.15),
    ]))

    # Bill 15: Paintwork
    bills.append(('Bill No. 15 - Paintwork', 'PAW-', [
        ('PVA interior paint, 2 coats on plastered walls and ceilings', 'm2', round(net_wall * 0.7 + floor_area), 'PVA Internal 2 Coats', 'Internal Painting', 0.15),
        ('Acrylic exterior paint, 2 coats on plastered walls', 'm2', round(ext_wall_area * 0.75), 'Acrylic External 2 Coats', 'External Painting', 0.15),
        ('Enamel paint on metalwork, doors and frames', 'm2', round(num_doors * 4.5), 'Enamel on Metalwork', 'Enamel Painting', 0.15),
    ]))

    # Bill 16: Electrical
    conduit_m = round(floor_area * 1.8)
    cable_m = round(floor_area * 2.5)
    num_lights = round(floor_area / 8)
    num_sockets = round(floor_area / 12)
    bills.append(('Bill No. 16 - Electrical Installations', 'ELW-', [
        ('20mm PVC conduit in walls and ceilings', 'm', conduit_m, 'PVC Conduit 20mm', 'Conduit Installation', 0.15),
        ('2.5mm Twin and Earth cable', 'm', cable_m, 'Cable 2.5mm T&E', 'Cable Pulling', 0.15),
        ('LED light fittings 2x18W 1200mm', 'each', num_lights, 'LED Light Fitting', 'Light Fitting Install', 0.15),
        ('Double switched socket outlets', 'each', num_sockets, None, None, 0),
        ('Single-lever light switches', 'each', round(num_lights * 0.5), None, None, 0),
        ('12-way distribution board, pre-wired', 'each', max(1, round(floor_area / 200)), 'Distribution Board', 'DB Board Installation', 0.15),
    ]))

    # Bill 17: Provisional Sums
    bills.append(('Bill No. 17 - Provisional Sums', 'PRC-', [
        ('Contingency allowance', 'sum', 1, None, None, 0),
        ('Professional fees and testing', 'sum', 1, None, None, 0),
    ]))

    return bills


def _conversion_bills(floor_area, wall_perim, wall_height, num_doors, num_windows_csm):
    """Bills for kitchen conversion (subset of trades, no earthworks/roofing)."""
    wall_area = wall_perim * wall_height
    net_wall = wall_area - (num_windows_csm * 1.44) - (num_doors * 1.65)

    bills = []

    # Concrete: new kitchen floor slab and service trenches
    bills.append(('Bill No. 1 - Concrete, Formwork & Reinforcement', 'CFR-', [
        ('Break out existing floor slab 150mm thick', 'm3', round(floor_area * 0.15, 1), None, None, 0),
        ('New 25MPa surface bed 150mm thick', 'm3', round(floor_area * 0.15, 1), '25MPa', 'Concrete Placement', 0.15),
        ('Mesh Ref 395 in surface bed', 'm2', round(floor_area * 1.05), 'Mesh Reinforcement - Ref 395', 'Mesh Laying', 0.15),
        ('Power float finish to surface bed', 'm2', floor_area, None, None, 0),
    ]))

    # Masonry: internal partition walls
    bills.append(('Bill No. 2 - Masonry', 'MAN-', [
        ('Half brick partition walls, NFP Class II', 'm2', round(net_wall * 0.3), 'Half Brick Wall - Class II', 'Brickwork - Half Brick', 0.15),
        ('Precast concrete lintels over openings', 'm', round((num_doors + num_windows_csm) * 1.2), 'Precast Lintels', 'DPC Installation', 0.15),
    ]))

    # Waterproofing
    bills.append(('Bill No. 3 - Waterproofing', 'WPR-', [
        ('Torch-on waterproofing to kitchen floor', 'm2', floor_area, 'Waterproofing Membrane', 'Waterproofing Membrane', 0.15),
    ]))

    # Carpentry
    bills.append(('Bill No. 4 - Carpentry and Joinery', 'CRJ-', [
        ('Meranti door frames', 'each', num_doors, 'Door Frame - Meranti', 'Door Hanging', 0.15),
        ('Solid timber doors (kitchen rated)', 'each', num_doors, 'Hollow Core Door', 'Door Hanging', 0.15),
    ]))

    # Ceilings
    bills.append(('Bill No. 5 - Ceilings', 'CPA-', [
        ('9.5mm Gypsum ceiling board on brandering', 'm2', floor_area, 'Gypsum Ceiling 9.5mm', 'Ceiling Boarding', 0.15),
    ]))

    # Plastering
    bills.append(('Bill No. 6 - Plastering', 'PLA-', [
        ('12mm Cement plaster on internal walls', 'm2', round(net_wall * 0.8), 'Plaster Internal 12mm', 'Internal Plastering', 0.15),
        ('40mm Screed to kitchen floor', 'm2', floor_area, 'Screed 40mm', 'Screeding', 0.15),
    ]))

    # Plumbing
    bills.append(('Bill No. 7 - Plumbing and Drainage', 'PLD-', [
        ('110mm PVC soil pipe', 'm', 25, 'PVC Waste Pipe 50mm', 'Pipe Installation', 0.15),
        ('50mm PVC waste pipes', 'm', 30, 'PVC Waste Pipe 50mm', 'Pipe Installation', 0.15),
        ('Commercial stainless steel sink units', 'each', 3, None, 'Sanitary Fittings', 0.15),
        ('Grease trap installation', 'each', 1, None, 'Sanitary Fittings', 0.15),
    ]))

    # Electrical
    bills.append(('Bill No. 8 - Electrical Installations', 'ELW-', [
        ('20mm PVC conduit', 'm', round(floor_area * 2), 'PVC Conduit 20mm', 'Conduit Installation', 0.15),
        ('4.0mm cable for heavy-duty circuits', 'm', round(floor_area * 1.5), 'Cable 2.5mm T&E', 'Cable Pulling', 0.15),
        ('LED light fittings', 'each', round(floor_area / 8), 'LED Light Fitting', 'Light Fitting Install', 0.15),
        ('3-phase distribution board', 'each', 1, 'Distribution Board', 'DB Board Installation', 0.15),
    ]))

    # Paintwork
    bills.append(('Bill No. 9 - Paintwork', 'PAW-', [
        ('PVA interior paint 2 coats on walls and ceilings', 'm2', round(net_wall * 0.8 + floor_area), 'PVA Internal 2 Coats', 'Internal Painting', 0.15),
        ('Enamel paint on doors and frames', 'm2', round(num_doors * 4.5), 'Enamel on Metalwork', 'Enamel Painting', 0.15),
    ]))

    return bills


def _refurb_bills(floor_area, wall_perim, wall_height, num_doors):
    """Bills for classroom refurbishment (light scope)."""
    wall_area = wall_perim * wall_height
    net_wall = wall_area - (num_doors * 1.65)

    bills = []

    # Ceilings
    bills.append(('Bill No. 1 - Ceilings', 'CPA-', [
        ('Remove damaged ceiling boards and brandering', 'm2', round(floor_area * 0.3), None, None, 0),
        ('New 9.5mm Gypsum ceiling board on brandering', 'm2', round(floor_area * 0.4), 'Gypsum Ceiling 9.5mm', 'Ceiling Boarding', 0.15),
        ('75mm Coved cornice', 'm', round(wall_perim * 0.6), None, 'Ceiling Boarding', 0.15),
    ]))

    # Plastering
    bills.append(('Bill No. 2 - Plastering', 'PLA-', [
        ('Hack off damaged plaster and prepare surfaces', 'm2', round(net_wall * 0.25), None, None, 0),
        ('12mm Re-plaster on internal walls', 'm2', round(net_wall * 0.3), 'Plaster Internal 12mm', 'Internal Plastering', 0.15),
        ('40mm Cement screed repairs to floors', 'm2', round(floor_area * 0.4), 'Screed 40mm', 'Screeding', 0.15),
    ]))

    # Paintwork
    bills.append(('Bill No. 3 - Paintwork', 'PAW-', [
        ('Prepare previously painted surfaces', 'm2', round(net_wall + floor_area), None, None, 0),
        ('PVA interior paint 2 coats on walls and ceilings', 'm2', round(net_wall + floor_area), 'PVA Internal 2 Coats', 'Internal Painting', 0.15),
        ('Enamel paint on doors and frames', 'm2', round(num_doors * 4.5), 'Enamel on Metalwork', 'Enamel Painting', 0.15),
    ]))

    # Electrical
    bills.append(('Bill No. 4 - Electrical Installations', 'ELW-', [
        ('Replace existing light fittings with LED', 'each', round(floor_area / 10), 'LED Light Fitting', 'Light Fitting Install', 0.15),
        ('Replace distribution boards', 'each', 3, 'Distribution Board', 'DB Board Installation', 0.15),
        ('New PVC conduit runs', 'm', round(floor_area * 0.5), 'PVC Conduit 20mm', 'Conduit Installation', 0.15),
        ('New cable 2.5mm T&E', 'm', round(floor_area * 0.8), 'Cable 2.5mm T&E', 'Cable Pulling', 0.15),
    ]))

    # Plumbing
    bills.append(('Bill No. 5 - Plumbing and Drainage', 'PLD-', [
        ('Replace mixer taps', 'each', 8, None, 'Sanitary Fittings', 0.15),
        ('Repair/replace waste pipes', 'm', 20, 'PVC Waste Pipe 50mm', 'Pipe Installation', 0.15),
    ]))

    # Ironmongery
    bills.append(('Bill No. 6 - Ironmongery', 'IRM-', [
        ('New 3-lever mortice locks', 'each', num_doors, '3-Lever Mortice Lock', 'Ironmongery Fitting', 0.15),
        ('Lever handle sets', 'each', num_doors, 'Lever Handle Set', 'Ironmongery Fitting', 0.15),
        ('Hydraulic door closers', 'each', num_doors, 'Door Closer', 'Ironmongery Fitting', 0.15),
    ]))

    return bills


# ═══════════════════════════════════════════════════════════════════════
# MANAGEMENT COMMAND
# ═══════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = 'Wipe all data and generate realistic SA school construction project data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm', action='store_true',
            help='Confirm you want to wipe all existing data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stderr.write(self.style.WARNING(
                'This will DELETE all existing data. Use --confirm to proceed.'
            ))
            return

        self.stdout.write('Wiping all existing data...')
        BOQItem.objects.all().delete()
        BOQItem.objects.all().delete()
        SpecificationComponent.objects.all().delete()
        Specification.objects.all().delete()
        LabourSpecification.objects.all().delete()
        LabourCrew.objects.all().delete()
        Material.objects.all().delete()
        TradeCode.objects.all().delete()

        # Step 1: Trade Codes
        self.stdout.write('Creating trade codes...')
        tc_map = {}
        for prefix, name in TRADE_CODES:
            tc = TradeCode.objects.create(prefix=prefix, trade_name=name)
            tc_map[prefix] = tc
        self.stdout.write(f'  {len(tc_map)} trade codes')

        # Step 2: Materials
        self.stdout.write('Creating materials...')
        mat_map = {}
        for code, trade, unit, rate, variety, spec in MATERIALS:
            m = Material.objects.create(
                material_code=code,
                trade_name=trade,
                unit=unit,
                market_rate=D(str(rate)),
                material_variety=variety,
                market_spec=spec,
            )
            mat_map[code] = m
        self.stdout.write(f'  {len(mat_map)} materials')

        # Step 3: Labour Crews
        self.stdout.write('Creating labour crews...')
        crew_map = {}
        for ctype, size, sk, ss, gen, sr, ssr, gr in LABOUR_CREWS:
            c = LabourCrew.objects.create(
                crew_type=ctype,
                crew_size=size,
                skilled=sk,
                semi_skilled=ss,
                general=gen,
                daily_production=D('10'),
                skilled_rate=D(str(sr)),
                semi_skilled_rate=D(str(ssr)),
                general_rate=D(str(gr)),
            )
            crew_map[ctype] = c
        self.stdout.write(f'  {len(crew_map)} labour crews')

        # Step 4: Specifications (per section)
        self.stdout.write('Creating specifications...')
        spec_map = {}  # (section, name) → Specification
        sections_data, prelim_rates = _build_section_items()

        # Determine which spec/labour names are actually used per section
        section_trades = {}
        section_spec_names = {}   # section → set of spec_name
        section_labour_names = {}  # section → set of labour_name
        for section, bills in sections_data.items():
            prefixes = set()
            spec_names_used = set()
            labour_names_used = set()
            for _bill_name, trade_prefix, items in bills:
                prefixes.add(trade_prefix)
                for _desc, _unit, _qty, spec_name, labour_name, _markup in items:
                    if spec_name:
                        spec_names_used.add(spec_name)
                    if labour_name:
                        labour_names_used.add(labour_name)
            section_trades[section] = prefixes
            section_spec_names[section] = spec_names_used
            section_labour_names[section] = labour_names_used

        spec_count = 0
        comp_count = 0
        for section, _prefixes in section_trades.items():
            if section == 'Section 1 - Preliminaries':
                continue  # No specs for prelims
            used_names = section_spec_names.get(section, set())
            for sname, sprefix, sunit, components in SPEC_TEMPLATES:
                if sname not in used_names:
                    continue
                tc = tc_map.get(sprefix)
                spec = Specification.objects.create(
                    section=section,
                    trade_code=tc,
                    unit_label=sunit,
                    name=sname,
                    boq_quantity=0,
                )
                spec_map[(section, sname)] = spec
                spec_count += 1
                for mat_code, label, qty in components:
                    mat = mat_map.get(mat_code)
                    SpecificationComponent.objects.create(
                        specification=spec,
                        material=mat,
                        label=label,
                        qty_per_unit=qty,
                    )
                    comp_count += 1
        self.stdout.write(f'  {spec_count} specifications, {comp_count} components')

        # Step 5: Labour Specifications (per section)
        self.stdout.write('Creating labour specifications...')
        labour_map = {}  # (section, name) → LabourSpecification
        ls_count = 0
        for section, _prefixes in section_trades.items():
            if section == 'Section 1 - Preliminaries':
                continue
            used_labour = section_labour_names.get(section, set())
            for lname, lprefix, lunit, crew_type, daily_prod in LABOUR_TEMPLATES:
                if lname not in used_labour:
                    continue
                crew = crew_map.get(crew_type)
                tc = tc_map.get(lprefix)
                trade_name_str = f'{lprefix}{tc.trade_name}' if tc else lprefix
                ls = LabourSpecification.objects.create(
                    section=section,
                    trade_name=trade_name_str,
                    name=lname,
                    unit=lunit,
                    crew=crew,
                    daily_production=D(str(daily_prod)),
                    team_mix=D('1.0000'),
                    site_factor=D('1.0000'),
                    tools_factor=D('1.0000'),
                    leadership_factor=D('1.0000'),
                    boq_quantity=0,
                )
                labour_map[(section, lname)] = ls
                ls_count += 1
        self.stdout.write(f'  {ls_count} labour specifications')

        # Step 6: BOQ Items
        self.stdout.write('Creating BoQ items...')
        baseline_count = 0
        output_count = 0
        grand_total = D('0')

        for section, bills in sections_data.items():
            section_base_progress = SECTION_PROGRESS.get(section, 0.5)
            item_seq = 0

            for bill_name, trade_prefix, items in bills:
                tc = tc_map.get(trade_prefix)

                # Create section header
                header_fields = {
                    'section': section,
                    'bill_no': bill_name,
                    'trade_code': tc,
                    'item_no': '',
                    'pay_ref': '',
                    'description': bill_name.split(' - ', 1)[-1] if ' - ' in bill_name else bill_name,
                    'unit': '',
                    'contract_quantity': None,
                    'contract_rate': None,
                    'is_section_header': True,
                }
                BOQItem.objects.create(**header_fields)
                BOQItem.objects.create(**header_fields, progress_quantity=None, forecast_quantity=None)
                baseline_count += 1
                output_count += 1

                for desc, unit, qty, spec_name, labour_name, markup_pct in items:
                    item_seq += 1
                    spec = spec_map.get((section, spec_name)) if spec_name else None
                    labour = labour_map.get((section, labour_name)) if labour_name else None

                    # Calculate contract rate
                    mat_rate = D('0')
                    lab_rate = D('0')
                    if spec:
                        mat_rate = spec.rate_per_unit or D('0')
                    if labour:
                        lab_rate = labour.rate_per_unit or D('0')

                    if mat_rate + lab_rate > 0:
                        contract_rate = (mat_rate + lab_rate) * (1 + D(str(markup_pct)))
                    elif section == 'Section 1 - Preliminaries':
                        contract_rate = D(str(prelim_rates.get(desc, 0)))
                    elif desc in prelim_rates:
                        contract_rate = D(str(prelim_rates[desc]))
                    else:
                        # Items without spec/labour: use reasonable defaults
                        default_rates = {
                            'm2': 65, 'm': 120, 'm3': 850, 'No': 450,
                            'each': 450, 'sum': 65000, 'pair': 130,
                            'kg': 32, 't': 18500, 'month': 45000,
                        }
                        contract_rate = D(str(default_rates.get(unit, 100)))

                    qty_d = D(str(qty))
                    contract_amount = qty_d * contract_rate
                    grand_total += contract_amount

                    # Calculate progress and forecast
                    trade_offset = TRADE_PROGRESS_OFFSET.get(trade_prefix, 0)
                    eff_progress = min(1.0, max(0.0,
                        section_base_progress + trade_offset + random.uniform(-0.05, 0.05)
                    ))
                    progress_qty = round(float(qty_d) * eff_progress, 2)
                    forecast_qty = round(float(qty_d) * random.uniform(1.00, 1.10), 2)
                    forecast_qty = max(forecast_qty, progress_qty)

                    common = {
                        'section': section,
                        'bill_no': bill_name,
                        'trade_code': tc,
                        'specification': spec,
                        'labour_specification': labour,
                        'item_no': str(item_seq),
                        'pay_ref': f'{section.split(" ")[1]}.{item_seq:03d}',
                        'description': desc,
                        'unit': unit,
                        'contract_quantity': qty_d,
                        'contract_rate': contract_rate.quantize(D('0.01')),
                        'is_section_header': False,
                    }

                    BOQItem.objects.create(**common)
                    BOQItem.objects.create(
                        **common,
                        progress_quantity=D(str(progress_qty)),
                        forecast_quantity=D(str(forecast_qty)),
                    )
                    baseline_count += 1
                    output_count += 1

        self.stdout.write(f'  {baseline_count} baseline items, {output_count} output items')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('DATA GENERATION COMPLETE'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'  Trade Codes:     {TradeCode.objects.count()}')
        self.stdout.write(f'  Materials:       {Material.objects.count()}')
        self.stdout.write(f'  Labour Crews:    {LabourCrew.objects.count()}')
        self.stdout.write(f'  Specifications:  {Specification.objects.count()}')
        self.stdout.write(f'  Spec Components: {SpecificationComponent.objects.count()}')
        self.stdout.write(f'  Labour Specs:    {LabourSpecification.objects.count()}')
        self.stdout.write(f'  Baseline Items:  {BOQItem.objects.count()}')
        self.stdout.write(f'  Output Items:    {BOQItem.objects.count()}')
        self.stdout.write(f'  Grand Total:     R{grand_total:,.2f}')

        # Per-section totals
        self.stdout.write('')
        for section in SECTION_PROGRESS:
            items = BOQItem.objects.filter(
                section=section, is_section_header=False
            )
            sec_total = sum(
                (i.contract_amount or 0) for i in items
            )
            self.stdout.write(f'  {section}: R{sec_total:,.2f}')

        # Sample rate checks
        self.stdout.write('')
        self.stdout.write('Rate checks:')
        for sname in ['25MPa', 'Half Brick Wall - Class II', 'PVA Internal 2 Coats', 'IBR Roof Sheeting']:
            spec = Specification.objects.filter(name=sname).first()
            if spec:
                self.stdout.write(f'  {sname}: material R{spec.rate_per_unit:.2f}/{spec.unit_label}')
