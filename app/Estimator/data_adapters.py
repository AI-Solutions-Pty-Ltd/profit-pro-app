"""
Data adapters for the Project Resource Estimator.

Adapters convert data from various sources (Django ORM, Excel, raw dicts)
into a uniform format that can be passed to the calculation functions in
calculations.py.
"""

from decimal import Decimal


class DjangoORMAdapter:
    """
    Reads data from Django ORM models and returns plain dicts
    compatible with the calculation functions.
    """

    def __init__(self, project_id=None):
        self.project_id = project_id

    def get_trade_codes(self):
        from app.Estimator.models import ProjectTradeCode
        qs = ProjectTradeCode.objects.all()
        if self.project_id:
            qs = qs.filter(project_id=self.project_id)
        return [
            {
                'prefix': tc.prefix,
                'trade_name': tc.trade_name,
                'trade_code': tc.trade_code,
            }
            for tc in qs
        ]

    def get_materials(self):
        from app.Estimator.models import ProjectMaterial
        qs = ProjectMaterial.objects.all()
        if self.project_id:
            qs = qs.filter(project_id=self.project_id)
        return [
            {
                'trade_name': mat.trade_name,
                'material_code': mat.material_code,
                'unit': mat.unit,
                'market_rate': mat.market_rate,
                'material_variety': mat.material_variety,
                'market_spec': mat.market_spec,
            }
            for mat in qs
        ]

    def get_specifications(self):
        from app.Estimator.models import ProjectSpecification
        qs = ProjectSpecification.objects.select_related('trade_code').prefetch_related('spec_components__material')
        if self.project_id:
            qs = qs.filter(project_id=self.project_id)
        results = []
        for spec in qs:
            results.append({
                'section': spec.section,
                'trade_name': spec.trade_code.trade_code if spec.trade_code else '',
                'name': spec.name,
                'unit_label': spec.unit_label,
                'boq_quantity': spec.baseline_boq_quantity,
                'components': spec.components,
            })
        return results

    def get_labour_crews(self):
        from app.Estimator.models import ProjectLabourCrew
        qs = ProjectLabourCrew.objects.all()
        if self.project_id:
            qs = qs.filter(project_id=self.project_id)
        return [
            {
                'crew_type': crew.crew_type,
                'crew_size': crew.crew_size,
                'skilled': crew.skilled,
                'semi_skilled': crew.semi_skilled,
                'general': crew.general,
                'daily_production': crew.daily_production,
                'crew_daily_cost': crew.crew_daily_cost,
            }
            for crew in qs
        ]

    def get_labour_specifications(self):
        from app.Estimator.models import ProjectLabourSpecification
        qs = ProjectLabourSpecification.objects.select_related('crew')
        if self.project_id:
            qs = qs.filter(project_id=self.project_id)
        results = []
        for ls in qs:
            results.append({
                'section': ls.section,
                'trade_name': ls.trade_name,
                'name': ls.name,
                'unit': ls.unit,
                'crew_type': ls.crew.crew_type if ls.crew else '',
                'daily_production': ls.daily_production,
                'daily_output': ls.daily_output,
                'daily_cost': ls.daily_cost,
                'rate_per_unit': ls.rate_per_unit,
                'boq_quantity': ls.baseline_boq_quantity,
                'total_cost': ls.total_cost,
            })
        return results

    def get_boq_items(self, project_id=None):
        from app.Estimator.models import BOQItem
        pid = project_id or self.project_id
        qs = BOQItem.objects.select_related(
            'trade_code', 'specification', 'labour_specification',
            'labour_specification__crew', 'material',
        ).prefetch_related(
            'specification__spec_components__material',
        )

        if pid is not None:
            qs = qs.filter(project_id=pid)

        results = []
        for item in qs:
            spec_rate = None
            spec_name = ''
            if item.specification:
                spec_rate = item.specification.rate_per_unit
                spec_name = item.specification.name

            material_rate = item.material.market_rate if item.material else None

            labour_rate = None
            if item.labour_specification:
                labour_rate = item.labour_specification.rate_per_unit

            results.append({
                'section': item.section,
                'bill_no': item.bill_no,
                'trade_name': item.trade_code.trade_code if item.trade_code else '',
                'specification_name': spec_name,
                'item_no': item.item_no,
                'pay_ref': item.pay_ref,
                'description': item.description,
                'unit': item.unit,
                'contract_quantity': item.contract_quantity,
                'contract_rate': item.contract_rate,
                'progress_quantity': item.progress_quantity,
                'forecast_quantity': item.forecast_quantity,
                'rate_override': material_rate,
                'specification_rate': spec_rate,
                'labour_rate': labour_rate,
                'is_section_header': item.is_section_header,
            })
        return results
