"""
Individual sheet importers for each data tab.

Each importer handles a single Excel file upload using update_or_create
(safe for re-uploads) rather than delete-all-then-create.

Sheet matching is fuzzy: case-insensitive substring search across multiple
keyword variants (plural/singular, abbreviations, US/UK spelling).
Falls back to the active sheet when no keyword matches — so single-sheet
uploads just work.

Each importer accepts an optional `project` parameter:
- When project is set: creates/updates Project* models scoped to that project
- When project is None: creates/updates System* models (library/admin mode)
"""
from decimal import Decimal, InvalidOperation

import openpyxl

from .models import (
    SystemTradeCode, SystemMaterial, SystemSpecification, SystemSpecificationComponent,
    SystemLabourCrew, SystemLabourSpecification,
    ProjectTradeCode, ProjectMaterial, ProjectSpecification, ProjectSpecificationComponent,
    ProjectLabourCrew, ProjectLabourSpecification,
)


def _find_sheet(wb, keywords):
    """Find a worksheet by fuzzy name matching."""
    for name in wb.sheetnames:
        normalised = name.lower().strip()
        for kw in keywords:
            if kw in normalised:
                return wb[name]
    return wb.active


def _safe_decimal(value):
    if value is None:
        return None
    if isinstance(value, str) and (value.startswith('#') or not value.strip()):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _safe_str(value):
    if value is None:
        return ''
    s = str(value).strip()
    if s.startswith('#'):
        return ''
    return s


# ── Trade Codes ──────────────────────────────────────────────────

class TradeCodeImporter:
    """Import Trade Codes from Excel.

    Expected columns: Prefix | Trade Name
    """
    SHEET_KEYWORDS = [
        'trade code', 'trade codes', 'tradecode', 'tradecodes',
    ]

    def __init__(self, path, project=None):
        self.path = path
        self.project = project

    def run(self):
        wb = openpyxl.load_workbook(self.path, data_only=True)
        ws = _find_sheet(wb, self.SHEET_KEYWORDS)
        created = updated = skipped = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            prefix = _safe_str(row[0]) if len(row) > 0 else ''
            trade_name = _safe_str(row[1]) if len(row) > 1 else ''
            if not prefix:
                skipped += 1
                continue

            if self.project:
                _, is_new = ProjectTradeCode.objects.update_or_create(
                    project=self.project, prefix=prefix,
                    defaults={'trade_name': trade_name},
                )
            else:
                _, is_new = SystemTradeCode.objects.update_or_create(
                    prefix=prefix,
                    defaults={'trade_name': trade_name},
                )
            if is_new:
                created += 1
            else:
                updated += 1
        return {'created': created, 'updated': updated, 'skipped': skipped}


# ── Material Costs ───────────────────────────────────────────────

class MaterialCostImporter:
    """Import Material costs from Excel.

    Expected columns: Trade Name | Material Code | Unit | Market Rate | Variety | Spec
    """
    SHEET_KEYWORDS = [
        'material cost', 'material costs', 'materialcost', 'materialcosts',
        'mat cost', 'mat costs',
        'materials code', 'material code',
    ]

    def __init__(self, file_path, project=None):
        self.file_path = file_path
        self.project = project

    def run(self):
        wb = openpyxl.load_workbook(self.file_path, data_only=True)
        ws = _find_sheet(wb, self.SHEET_KEYWORDS)
        created = updated = 0

        for row in ws.iter_rows(min_row=2, values_only=True):
            ncols = len(row) if row else 0
            trade_name = _safe_str(row[0]) if ncols > 0 else ''
            mat_code = _safe_str(row[1]) if ncols > 1 else ''
            unit = _safe_str(row[2]) if ncols > 2 else ''
            rate = row[3] if ncols > 3 else None
            variety = _safe_str(row[4]) if ncols > 4 else ''
            spec = _safe_str(row[5]) if ncols > 5 else ''

            if not mat_code:
                continue

            defaults = {
                'trade_name': trade_name,
                'unit': unit,
                'market_rate': _safe_decimal(rate) or Decimal('0'),
                'material_variety': variety,
                'market_spec': spec,
            }

            if self.project:
                _, was_created = ProjectMaterial.objects.update_or_create(
                    project=self.project, material_code=mat_code,
                    defaults=defaults,
                )
            else:
                _, was_created = SystemMaterial.objects.update_or_create(
                    material_code=mat_code,
                    defaults=defaults,
                )
            if was_created:
                created += 1
            else:
                updated += 1

        wb.close()
        return {'created': created, 'updated': updated}


# ── Labour Costs ─────────────────────────────────────────────────

