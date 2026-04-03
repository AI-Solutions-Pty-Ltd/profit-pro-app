"""Auto-populate trade_code, specification and labour_specification FKs on BOQItem
by analysing bill_no text and walking section headers in order.

Usage:
    python manage.py auto_populate_fks          # dry-run (shows what would change)
    python manage.py auto_populate_fks --apply  # actually write to DB
"""

from django.core.management.base import BaseCommand

from app.Estimator.models import (
    BOQItem,
    ProjectTradeCode as TradeCode,
    ProjectSpecification as Specification,
    ProjectLabourSpecification as LabourSpecification,
)


# ── bill_no keyword → TradeCode prefix mapping ────────────────────────
BILL_TO_TRADE = {
    'earthworks': 'EAR-',
    'concrete': 'CFR-',
    'masonry': 'MAN-',
    'waterproofing': 'WPR-',
    'roof cover': 'ROF-',
    'roof cladding': 'ROF-',
    'capentry': 'CRJ-',
    'carpentry': 'CRJ-',
    'joinery': 'CRJ-',
    'ceiling': 'CPA-',
    'partition': 'CPA-',
    'floor cover': 'FLR-',
    'wall lining': 'FLR-',
    'plastering': 'PLA-',
    'plumbing': 'PLD-',
    'drainage': 'PLD-',
    'glazing': 'GLZ-',
    'ironmongery': 'IRM-',
    'paintwork': 'PAW-',
    'paperhanging': 'PAH-',
    'electrical': 'ELW-',
    'mechanical': 'MEW-',
    'metalwork': 'MTW-',
    'structural steel': 'STW-',
    'precast': 'PRC-',
    'external': 'EXT-',
    'tiling': 'TIL-',
    'preliminaries': 'PRE-',
    'fixed charge': 'PRE-',
    'time related': 'PRE-',
    'demolition': 'EAR-',
    'alteration': 'EAR-',
}


