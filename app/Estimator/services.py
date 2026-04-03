from app.Estimator.models import (
    ProjectLabourCrew,
    ProjectLabourSpecification,
    ProjectMaterial,
    ProjectSpecification,
    ProjectSpecificationComponent,
    ProjectTradeCode,
    SystemLabourCrew,
    SystemLabourSpecification,
    SystemMaterial,
    SystemSpecification,
    SystemTradeCode,
)


def initialize_project_estimator(project):
    """Clone all System* library records into Project* tables for a project.

    Skips if the project already has Project* records (idempotent guard).
    Returns a dict of counts per entity type.
    """
    if ProjectMaterial.objects.filter(project=project).exists():
        return {'status': 'already_initialized'}

    results = {}

    # ── Trade Codes ──
    tc_map = {}
    for stc in SystemTradeCode.objects.all():
        ptc = ProjectTradeCode.objects.create(
            project=project, source=stc,
            prefix=stc.prefix, trade_name=stc.trade_name,
        )
        tc_map[stc.pk] = ptc
    results['trade_codes'] = len(tc_map)

    # ── Materials ──
    mat_map = {}
    for sm in SystemMaterial.objects.all():
        pm = ProjectMaterial.objects.create(
            project=project, source=sm,
            trade_name=sm.trade_name, material_code=sm.material_code,
            unit=sm.unit, market_rate=sm.market_rate,
            material_variety=sm.material_variety, market_spec=sm.market_spec,
        )
        mat_map[sm.pk] = pm
    results['materials'] = len(mat_map)

    # ── Labour Crews ──
    crew_map = {}
    for slc in SystemLabourCrew.objects.all():
        plc = ProjectLabourCrew.objects.create(
            project=project, source=slc,
            crew_type=slc.crew_type, crew_size=slc.crew_size,
            skilled=slc.skilled, semi_skilled=slc.semi_skilled, general=slc.general,
            daily_production=slc.daily_production,
            skilled_rate=slc.skilled_rate, semi_skilled_rate=slc.semi_skilled_rate,
            general_rate=slc.general_rate,
        )
        crew_map[slc.pk] = plc
    results['labour_crews'] = len(crew_map)

    # ── Labour Specifications ──
    lspec_count = 0
    for sls in SystemLabourSpecification.objects.all():
        ProjectLabourSpecification.objects.create(
            project=project, source=sls,
            section=sls.section, trade_name=sls.trade_name,
            name=sls.name, unit=sls.unit,
            crew=crew_map.get(sls.crew_id) if sls.crew_id else None,
            daily_production=sls.daily_production,
            team_mix=sls.team_mix, site_factor=sls.site_factor,
            tools_factor=sls.tools_factor, leadership_factor=sls.leadership_factor,
        )
        lspec_count += 1
    results['labour_specs'] = lspec_count

    # ── Specifications (from SystemSpecification records) ──
    spec_count = 0
    for ss in SystemSpecification.objects.select_related('trade_code').prefetch_related('spec_components'):
        ps = ProjectSpecification.objects.create(
            project=project,
            source=ss.system_spec if hasattr(ss, 'system_spec') and ss.system_spec else None,
            section=ss.section,
            trade_code=tc_map.get(ss.trade_code_id) if ss.trade_code_id else None,
            unit_label=ss.unit_label,
            name=ss.name,
        )
        for comp in ss.spec_components.all():
            ProjectSpecificationComponent.objects.create(
                specification=ps,
                material=mat_map.get(comp.material_id) if comp.material_id else None,
                label=comp.label,
                qty_per_unit=comp.qty_per_unit,
                sort_order=comp.sort_order,
            )
        spec_count += 1
    results['specifications'] = spec_count

    results['status'] = 'initialized'
    return results


def pull_from_library(project):
    """Overwrite project values with current system library values.

    Updates all Project* records that have a source FK, syncing field values
    from the corresponding System* record. Does NOT delete project-only records
    that have no system source.
    Returns a dict of counts per entity type.
    """
    results = {}

    # ── Trade Codes ──
    count = 0
    for ptc in ProjectTradeCode.objects.filter(project=project, source__isnull=False).select_related('source'):
        ptc.prefix = ptc.source.prefix
        ptc.trade_name = ptc.source.trade_name
        ptc.save()
        count += 1
    results['trade_codes'] = count

    # ── Materials ──
    count = 0
    for pm in ProjectMaterial.objects.filter(project=project, source__isnull=False).select_related('source'):
        pm.trade_name = pm.source.trade_name
        pm.unit = pm.source.unit
        pm.market_rate = pm.source.market_rate
        pm.material_variety = pm.source.material_variety
        pm.market_spec = pm.source.market_spec
        pm.save()
        count += 1
    results['materials'] = count

    # ── Labour Crews ──
    count = 0
    for plc in ProjectLabourCrew.objects.filter(project=project, source__isnull=False).select_related('source'):
        plc.crew_type = plc.source.crew_type
        plc.crew_size = plc.source.crew_size
        plc.skilled = plc.source.skilled
        plc.semi_skilled = plc.source.semi_skilled
        plc.general = plc.source.general
        plc.daily_production = plc.source.daily_production
        plc.skilled_rate = plc.source.skilled_rate
        plc.semi_skilled_rate = plc.source.semi_skilled_rate
        plc.general_rate = plc.source.general_rate
        plc.save()
        count += 1
    results['labour_crews'] = count

    # ── Labour Specifications ──
    count = 0
    for pls in ProjectLabourSpecification.objects.filter(
        project=project, source__isnull=False
    ).select_related('source'):
        pls.section = pls.source.section
        pls.trade_name = pls.source.trade_name
        pls.name = pls.source.name
        pls.unit = pls.source.unit
        pls.daily_production = pls.source.daily_production
        pls.team_mix = pls.source.team_mix
        pls.site_factor = pls.source.site_factor
        pls.tools_factor = pls.source.tools_factor
        pls.leadership_factor = pls.source.leadership_factor
        # Re-link crew by matching crew_type
        if pls.source.crew:
            pls.crew = ProjectLabourCrew.objects.filter(
                project=project, crew_type=pls.source.crew.crew_type
            ).first()
        pls.save()
        count += 1
    results['labour_specs'] = count

    # ── Specifications (sync components from SystemMaterialSpec source) ──
    count = 0
    for ps in ProjectSpecification.objects.filter(
        project=project, source__isnull=False
    ).select_related('source'):
        ps.name = ps.source.name
        ps.unit_label = ps.source.unit
        ps.save()
        # Rebuild components from system spec
        ps.spec_components.all().delete()
        for comp in ps.source.system_spec_components.all():
            mat = None
            if comp.material_id:
                mat = ProjectMaterial.objects.filter(
                    project=project, source_id=comp.material_id
                ).first()
            ProjectSpecificationComponent.objects.create(
                specification=ps, material=mat,
                label=comp.label, qty_per_unit=comp.qty_per_unit,
                sort_order=comp.sort_order,
            )
        count += 1
    results['specifications'] = count

    return results