class LabourCostImporter:
    """Import Labour Crew costs from Excel.

    Supports TWO layouts:
    - Offset layout (from Complete_Upload): data starts row 3, cols offset by 1
    - Simple layout (from template): data starts row 2, no offset

    Auto-detects by checking if row 2 col B contains "Crew Type".
    """
    SHEET_KEYWORDS = [
        'labour cost', 'labour costs', 'labourcost', 'labourcosts',
        'labor cost', 'labor costs',
        'crew cost', 'crew costs', 'crew',
    ]

    def __init__(self, file_path, project=None):
        self.file_path = file_path
        self.project = project

    def run(self):
        wb = openpyxl.load_workbook(self.file_path, data_only=True)
        ws = _find_sheet(wb, self.SHEET_KEYWORDS)
        created = updated = 0

        row2_b = _safe_str(ws.cell(row=2, column=2).value).lower()
        is_offset = 'crew type' in row2_b

        data_start = 3 if is_offset else 2
        col_offset = 1 if is_offset else 0

        for row in ws.iter_rows(min_row=data_start, values_only=True):
            ncols = len(row) if row else 0
            c = col_offset
            crew_type = _safe_str(row[0 + c]) if ncols > c else ''
            if not crew_type:
                continue

            rate_base = 8 if is_offset else 5
            defaults = {
                'crew_size': int(row[1 + c] or 0) if ncols > 1 + c else 0,
                'skilled': int(row[2 + c] or 0) if ncols > 2 + c else 0,
                'semi_skilled': int(row[3 + c] or 0) if ncols > 3 + c else 0,
                'general': int(row[4 + c] or 0) if ncols > 4 + c else 0,
                'skilled_rate': _safe_decimal(row[rate_base]) or Decimal('0') if ncols > rate_base else Decimal('0'),
                'semi_skilled_rate': _safe_decimal(row[rate_base + 1]) or Decimal('0') if ncols > rate_base + 1 else Decimal('0'),
                'general_rate': _safe_decimal(row[rate_base + 2]) or Decimal('0') if ncols > rate_base + 2 else Decimal('0'),
            }

            if self.project:
                _, was_created = ProjectLabourCrew.objects.update_or_create(
                    project=self.project, crew_type=crew_type,
                    defaults=defaults,
                )
            else:
                _, was_created = SystemLabourCrew.objects.update_or_create(
                    crew_type=crew_type,
                    defaults=defaults,
                )
            if was_created:
                created += 1
            else:
                updated += 1

        wb.close()
        return {'created': created, 'updated': updated}


# ── Material Specifications ──────────────────────────────────────

class MaterialSpecImporter:
    """Import Material Specifications from Excel.

    Supports wide format and multi-row format. Auto-detects.
    """
    SHEET_KEYWORDS = [
        'material spec', 'material specs', 'material specification', 'material specifications',
        'materialspec', 'materialspecs',
        'mat spec', 'mat specs',
        'specification code', 'spec code',
    ]

    def __init__(self, file_path, project=None):
        self.file_path = file_path
        self.project = project

    def _get_trade_code(self, prefix_str):
        """Resolve trade code by prefix, using project or system models."""
        if not prefix_str:
            return None
        if self.project:
            return ProjectTradeCode.objects.filter(
                project=self.project, prefix=prefix_str
            ).first()
        tc = SystemTradeCode.objects.filter(prefix=prefix_str).first()
        if not tc:
            for stc in SystemTradeCode.objects.all():
                if stc.trade_code == prefix_str:
                    return stc
        return tc

    def _get_material(self, mat_code):
        """Resolve material by code, using project or system models."""
        if not mat_code:
            return None
        if self.project:
            return ProjectMaterial.objects.filter(
                project=self.project, material_code=mat_code
            ).first()
        return SystemMaterial.objects.filter(material_code=mat_code).first()

    def run(self):
        wb = openpyxl.load_workbook(self.file_path, data_only=True)
        ws = _find_sheet(wb, self.SHEET_KEYWORDS)

        row3_vals = [c.value for c in ws[3]] if ws.max_row >= 3 else []
        is_wide = any('specification code' in _safe_str(v).lower() for v in row3_vals)

        if is_wide:
            return self._import_wide(ws)
        return self._import_multirow(ws)

    def _import_wide(self, ws):
        created = updated = 0

        for row in ws.iter_rows(min_row=4, values_only=True):
            ncols = len(row) if row else 0
            if ncols < 4:
                continue

            section = _safe_str(row[0])
            trade_code_str = _safe_str(row[1])
            unit = _safe_str(row[2]) or 'm3'
            spec_name = _safe_str(row[3])

            if not spec_name:
                continue

            trade_code = self._get_trade_code(trade_code_str)

            if self.project:
                spec, was_created = ProjectSpecification.objects.update_or_create(
                    project=self.project, name=spec_name,
                    defaults={'section': section, 'trade_code': trade_code, 'unit_label': unit},
                )
                if not was_created:
                    spec.spec_components.all().delete()
            else:
                spec, was_created = SystemSpecification.objects.update_or_create(
                    name=spec_name,
                    defaults={'section': section, 'trade_code': trade_code, 'unit_label': unit},
                )
                if not was_created:
                    spec.spec_components.all().delete()

            if was_created:
                created += 1
            else:
                updated += 1

            ComponentModel = ProjectSpecificationComponent if self.project else SystemSpecificationComponent
            for i in range(4):
                mat_col = 4 + i
                qty_col = 8 + i
                mat_code = _safe_str(row[mat_col]) if ncols > mat_col else ''
                qty = _safe_decimal(row[qty_col]) if ncols > qty_col else None

                if not mat_code:
                    continue

                mat = self._get_material(mat_code)
                ComponentModel.objects.create(
                    specification=spec,
                    material=mat,
                    label=mat_code,
                    qty_per_unit=qty or Decimal('0'),
                    sort_order=i,
                )

        return {'created': created, 'updated': updated}

    def _import_multirow(self, ws):
        specs_data: dict[str, dict] = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            ncols = len(row) if row else 0
            spec_name = _safe_str(row[0]) if ncols > 0 else ''
            if not spec_name:
                continue

            if spec_name not in specs_data:
                specs_data[spec_name] = {
                    'section': _safe_str(row[1]) if ncols > 1 else '',
                    'trade_code_prefix': _safe_str(row[2]) if ncols > 2 else '',
                    'unit': _safe_str(row[3]) if ncols > 3 else 'm3',
                    'components': [],
                }

            mat_code_str = _safe_str(row[4]) if ncols > 4 else ''
            if mat_code_str:
                specs_data[spec_name]['components'].append({
                    'material_code': mat_code_str,
                    'label': (_safe_str(row[5]) if ncols > 5 else '') or mat_code_str,
                    'qty_per_unit': (_safe_decimal(row[6]) if ncols > 6 else None) or Decimal('0'),
                })

        created = updated = 0

        for name, data in specs_data.items():
            trade_code = self._get_trade_code(data['trade_code_prefix'])

            if self.project:
                spec, was_created = ProjectSpecification.objects.update_or_create(
                    project=self.project, name=name,
                    defaults={'section': data['section'], 'trade_code': trade_code, 'unit_label': data['unit']},
                )
                if not was_created:
                    spec.spec_components.all().delete()
            else:
                spec, was_created = SystemSpecification.objects.update_or_create(
                    name=name,
                    defaults={'section': data['section'], 'trade_code': trade_code, 'unit_label': data['unit']},
                )
                if not was_created:
                    spec.spec_components.all().delete()

            if was_created:
                created += 1
            else:
                updated += 1

            ComponentModel = ProjectSpecificationComponent if self.project else SystemSpecificationComponent
            for i, comp in enumerate(data['components']):
                mat = self._get_material(comp['material_code'])
                ComponentModel.objects.create(
                    specification=spec,
                    material=mat,
                    label=comp['label'],
                    qty_per_unit=comp['qty_per_unit'],
                    sort_order=i,
                )

        return {'created': created, 'updated': updated}


