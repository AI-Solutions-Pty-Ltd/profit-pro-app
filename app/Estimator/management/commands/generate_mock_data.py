"""
Generate realistic mock data for BoQ items.

Assigns material specifications, labour specifications, direct materials,
and generates forecast/progress quantities based on description and unit matching.
"""

import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from app.Estimator.models import (
    BOQItem,
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

# ── Unit normalisation ───────────────────────────────────────────────

UNIT_MAP = {
    'no': 'no', 'no.': 'no',
    'sum': 'sum',
    'item': 'item', 'items': 'item',
    'm³': 'm3',
}


def normalize_unit(unit):
    return UNIT_MAP.get(unit.lower().strip(), unit.lower().strip())


# ── Matching engine ──────────────────────────────────────────────────

def match_rules(desc, unit, rules, lookup_dict):
    desc_lower = desc.lower()
    unit_norm = normalize_unit(unit)
    for keywords, match_unit, name in rules:
        if unit_norm != normalize_unit(match_unit):
            continue
        for kw in keywords:
            if kw in desc_lower:
                if name is None:
                    return None
                if name in lookup_dict:
                    return lookup_dict[name]
                break
    return None


def find_direct_material(desc, unit, rules, all_materials):
    desc_lower = desc.lower()
    unit_norm = normalize_unit(unit)
    for keywords, match_unit, mat_code in rules:
        if unit_norm != normalize_unit(match_unit):
            continue
        if mat_code is None:
            continue
        for kw in keywords:
            if kw in desc_lower:
                if mat_code in all_materials:
                    return all_materials[mat_code]
                break
    return None


class Command(BaseCommand):
    help = 'Generate mock spec assignments and forecast data for BoQ items'

    def handle(self, *args, **options):
        random.seed(42)

        specs = {s.name: s for s in Specification.objects.all()}
        labour_specs = {ls.name: ls for ls in LabourSpecification.objects.all()}
        all_materials = {m.material_code: m for m in Material.objects.all()}

        # ── Material Specification Rules ─────────────────────────────
        mat_spec_rules = [
            # Concrete by strength
            (['blinding', 'under footings'], 'm3', '10MPa'),
            (['apron'], 'm3', '15MPa'),
            (['surface bed', 'slab', 'in surface'], 'm3', '25MPa'),
            (['footing', 'foundation', 'bases', 'in footing'], 'm3', '20MPa'),
            (['veranda', 'verander'], 'm3', '20MPa'),
            (['column', 'beam'], 'm3', '30MPa'),
            (['lintel'], 'm3', '25MPa'),
            (['pier'], 'm3', '25MPa'),
            (['thickening'], 'm3', '20MPa'),
            (['soft sifted soil', 'backfill'], 'm3', '10MPa'),
            # Brickwork
            (['one brick wall'], 'm2', 'One Brick - Class II'),
            (['half brick wall', 'half brick'], 'm2', 'Half Brick - Class II'),
            (['beamfilling'], 'm2', 'Half Brick - Class II'),
            (['pier brick'], 'm3', 'One Brick - Class II'),
            (['face brickwork', 'extra over.*face'], 'm2', 'Maxi Brick - Class II'),
            (['brick on edge'], 'm', 'Brick Copings'),
            (['window sill', 'precast.*sill'], 'm', 'Precast Sills'),
            (['brick reinforcement', '75mm wide brick', 'brickforce'], 'm', 'Damp Course - DPC 75mm'),
            (['150mm wide brick'], 'm', 'Damp Course - DPC 150mm'),
            # Blocks
            (['140mm block', 'block wall 140', 'm140'], 'm2', 'Block-M140'),
            (['90mm block', 'block wall 90', 'm90'], 'm2', 'Block-M90'),
            # Formwork
            (['formwork', 'shuttering', 'shutterboard'], 'm2', 'Rough Formwork Shutterboard - 18mm'),
            (['turning piece'], 'm', 'Turning Piece'),
            # Reinforcement
            (['ref 395', '395 layer'], 'm2', 'Mesh Reinforcement - Ref 395'),
            (['ref 245', '245 layer'], 'm2', 'Mesh Reinforcement - Ref 245'),
            (['ref 100', '100 layer'], 'm2', 'Mesh Reinforcement - Ref 100'),
            (['ref 617', '617 layer'], 'm2', 'Mesh Reinforcement - Ref 617'),
            (['ref 888', '888 layer'], 'm2', 'Mesh Reinforcement - Ref 888'),
            (['various bars', 'rebar', 'high-tensile'], 't', 'Rebar Reinforcement - High Tensile Y12'),
            # DPC / DPM
            (['under surface bed', 'under apron', 'damp proof membrane', 'dpm'], 'm2', 'Damp Proof Membrane - DPM 250Micron'),
            (['375micron'], 'm2', 'Damp Proof Membrane - DPM 375Micron'),
            (['in walls', 'dpc in wall'], 'm2', 'Damp Course - DPC 150mm'),
            # Lintels
            (['precast.*lintel', 'concrete lintel'], 'm', 'Block-Lintel U140'),
        ]

        # ── Direct Material Rules (uses actual DB material codes) ────
        direct_mat_rules = [
            # Roofing
            (['ibr', 'corrugated iron', 'roof sheet', 'chromadek', 'galvanized', 'roof covering', 'lightning'], 'm2', 'SKN-IBR580'),
            (['ridge cap', 'ridge'], 'm', 'ACC-RIDG'),
            (['insulation', 'fibre blanket', 'isotherm'], 'm2', 'ACC-INS'),
            (['fascia', 'barge board', 'fibre cement'], 'm', 'TIM-FAS-FIB'),
            (['eave closure'], 'm', 'ACC-EAVE'),
            (['valley'], 'm', 'ACC-VAL'),
            (['roof vent'], 'No', 'ACC-VENT'),
            (['verge tile'], 'No', 'ACC-VERG'),
            # Doors
            (['timber door', 'solid timber door', 'solid door'], 'No', 'DR-SLD-EXT'),
            (['hollow core', 'flush door'], 'No', 'DR-HLO-INT'),
            (['steel door', 'metal door', 'steel frame'], 'No', 'PRS-813'),
            (['door frame', 'meranti frame'], 'No', 'DR-FRM-MER'),
            # Windows
            (['aluminium window', 'aluminum window', 'casement window'], 'No', 'ALU-WIN-CSM'),
            (['sliding window'], 'No', 'ALU-WIN-SLD'),
            (['shopfront', 'shop front'], 'No', 'ALU-SF-STD'),
            (['glass', 'glazing', 'laminated glass'], 'm2', 'ALU-SF-GLZ'),
            (['louvre', 'louver'], 'No', 'ALU-LOU-VNT'),
            # Painting
            (['primer', 'plaster primer'], 'm2', 'PRE-PRM'),
            (['pva paint', 'acrylic pva', 'emulsion', 'two coats', 'three coats', 'paint'], 'm2', 'PVA-INT'),
            (['enamel', 'enamel paint', 'gloss'], 'm2', 'ENM-GLS'),
            (['varnish'], 'm2', 'SIL-PRM'),
            (['textured acrylic'], 'm2', 'ACR-EXT'),
            (['red oxide', 'anti-rust'], 'm2', 'FIN-PRM-ROX'),
            # Plastering
            (['plaster', 'plastering', 'render', 'rendering'], 'm2', 'PLR-MIX-PRE'),
            (['screed', 'floor screed', 'thick on floor', 'on floors', 'floor finish'], 'm2', 'ACC-SCR-LEV'),
            (['cornice', 'coved cornice', 'gypsum cov'], 'm', 'COR-COVE-75'),
            # Tiling
            (['ceramic tile', 'floor tile', 'wall tile', 'tiling'], 'm2', 'CER-FLR'),
            (['porcelain tile', 'porcelain'], 'm2', 'POR-MAT'),
            (['skirting', 'ceramic skirting'], 'm', 'ACC-SKR-CER'),
            (['tile adhesive'], 'm2', 'ADH-CER-STD'),
            (['vinyl', 'vinyl floor', 'wax polish', 'vinyl tile'], 'm2', 'CEL-TILE-VIN'),
            # Plumbing / drainage
            (['gutter', 'rainwater gutter'], 'm', 'RWD-GUT-PVC'),
            (['downpipe', 'rain water pipe', 'rwdp', 'fluted'], 'm', 'RWD-ACC-SHOE'),
            (['pvc pipe', 'drain pipe', 'drainage', 'dia'], 'm', 'PIP-HDPE-50'),
            (['tap', 'bib tap', 'mixer', 'basin mixer'], 'No', 'SAN-TAP-MIX'),
            (['basin', 'wash hand basin', 'whb', 'wash basin'], 'No', 'SAN-BAS-PED'),
            (['toilet', 'wc', 'water closet', 'close coupled'], 'No', 'SAN-BAS-PED'),
            # Electrical
            (['light fitting', 'luminaire', 'fluorescent', 'led'], 'No', 'FIT-SWI-1L'),
            (['switch', 'light switch', 'isolator'], 'No', 'FIT-SWI-1L'),
            (['socket', 'plug point', 'power point'], 'No', 'FIT-SOC-DBL'),
            (['distribution board', 'db board', 'db coc'], 'No', 'DB-BRK-20A'),
            (['cable', 'wiring', 'surfix', 'conductor', 'core'], 'm', 'CAB-S2.5'),
            (['conduit'], 'm', 'CON-PVC-20'),
            (['earth wire', 'earth conductor', 'copper earth', 'earth bar', 'flat bar', 'copper bar'], 'm', 'CAB-ECC-16'),
            (['ampere', 'circuit breaker', 'mcb'], 'No', 'DB-BRK-20A'),
            (['rcd', 'elcb', 'earth leakage'], 'No', 'DB-BRK-EL'),
            (['main switch'], 'No', 'DB-BRK-60A'),
            (['warning tape', 'marking tape'], 'm', 'CAB-TE-2.5'),
            (['test terminal', 'terminal block', 'cadweld', 'connection'], 'No', 'DB-BRK-20A'),
            (['danger sign', 'label'], 'No', 'DB-BRK-20A'),
            (['danger sign', 'label'], 'Item', 'DB-BRK-20A'),
            (['drilling', 'hole'], 'No', 'DB-BRK-20A'),
            (['earth rod'], 'No', 'DB-BRK-EL'),
            (['bare stranded', 'bare copper'], 'm', 'CAB-ECC-16'),
            # Carpentry / joinery
            (['meranti skirting', 'wrot', 'timber skirting'], 'm', 'SKR-PVC'),
            (['worktop', 'countertop', 'counter top'], 'No', 'BRD-MEL-WHT'),
            (['cupboard', 'cabinet', 'storage unit'], 'No', 'FIT-CUB-MET'),
            (['shelving', 'shelf', 'shelves', 'fixed shelf'], 'No', 'BRD-MEL-WHT'),
            (['melamine', 'melamine board'], 'm2', 'BRD-MEL-WHT'),
            # Waterproofing
            (['waterproofing', 'waterproof membrane', 'torch on'], 'm2', 'ACR-MEM-20'),
            (['bitumen primer', 'bituminous primer'], 'm2', 'BIT-PR'),
            # Steel / metalwork
            (['balustrade', 'handrail', 'railing'], 'm', 'B-PLAIN'),
            # Ceiling
            (['ceiling', 'brandering', 'suspended ceiling'], 'm2', 'CEL-PVC-9.0'),
            # Furniture
            (['desk', 'table', 'bench', 'round desk'], 'No', 'BRD-MEL-WHT'),
            (['chair', 'stool', 'seating'], 'No', 'BRD-MEL-WHT'),
            (['whiteboard', 'notice board', 'chalkboard'], 'No', 'BRD-MEL-WHT'),
            (['locker'], 'No', 'FIT-CUB-MET'),
            # Supply/install catch-alls
            (['supply and install', 'supply and delivery'], 'No', 'SAN-TAP-MIX'),
            (['supply and install', 'supply and delivery', 'allow'], 'Item', 'SAN-TAP-MIX'),
            # Overhaul
            (['overhaul', 'long overhaul'], 'm3.km', 'PIP-HDPE-50'),
            # Pipe catch-all
            (['pipe', 'mm dia', 'mm²'], 'm', 'PIP-HDPE-50'),
            # Painting surfaces
            (['cornices', 'doors frames', 'window frame', 'doors', 'external walls', 'internal walls'], 'm2', 'PVA-INT'),
            (['to apron'], 'm2', 'PVA-INT'),
            (['aerolite', 'pink'], 'm2', 'ACC-INS'),
            # Plumbing extras
            (['extra over rainwater', 'bends'], 'No', 'RWD-ACC-SHOE'),
            (['telephone point', 'data point', 'surface mounted', 'appliance'], 'No', 'FIT-SOC-DBL'),
            # Earthworks
            (['trenches', 'trench'], 'm', 'PIP-HDPE-50'),
            (['earth rod', '1,8 m earth'], 'm', 'CAB-ECC-16'),
            # Hardware / ironmongery
            (['barrel bolt', 'bolt'], 'No', 'HRD-HNG-100'),
            (['push plate', 'kick plate', 'plate'], 'No', 'HRD-HNG-100'),
            (['hook', 'coat hook', 'rail'], 'No', 'HRD-HNG-100'),
            (['stopper', 'door stop'], 'No', 'HRD-HNG-100'),
            # Glass
            (['pane', 'glass', 'glazing', 'narrow width'], 'm2', 'ALU-SF-GLZ'),
            # Conduit / electrical bare sizes
            (['mm', 'galvanised', 'draw wire'], 'm', 'CON-PVC-20'),
            (['mm', 'deep', 'core'], 'No.', 'DB-BRK-20A'),
            # Provisional / skip
            (['provisional sum', 'prime cost', 'allow a sum'], 'SUM', None),
            (['daywork', 'attendance', 'profit'], '%', None),
        ]

        # ── Labour Specification Rules ───────────────────────────────
        lab_rules = [
            # Earthworks
            (['rip and scarify', 'scarify', 'site preparation', 'topsoil', 'remove topsoil'], 'm2', 'Excavations - Site Preparation'),
            (['excavat', 'excavate for restricted', 'trench'], 'm3', 'Excavations - Manual Trenches'),
            (['intermediate excavat', 'intermediate rock', 'intermediate'], 'm3', 'Excavations - Manual Intermediate Rock'),
            (['hard rock excavat', 'hard rock'], 'm3', 'Excavations - Manual Hard Rock'),
            # Concrete placement
            (['surface bed', 'slab', 'in footing', 'in apron', 'veranda', 'verander', 'thickening'], 'm3', 'Concrete Manual'),
            (['blinding', 'under footings', 'bases'], 'm3', 'Blinding Layer'),
            (['test cube', 'concrete cube'], 'No', 'Concrete Sundries'),
            (['expansion joint', 'joint', 'jointex'], 'm', 'Concrete Joints'),
            (['top of surface', 'top of veranda', 'top apron', 'concrete finish', 'power float'], 'm2', 'Concrete Finishes'),
            (['concrete edge', 'edge beam'], 'm', 'Concrete Edges'),
            # Formwork
            (['to sides footing', 'sides footing', 'side of footing'], 'm2', 'Formwork - Sides'),
            (['formwork', 'shutterboard', 'shuttering'], 'm2', 'Formwork - Foundations'),
            (['soffit', 'suspended slab'], 'm2', 'Formwork - Soffits'),
            (['turning piece'], 'm', 'Formwork - Edges'),
            # Reinforcement
            (['ref 395', 'ref 245', 'ref 100', 'ref 617', 'ref 888', 'mesh', 'layer mesh'], 'm2', 'Mesh Reinforcement'),
            (['various bars', 'rebar', 'high-tensile', 'reinforcement bar'], 't', 'Rebar Reinforcement'),
            # Soil
            (['poison', 'soil poison', 'termite'], 'm2', 'Soil Poisoning'),
            # Brickwork labour
            (['one brick wall', 'half brick wall', 'brick wall', 'pier brick', 'face brick', 'beamfilling'], 'm2', 'Concrete Manual'),
            (['block wall', '140mm block', '90mm block'], 'm2', 'Concrete Manual'),
            # General m2 labour (plastering, tiling, painting, roofing, ceiling, waterproofing, DPC/DPM, insulation)
            (['plaster', 'plastering', 'render', 'screed'], 'm2', 'Concrete Finishes'),
            (['tiling', 'tile', 'ceramic', 'porcelain', 'vinyl'], 'm2', 'Concrete Finishes'),
            (['paint', 'primer', 'enamel', 'pva', 'varnish', 'two coats', 'three coats'], 'm2', 'Concrete Finishes'),
            (['roofing', 'roof sheet', 'ibr', 'corrugated', 'roof covering'], 'm2', 'Formwork - Soffits'),
            (['ceiling', 'brandering'], 'm2', 'Formwork - Soffits'),
            (['waterproofing', 'waterproof', 'bitumen'], 'm2', 'Concrete Finishes'),
            (['dpc', 'dpm', 'damp proof'], 'm2', 'Concrete Finishes'),
            (['insulation', 'fibre blanket', 'isotherm'], 'm2', 'Concrete Finishes'),
            (['glass', 'glazing'], 'm2', 'Concrete Finishes'),
            (['floor', 'on floor', 'polish'], 'm2', 'Concrete Finishes'),
            # General m labour
            (['gutter', 'downpipe', 'fascia', 'barge board', 'cornice', 'skirting'], 'm', 'Concrete Edges'),
            (['pipe', 'conduit', 'cable', 'conductor', 'core', 'dia'], 'm', 'Concrete Edges'),
            (['expansion joint', 'jointex'], 'm', 'Concrete Joints'),
            (['ridge', 'valley', 'eave'], 'm', 'Concrete Edges'),
            (['balustrade', 'handrail', 'railing'], 'm', 'Concrete Edges'),
            (['earth wire', 'earth bar', 'copper', 'bare stranded', 'warning tape'], 'm', 'Concrete Edges'),
            # Unit items (No, No., no, Item, Items)
            (['door', 'window', 'fitting', 'fixture', 'basin', 'toilet', 'sink', 'shower'], 'No', 'Concrete Sundries'),
            (['switch', 'socket', 'plug', 'light', 'ampere', 'circuit', 'breaker', 'rcd', 'elcb'], 'No', 'Concrete Sundries'),
            (['cupboard', 'cabinet', 'shelf', 'worktop', 'desk', 'chair', 'locker', 'board'], 'No', 'Concrete Sundries'),
            (['sign', 'label', 'terminal', 'connection', 'cadweld', 'drilling', 'earth', 'rod'], 'No', 'Concrete Sundries'),
            (['vent', 'verge', 'louvre', 'shopfront', 'hinge', 'closer', 'handle', 'lock'], 'No', 'Concrete Sundries'),
            (['supply', 'install', 'provide', 'manhole', 'inspection', 'frame', 'screw'], 'No', 'Concrete Sundries'),
            # Item unit
            (['sign', 'label', 'db coc', 'allow', 'supply', 'install', 'danger'], 'Item', 'Concrete Sundries'),
            # m3.km
            (['overhaul', 'long overhaul'], 'm3.km', 'Blinding Layer'),
            # Soft soil m3
            (['soft sifted', 'backfill', 'fill'], 'm3', 'Excavations - Manual Trenches'),
            # Pickable soil m³
            (['pickable', 'pick'], 'm3', 'Excavations - Manual Trenches'),
            # G5 material
            (['g5 material', 'compacted'], 'm3', 'Excavations - Manual Trenches'),
            # Painting surface labour
            (['cornices', 'doors frames', 'window frame', 'doors', 'external walls', 'internal walls', 'to apron'], 'm2', 'Concrete Finishes'),
            (['aerolite', 'pink'], 'm2', 'Concrete Finishes'),
            # Plumbing extras
            (['extra over rainwater', 'bends'], 'No', 'Concrete Sundries'),
            (['telephone point', 'data point', 'surface mounted', 'appliance'], 'No', 'Concrete Sundries'),
            # Trench labour
            (['trenches', 'trench'], 'm', 'Concrete Edges'),
            (['earth rod', '1,8 m earth'], 'm', 'Concrete Edges'),
            # Catch-all for remaining m2 items
            (['narrow width', 'on narrow', 'pane', 'exceeding'], 'm2', 'Concrete Finishes'),
            # Catch-all for remaining m items
            (['mm', 'galvanised', 'draw wire'], 'm', 'Concrete Edges'),
            # Catch-all for remaining No items (hardware, ironmongery)
            (['barrel', 'bolt', 'push plate', 'kick plate', 'plate', 'hook', 'stopper', 'stop'], 'No', 'Concrete Sundries'),
            # Catch-all for No. items
            (['mm', 'core', 'deep', 'domestic', 'ampere'], 'No.', 'Concrete Sundries'),
            # Catch-all for remaining no items
            (['copper', 'bar', 'flat'], 'no', 'Concrete Sundries'),
            # Catch-all for empty unit items
            (['bare', 'stranded', 'conductor'], '', 'Concrete Edges'),
        ]

        # ── Process Output BoQ ───────────────────────────────────────
        output_items = BOQItem.objects.filter(is_section_header=False)
        mat_spec = 0
        direct_mat = 0
        lab = 0
        fcst = 0

        for item in output_items:
            changed = False

            # 1) Material specification
            if not item.specification and not item.material:
                s = match_rules(item.description, item.unit, mat_spec_rules, specs)
                if s:
                    item.specification = s
                    mat_spec += 1
                    changed = True

            # 2) Direct material fallback
            if not item.specification and not item.material:
                m = find_direct_material(item.description, item.unit, direct_mat_rules, all_materials)
                if m:
                    item.material = m
                    direct_mat += 1
                    changed = True

            # 3) Labour specification
            if not item.labour_specification:
                matched_labour = match_rules(item.description, item.unit, lab_rules, labour_specs)
                if matched_labour:
                    item.labour_specification = matched_labour
                    lab += 1
                    changed = True

            # 4) Generate forecast/progress quantities
            if item.contract_quantity and item.contract_quantity > 0:
                item.forecast_quantity = (
                    item.contract_quantity * Decimal(str(random.uniform(0.85, 1.20)))
                ).quantize(Decimal('0.01'))
                item.progress_quantity = (
                    item.contract_quantity * Decimal(str(random.uniform(0.30, 0.95)))
                ).quantize(Decimal('0.01'))
                fcst += 1
                changed = True

            if changed:
                item.save()

        self.stdout.write('  Output BoQ:')
        self.stdout.write(f'    Material specs: {mat_spec}')
        self.stdout.write(f'    Direct materials: {direct_mat}')
        self.stdout.write(f'    Labour specs: {lab}')
        self.stdout.write(f'    Forecast/progress: {fcst}')

        # Coverage stats
        with_any = BOQItem.objects.filter(is_section_header=False).exclude(
            specification__isnull=True, material__isnull=True, labour_specification__isnull=True
        ).count()
        total = BOQItem.objects.filter(is_section_header=False).count()
        self.stdout.write(f'    Coverage: {with_any}/{total} ({100*with_any//total}%)')

        # Baseline BoQ is now sourced from BillOfQuantities LineItem (no longer a separate model)
        self.stdout.write(self.style.SUCCESS('Mock data generation completed.'))