class Command(BaseCommand):
    help = 'Auto-populate trade_code, specification and labour_specification on BoQ items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help='Actually write changes to the database (default is dry-run)',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        if not apply:
            self.stdout.write(self.style.WARNING('DRY-RUN mode — use --apply to save\n'))

        # Pre-load lookups
        trade_by_prefix = {tc.prefix: tc for tc in TradeCode.objects.all()}
        specs = list(Specification.objects.all())
        labour_specs = list(LabourSpecification.objects.all())

        # Process Output BoQ
        self.stdout.write('\n=== Output BoQ ===')
        stats = self._process_model(BOQItem, trade_by_prefix, specs, labour_specs, apply)
        self._print_stats(stats)

        if apply:
            pass

    def _process_model(self, model_cls, trade_by_prefix, specs, labour_specs, apply):
        items = list(model_cls.objects.select_related(
            'trade_code', 'specification', 'labour_specification',
        ).order_by('id'))

        # Build section-specific lookup dicts for faster matching
        specs_by_section = {}
        for spec in specs:
            specs_by_section.setdefault(spec.section, []).append(spec)

        labour_by_section = {}
        for ls in labour_specs:
            labour_by_section.setdefault(ls.section, []).append(ls)

        stats = {'trade_code': 0, 'specification': 0, 'labour_specification': 0}
        current_spec = None
        current_labour = None
        current_section = None

        for item in items:
            changed = False

            # Track current section for section-aware spec matching
            if item.section and item.section != current_section:
                current_section = item.section
                current_spec = None
                current_labour = None

            # ── Trade Code from bill_no ──
            if not item.trade_code and item.bill_no:
                tc = self._match_trade_code(item.bill_no, trade_by_prefix)
                if tc:
                    item.trade_code = tc
                    stats['trade_code'] += 1
                    changed = True

            # Get section-specific specs
            section_specs = specs_by_section.get(current_section, specs)
            section_labour = labour_by_section.get(current_section, labour_specs)

            # ── Spec / Labour from header context ──
            if item.is_section_header:
                # Check if this header introduces a new spec context
                found_spec = self._match_spec_in_text(item.description, section_specs)
                if found_spec:
                    current_spec = found_spec

                found_labour = self._match_labour_in_text(item.description, section_labour)
                if found_labour:
                    current_labour = found_labour

                # Reset context on major section breaks
                desc_upper = (item.description or '').upper().strip()
                if desc_upper.startswith('BILL NO.') or desc_upper.startswith('SECTION NO.'):
                    current_spec = None
                    current_labour = None
            else:
                # Apply spec to line items — try item description first,
                # then fall back to current header context
                if not item.specification:
                    desc_match = self._match_spec_in_text(
                        item.description, section_specs,
                    )
                    chosen_spec = desc_match or current_spec
                    if chosen_spec:
                        item.specification = chosen_spec
                        stats['specification'] += 1
                        changed = True

                if hasattr(item, 'labour_specification'):
                    if not item.labour_specification:
                        desc_match_l = self._match_labour_in_text(
                            item.description, section_labour,
                        )
                        chosen_labour = desc_match_l or current_labour
                        if chosen_labour:
                            item.labour_specification = chosen_labour
                            stats['labour_specification'] += 1
                            changed = True

            if changed and apply:
                item.save()

        return stats

    def _match_trade_code(self, bill_no, trade_by_prefix):
        bill_lower = bill_no.lower()
        for keyword, prefix in BILL_TO_TRADE.items():
            if keyword in bill_lower:
                return trade_by_prefix.get(prefix)
        return None

    # ── header keyword → Material Spec name mapping ──────────────────────
    HEADER_TO_SPEC = {
        # Concrete
        'blinding layer in 15mpa': '15MPa',
        'blinding layer in 10mpa': '10MPa',
        'reinforced concrete 25mpa': '25MPa',
        'reinforced concrete 30mpa': '30MPa',
        'reinforced concrete 20mpa': '20MPa',
        'reinforced concrete 15mpa': '15MPa',
        'reinforced concrete 10mpa': '10MPa',
        '25mpa/19mm': '25MPa',
        '30mpa/19mm': '30MPa',
        '20mpa/19mm': '20MPa',
        '15mpa/19mm': '15MPa',
        '10mpa/19mm': '10MPa',
        'rough formwork': 'Rough Formwork Shutterboard - 18mm',
        'to sides footing': 'Rough Formwork Shutterboard - 18mm',
        'smooth formwork': 'Smooth Formwork Shutter - 114mm',
        'in surface bed': '25MPa',
        'in footing': '25MPa',
        'in apron': '25MPa',
        'under footings': '15MPa',
        'test cube': '25MPa',
        'expansion joint': '25MPa',
        'top of surface': '25MPa',
        'top of veranda': '25MPa',
        'top apron': '25MPa',
        'ref 100': 'Mesh Reinforcement - Ref 100',
        'ref 245': 'Mesh Reinforcement - Ref 245',
        'ref 395': 'Mesh Reinforcement - Ref 395',
        'ref 617': 'Mesh Reinforcement - Ref 617',
        'ref 888': 'Mesh Reinforcement - Ref 888',
        'high-tensile welded mesh': 'Mesh Reinforcement - Ref 395',
        'welded mesh': 'Mesh Reinforcement - Ref 395',
        'steel bars': 'Rebar Reinforcement - High Tensile Y12',
        'high-tensile': 'Rebar Reinforcement - High Tensile Y12',
        'mild steel': 'Rebar Reinforcement - Mild Tensile Steel R8',
        # Masonry — item descriptions
        'half brick wall': 'Half Brick - Class II',
        'half brick': 'Half Brick - Class II',
        'one brick wall': 'One Brick - Class II',
        'one brick': 'One Brick - Class II',
        'pier brick wall': 'One Brick - Class II',
        'pier brick': 'One Brick - Class II',
        'maxi brick': 'Maxi Brick - Class II',
        'beamfilling': 'One Brick - Class II',
        'face brickwork': 'Half Brick - Class II',
        'brick on edge': 'Brick Copings',
        'window sill': 'Brick Sills',
        'brick lintels': 'Brick Lintels',
        'brick copings': 'Brick Copings',
        'brick sills': 'Brick Sills',
        'precast concrete lintel': 'Precast Lintels',
        'prestressed fabricated concrete lintel': 'Precast Lintels',
        'turning piece': 'Turning Piece',
        'brick reinforcement': 'Mesh Reinforcement - Ref 395',
        'brickwork reinforcement': 'Mesh Reinforcement - Ref 395',
        'block work in 140': 'Block-M140',
        'blockwork 140': 'Block-M140',
        'block work in 90': 'Block-M90',
        'blockwork 90': 'Block-M90',
        'block lintel u140': 'Block-Lintel U140',
        'block lintel u90': 'Block-Lintel U90',
        # Waterproofing / DPC
        'damp proof course': 'Damp Course - DPC 150mm',
        'dpc embossed': 'Damp Course - DPC 150mm',
        '375 micron': 'Damp Proof Membrane - DPM 375Micron',
        '250 micron': 'Damp Proof Membrane - DPM 250Micron',
        'waterproof sheeting': 'Damp Proof Membrane - DPM 250Micron',
        # Roofing
        'ibr sheeting': 'Roof Sheeting - IBR 0.5mm',
        'corrugated sheeting': 'Roof Sheeting - Corrugated 0.5mm',
        'roof cover': 'Roof Sheeting - IBR 0.5mm',
        'profiled metal sheeting': 'Roof Sheeting - IBR 0.5mm',
        'roof insulation': 'Roof Insulation - 135mm',
        'insulation blanket': 'Roof Insulation - 135mm',
        'ridge capping': 'Ridge Capping',
        'ridge cap': 'Ridge Capping',
        'flashing': 'Roof Flashing - Aluminium',
        # Carpentry & Joinery
        'roof truss': 'Timber Roof Truss',
        'timber truss': 'Timber Roof Truss',
        'batten': 'Timber Battens - 38x38mm',
        'fascia board': 'Timber Fascia Board',
        'fascia': 'Timber Fascia Board',
        'wooden door': 'Hollow Core Door',
        'hollow core': 'Hollow Core Door',
        'solid timber door': 'Hollow Core Door',
        'door frame': 'Door Frame - Hardwood',
        'skirting': 'Timber Fascia Board',
        'cornice': 'Gypsum Ceiling Board - 9.5mm',
        # Ceilings & Partitions
        'gypsum ceiling board': 'Gypsum Ceiling Board - 9.5mm',
        'ceiling board': 'Gypsum Ceiling Board - 9.5mm',
        'nailed up ceiling': 'Gypsum Ceiling Board - 9.5mm',
        'suspended ceiling': 'Suspended Ceiling Grid',
        'dry wall': 'Dry Wall Partition - 100mm',
        'partition': 'Dry Wall Partition - 100mm',
        # Structural Steelwork
        'structural steel': 'Steel IPE Beams',
        'steel section': 'Steel Angles',
        'ipe beam': 'Steel IPE Beams',
        'steel angle': 'Steel Angles',
        'steel channel': 'Steel Channels',
        # Metalwork
        'pressed steel door frame': 'Steel Door Frame',
        'steel door frame': 'Steel Door Frame',
        'steel window': 'Steel Window Frame',
        'galvanised steel window': 'Steel Window Frame',
        'burglar bar': 'Burglar Bars',
        'security bar': 'Burglar Bars',
        'balustrade': 'Balustrade - Mild Steel',
        'handrail': 'Balustrade - Mild Steel',
        # Floor Coverings
        'ceramic floor': 'Ceramic Floor Tiles - 300x300',
        'floor tile': 'Ceramic Floor Tiles - 300x300',
        'porcelain tile': 'Porcelain Floor Tiles - 600x600',
        'vinyl sheet': 'Vinyl Sheet Flooring',
        'vinyl floor': 'Vinyl Sheet Flooring',
        'floorworx': 'Vinyl Sheet Flooring',
        'carpet': 'Carpet Tiles',
        # Plastering
        'internal plaster': 'Plaster Coat - 12mm Internal',
        'plaster internal': 'Plaster Coat - 12mm Internal',
        'cement plaster  rendering': 'Plaster Coat - 12mm Internal',
        'external plaster': 'Plaster Coat - 15mm External',
        'plaster external': 'Plaster Coat - 15mm External',
        'screed': 'Plaster Screed - 40mm',
        'granolithic': 'Plaster Screed - 40mm',
        # Plumbing & Drainage
        'copper pipe': 'Copper Pipe - 15mm',
        'waste pipe': 'PVC Waste Pipe - 50mm',
        'pvc pipe': 'PVC Waste Pipe - 50mm',
        'gutter': 'PVC Waste Pipe - 50mm',
        'downpipe': 'PVC Waste Pipe - 50mm',
        'rainwater': 'PVC Waste Pipe - 50mm',
        'wash basin': 'Wash Basin - Pedestal',
        'geyser': 'Geyser - 150L',
        'water heater': 'Geyser - 150L',
        # Glazing
        '4mm clear float': 'Float Glass - 4mm',
        '6mm clear float': 'Float Glass - 6mm',
        'float glass 4': 'Float Glass - 4mm',
        'float glass 6': 'Float Glass - 6mm',
        'laminated safety': 'Laminated Safety Glass - 6.38mm',
        'glazing to steel': 'Float Glass - 4mm',
        'glazing': 'Float Glass - 4mm',
        'aluminium window': 'Aluminium Window - Standard',
        # Ironmongery
        'hinge': 'Butt Hinges - 100mm',
        'barrel bolt': 'Butt Hinges - 100mm',
        'lockset': 'Cylinder Lock - 3 Lever',
        'mortice lock': 'Cylinder Lock - 3 Lever',
        'lock': 'Cylinder Lock - 3 Lever',
        'pull door handle': 'Lever Handle Set',
        'handle': 'Lever Handle Set',
        'push plate': 'Lever Handle Set',
        'kick plate': 'Lever Handle Set',
        'door closer': 'Door Closer - Hydraulic',
        'door stopper': 'Door Closer - Hydraulic',
        # Paintwork
        'pva acrylic': 'PVA Internal Paint - 2 Coats',
        'pva paint': 'PVA Internal Paint - 2 Coats',
        'internal paint': 'PVA Internal Paint - 2 Coats',
        'acrylic pva': 'PVA Internal Paint - 2 Coats',
        'plastic pva': 'PVA Internal Paint - 2 Coats',
        'floated plaster surfaces': 'PVA Internal Paint - 2 Coats',
        'fibre-cement board surface': 'PVA Internal Paint - 2 Coats',
        'acrylic paint': 'Acrylic External Paint - 2 Coats',
        'external paint': 'Acrylic External Paint - 2 Coats',
        'enamel paint': 'Enamel Paint on Metalwork',
        'on metal surface': 'Enamel Paint on Metalwork',
        'varnish': 'Wood Varnish - 2 Coats',
        'on wood surface': 'Wood Varnish - 2 Coats',
        # Electrical
        'conduit': 'PVC Conduit - 20mm',
        'cable': 'Cable - 2.5mm Twin & Earth',
        'wiring': 'Cable - 2.5mm Twin & Earth',
        'copper earth': 'Cable - 2.5mm Twin & Earth',
        'earth rod': 'Cable - 2.5mm Twin & Earth',
        'earth bar': 'Cable - 2.5mm Twin & Earth',
        'cadweld': 'Cable - 2.5mm Twin & Earth',
        'socket outlet': 'PVC Conduit - 20mm',
        'isolator': 'Distribution Board - 20A',
        'luminaire': 'LED Light Fitting - 4ft',
        'led lamp': 'LED Light Fitting - 4ft',
        'light fitting': 'LED Light Fitting - 4ft',
        'light switch': 'LED Light Fitting - 4ft',
        'photo cell': 'LED Light Fitting - 4ft',
        'bulkhead fitting': 'LED Light Fitting - 4ft',
        'distribution board': 'Distribution Board - 20A',
        'db board': 'Distribution Board - 20A',
        'circuit breaker': 'Distribution Board - 20A',
        'main switch': 'Distribution Board - 20A',
        'danger sign': 'Distribution Board - 20A',
        # Tiling
        'wall tile': 'Ceramic Wall Tiles - 200x300',
        # External
        'paving': 'Concrete Paving - 50mm',
        'palisade': 'Palisade Fencing - 1.8m',
        'fencing': 'Palisade Fencing - 1.8m',
        'fence': 'Palisade Fencing - 1.8m',
        'kerb': 'Concrete Kerbing - Fig 10',
        'curb': 'Concrete Kerbing - Fig 10',
        'grass': 'Kikuyu Grass',
        'landscap': 'Kikuyu Grass',
        # Precast
        'precast lintel': 'Precast Lintels',
        'prestressed fabricated concrete lintel': 'Precast Lintels',
        'precast sill': 'Precast Sills',
    }

    def _match_spec_in_text(self, text, specs):
        """Find the best matching specification name in a header description."""
        if not text:
            return None
        text_upper = text.upper().strip()

        # Sort specs by name length descending so longer names match first
        for spec in sorted(specs, key=lambda s: len(s.name), reverse=True):
            spec_name = spec.name
            if spec_name.upper() in text_upper:
                return spec
            if '/' in text_upper:
                for part in text_upper.split():
                    clean = part.split('/')[0]
                    if clean == spec_name.upper():
                        return spec

        # Keyword-based fallback matching
        text_lower = text.lower().strip()
        # Build a name→spec lookup from the current section-filtered specs
        spec_by_name = {s.name: s for s in specs}
        for keyword, spec_name in self.HEADER_TO_SPEC.items():
            if keyword in text_lower:
                match = spec_by_name.get(spec_name)
                if match:
                    return match

        return None

    def _match_labour_in_text(self, text, labour_specs):
        """Find the best matching labour specification in a header description."""
        if not text:
            return None
        text_upper = text.upper().strip()

        for ls in sorted(labour_specs, key=lambda s: len(s.name), reverse=True):
            if ls.name.upper() in text_upper:
                return ls

        # Keyword-based fallback matching
        keyword_map = {
            # Concrete & Formwork
            'blinding layer': 'Blinding Layer',
            'reinforced concrete': 'Concrete Ready Mix',
            'concrete in': 'Concrete Ready Mix',
            'formwork': None,  # handled by specific formwork types
            'rough formwork': 'Formwork - Foundations',
            'smooth formwork': 'Formwork - Sides',
            'formwork to sides': 'Formwork - Sides',
            'formwork to soffit': 'Formwork - Soffits',
            'steel bars': 'Rebar Reinforcement',
            'high-tensile welded mesh': 'Mesh Reinforcement',
            'welded mesh': 'Mesh Reinforcement',
            'unformed surface': 'Concrete Finishes',
            'wooden-floated': 'Concrete Finishes',
            'movement joint': 'Concrete Joints',
            'expansion joint': 'Concrete Joints',
            'site preparation': 'Excavations - Site Preparation',
            'restricted excavation': 'Excavations - Manual Trenches',
            'intermediate excavation': 'Excavations - Manual Intermediate Rock',
            'hard rock excavation': 'Excavations - Manual Hard Rock',
            'soil poisoning': 'Soil Poisoning',
            'soil insecticide': 'Soil Poisoning',
            'test cube': 'Concrete Sundries',
            'edge to': 'Concrete Edges',
            # Masonry
            'half brick': 'Brickwork - Half Brick',
            'one brick': 'Brickwork - One Brick',
            'block work in 140': 'Blockwork - 140mm',
            'blockwork 140': 'Blockwork - 140mm',
            'block work in 90': 'Blockwork - 90mm',
            'blockwork 90': 'Blockwork - 90mm',
            'damp proof course': 'Damp Proof Course',
            'dpc': 'Damp Proof Course',
            # Roofing
            'roof sheeting': 'Roof Sheeting',
            'roof covering': 'Roof Sheeting',
            'ibr sheeting': 'Roof Sheeting',
            'corrugated sheeting': 'Roof Sheeting',
            'roof insulation': 'Roof Insulation',
            'insulation blanket': 'Roof Insulation',
            'ridge capping': 'Ridge & Flashing',
            'flashing': 'Ridge & Flashing',
            # Carpentry & Joinery
            'roof truss': 'Roof Trusses',
            'timber truss': 'Roof Trusses',
            'batten': 'Timber Battens',
            'door hang': 'Door Hanging',
            'door frame': 'Door Frame Installation',
            'door leaf': 'Door Hanging',
            # Ceilings & Partitions
            'ceiling board': 'Ceiling Boarding',
            'gypsum ceiling': 'Ceiling Boarding',
            'suspended ceiling': 'Suspended Ceiling',
            'dry wall': 'Dry Wall Partitions',
            'partition': 'Dry Wall Partitions',
            # Structural Steelwork
            'structural steel': 'Steel Erection',
            'steel section': 'Steel Erection',
            'steel erect': 'Steel Erection',
            'bolt connection': 'Steel Connections',
            # Metalwork
            'steel door frame': 'Steel Frame Installation',
            'steel window': 'Steel Frame Installation',
            'burglar bar': 'Burglar Bar Installation',
            'security bar': 'Burglar Bar Installation',
            'balustrade': 'Balustrade Installation',
            'handrail': 'Balustrade Installation',
            # Floor Coverings
            'floor tile': 'Floor Tiling',
            'ceramic tile': 'Floor Tiling',
            'porcelain tile': 'Floor Tiling',
            'vinyl floor': 'Vinyl Flooring',
            'vinyl sheet': 'Vinyl Flooring',
            'carpet': 'Carpet Laying',
            # Plastering
            'internal plaster': 'Internal Plastering',
            'plaster internal': 'Internal Plastering',
            'external plaster': 'External Plastering',
            'plaster external': 'External Plastering',
            'screed': 'Floor Screeding',
            # Plumbing & Drainage
            'pipe': 'Pipe Installation',
            'waste pipe': 'Pipe Installation',
            'water pipe': 'Pipe Installation',
            'basin': 'Sanitary Fittings',
            'toilet': 'Sanitary Fittings',
            'w.c.': 'Sanitary Fittings',
            'bath': 'Sanitary Fittings',
            'shower': 'Sanitary Fittings',
            'geyser': 'Geyser Installation',
            'water heater': 'Geyser Installation',
            # Glazing
            'glass': 'Glass Installation',
            'glazing': 'Glass Installation',
            'aluminium window': 'Aluminium Window Fitting',
            # Ironmongery
            'ironmongery': 'Ironmongery Fitting',
            'hinge': 'Ironmongery Fitting',
            'lock': 'Ironmongery Fitting',
            'handle': 'Ironmongery Fitting',
            'door closer': 'Ironmongery Fitting',
            # Paintwork
            'internal paint': 'Internal Painting',
            'pva paint': 'Internal Painting',
            'external paint': 'External Painting',
            'acrylic paint': 'External Painting',
            'enamel': 'Metalwork Painting',
            'paint on metal': 'Metalwork Painting',
            'varnish': 'Timber Varnishing',
            # Electrical
            'conduit': 'Conduit Installation',
            'cable': 'Cable Installation',
            'wiring': 'Cable Installation',
            'light fitting': 'Light Fitting Installation',
            'luminaire': 'Light Fitting Installation',
            'distribution board': 'DB Board Installation',
            'db board': 'DB Board Installation',
            # Tiling
            'wall tile': 'Wall Tiling',
            # Waterproofing
            'waterproof': 'Waterproofing Membrane',
            'torch on': 'Waterproofing Membrane',
            # External
            'paving': 'Paving',
            'pave': 'Paving',
            'fencing': 'Fencing',
            'fence': 'Fencing',
            'palisade': 'Fencing',
            'landscap': 'Landscaping',
            'grass': 'Landscaping',
            'kerb': 'Kerbing',
            'curb': 'Kerbing',
            # Precast
            'precast': 'Precast Element Installation',
            'lintel': 'Precast Element Installation',
        }

        text_lower = text.lower().strip()
        for keyword, ls_name in keyword_map.items():
            if keyword in text_lower:
                if ls_name is None:
                    continue
                match = next((ls for ls in labour_specs if ls.name == ls_name), None)
                if match:
                    return match

        return None

    def _print_stats(self, stats):
        for field, count in stats.items():
            self.stdout.write(f'  {field}: {count} populated')