# ── Labour Specifications ────────────────────────────────────────

class LabourSpecImporter:
    """Import Labour Specifications from Excel.

    Supports two-header and simple layouts. Auto-detects.
    """
    SHEET_KEYWORDS = [
        'labour spec', 'labour specs', 'labour specification', 'labour specifications',
        'labourspec', 'labourspecs',
        'labor spec', 'labor specs', 'labor specification', 'labor specifications',
    ]

    def __init__(self, file_path, project=None):
        self.file_path = file_path
        self.project = project

    def run(self):
        wb = openpyxl.load_workbook(self.file_path, data_only=True)
        ws = _find_sheet(wb, self.SHEET_KEYWORDS)
        created = updated = 0

        row1_vals = [_safe_str(c.value).lower() for c in ws[1]] if ws.max_row >= 1 else []
        has_group_header = any('productivity' in v for v in row1_vals)
        data_start = 3 if has_group_header else 2

        for row in ws.iter_rows(min_row=data_start, values_only=True):
            ncols = len(row) if row else 0
            name = _safe_str(row[2]) if ncols > 2 else ''
            if not name:
                continue

            crew_type_str = _safe_str(row[4]) if ncols > 4 else ''
            if self.project:
                crew = (
                    ProjectLabourCrew.objects.filter(
                        project=self.project, crew_type=crew_type_str
                    ).first() if crew_type_str else None
                )
            else:
                crew = (
                    SystemLabourCrew.objects.filter(crew_type=crew_type_str).first()
                    if crew_type_str else None
                )

            defaults = {
                'section': _safe_str(row[0]) if ncols > 0 else '',
                'trade_name': _safe_str(row[1]) if ncols > 1 else '',
                'unit': _safe_str(row[3]) if ncols > 3 else '',
                'crew': crew,
                'daily_production': (_safe_decimal(row[5]) if ncols > 5 else None) or Decimal('0'),
                'team_mix': (_safe_decimal(row[6]) if ncols > 6 else None) or Decimal('1'),
                'site_factor': (_safe_decimal(row[7]) if ncols > 7 else None) or Decimal('1'),
                'tools_factor': (_safe_decimal(row[8]) if ncols > 8 else None) or Decimal('1'),
                'leadership_factor': (_safe_decimal(row[9]) if ncols > 9 else None) or Decimal('1'),
            }

            if self.project:
                _, was_created = ProjectLabourSpecification.objects.update_or_create(
                    project=self.project, name=name,
                    defaults=defaults,
                )
            else:
                _, was_created = SystemLabourSpecification.objects.update_or_create(
                    name=name,
                    defaults=defaults,
                )
            if was_created:
                created += 1
            else:
                updated += 1

        wb.close()
        return {'created': created, 'updated': updated}
