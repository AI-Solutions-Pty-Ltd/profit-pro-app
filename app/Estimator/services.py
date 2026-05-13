from app.Estimator.models import (
    BOQItem,
    ContractorItemLibraryEntry,
    ContractorLabourCrew,
    ContractorLabourSpecification,
    ContractorMaterial,
    ContractorMaterialSpec,
    ContractorPlantCost,
    ContractorPlantSpecification,
    ContractorPlantSpecificationComponent,
    ContractorPreliminaryCost,
    ContractorPreliminarySpecification,
    ContractorSpecification,
    ContractorSpecificationComponent,
    ContractorTradeCode,
    ProjectItemLibraryEntry,
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
    SystemItemLibraryEntry,
    SystemLabourCrew,
    SystemLabourSpecification,
    SystemMaterial,
    SystemPlantCost,
    SystemPlantSpecification,
    SystemPreliminaryCost,
    SystemPreliminarySpecification,
    SystemSpecification,
    SystemTradeCode,
)


def initialize_project_estimator(project):
    """Clone all Contractor* library records into Project* tables for a project.

    The project must be linked to a contractor Company. Skips if the project
    already has Project* records (idempotent guard). Returns a dict of counts
    per entity type.
    """
    company = project.contractor
    if company is None:
        return {"status": "no_contractor_company"}

    if ProjectMaterial.objects.filter(project=project).exists():
        return {"status": "already_initialized"}

    results = {}

    # ── Trade Codes ──
    tc_map = {}
    for ctc in ContractorTradeCode.objects.filter(company=company):
        ptc = ProjectTradeCode.objects.create(
            project=project,
            prefix=ctc.prefix,
            trade_name=ctc.trade_name,
        )
        tc_map[ctc.pk] = ptc
    results["trade_codes"] = len(tc_map)

    # ── Materials ──
    mat_map = {}
    for cm in ContractorMaterial.objects.filter(company=company):
        pm = ProjectMaterial.objects.create(
            project=project,
            trade_name=cm.trade_name,
            material_code=cm.material_code,
            unit=cm.unit,
            pack_qty=cm.pack_qty,
            pack_cost=cm.pack_cost,
            material_variety=cm.material_variety,
            market_spec=cm.market_spec,
        )
        mat_map[cm.pk] = pm
    results["materials"] = len(mat_map)

    # ── Labour Crews ──
    crew_map = {}
    for clc in ContractorLabourCrew.objects.filter(company=company):
        plc = ProjectLabourCrew.objects.create(
            project=project,
            crew_type=clc.crew_type,
            crew_size=clc.crew_size,
            skilled=clc.skilled,
            semi_skilled=clc.semi_skilled,
            general=clc.general,
            daily_production=clc.daily_production,
            skilled_rate=clc.skilled_rate,
            semi_skilled_rate=clc.semi_skilled_rate,
            general_rate=clc.general_rate,
        )
        crew_map[clc.pk] = plc
    results["labour_crews"] = len(crew_map)

    # ── Labour Specifications ──
    lspec_map = {}
    for cls in ContractorLabourSpecification.objects.filter(company=company):
        pls = ProjectLabourSpecification.objects.create(
            project=project,
            section=cls.section,
            trade_name=cls.trade_name,
            name=cls.name,
            unit=cls.unit,
            crew=crew_map.get(getattr(cls, "crew_id", None))
            if getattr(cls, "crew_id", None)
            else None,
            daily_production=cls.daily_production,
            team_mix=cls.team_mix,
            site_factor=cls.site_factor,
            tools_factor=cls.tools_factor,
            leadership_factor=cls.leadership_factor,
        )
        lspec_map[cls.pk] = pls
    results["labour_specs"] = len(lspec_map)

    # ── Plant Costs ──
    plant_map = {}
    for cpc in ContractorPlantCost.objects.filter(company=company):
        ppc = ProjectPlantCost.objects.create(
            project=project,
            name=cpc.name,
            hourly_production=cpc.hourly_production,
            hourly_rate=cpc.hourly_rate,
        )
        plant_map[cpc.pk] = ppc
    results["plant_costs"] = len(plant_map)

    # ── Plant Specifications ──
    pspec_map = {}
    for cps in ContractorPlantSpecification.objects.filter(
        company=company
    ).prefetch_related("components"):
        pps = ProjectPlantSpecification.objects.create(
            project=project,
            section=cps.section,
            trade_name=cps.trade_name,
            name=cps.name,
            unit=cps.unit,
            daily_production=cps.daily_production,
            operator_factor=cps.operator_factor,
            site_factor=cps.site_factor,
        )
        for comp in cps.components.all():
            ProjectPlantSpecificationComponent.objects.create(
                specification=pps,
                plant_type=plant_map.get(getattr(comp, "plant_type_id", None))
                if getattr(comp, "plant_type_id", None)
                else None,
                hours=comp.hours,
                sort_order=comp.sort_order,
            )
        pspec_map[cps.pk] = pps
    results["plant_specs"] = len(pspec_map)

    # ── Preliminary Costs ──
    prelim_count = 0
    for cpc in ContractorPreliminaryCost.objects.filter(company=company):
        ProjectPreliminaryCost.objects.create(
            project=project,
            name=cpc.name,
            preliminary_type=cpc.preliminary_type,
            sum_value=cpc.sum_value,
            amount=cpc.amount,
            number_per_month=cpc.number_per_month,
            monthly_rate=cpc.monthly_rate,
            months=cpc.months,
        )
        prelim_count += 1
    results["preliminary_costs"] = prelim_count

    # ── Preliminary Specifications ──
    prelim_spec_map = {}
    for cps in ContractorPreliminarySpecification.objects.filter(company=company):
        pps = ProjectPreliminarySpecification.objects.create(
            project=project,
            section=cps.section,
            trade_name=cps.trade_name,
            name=cps.name,
            unit=cps.unit,
            preliminary_type=cps.preliminary_type,
        )
        prelim_spec_map[cps.pk] = pps
    results["preliminary_specs"] = len(prelim_spec_map)

    # ── Material Specifications (with components) ──
    spec_map = {}
    for cs in (
        ContractorSpecification.objects.filter(company=company)
        .select_related("trade_code")
        .prefetch_related("spec_components")
    ):
        ps = ProjectSpecification.objects.create(
            project=project,
            section=cs.section,
            trade_code=tc_map.get(getattr(cs, "trade_code_id", None))
            if getattr(cs, "trade_code_id", None)
            else None,
            unit_label=cs.unit_label,
            name=cs.name,
        )
        for comp in cs.spec_components.all():
            ProjectSpecificationComponent.objects.create(
                specification=ps,
                material=mat_map.get(getattr(comp, "material_id", None))
                if getattr(comp, "material_id", None)
                else None,
                label=comp.label,
                qty_per_unit=comp.qty_per_unit,
                sort_order=comp.sort_order,
            )
        spec_map[cs.pk] = ps
    results["specifications"] = len(spec_map)

    # ── Item Library Entries ──
    lib_count = 0
    for centry in ContractorItemLibraryEntry.objects.filter(
        company=company
    ).select_related(
        "trade_code", "material_spec", "labour_spec", "plant_spec", "preliminary_spec"
    ):
        ProjectItemLibraryEntry.objects.create(
            project=project,
            source_contractor=centry,
            trade_code=tc_map.get(centry.trade_code_id)
            if centry.trade_code_id
            else None,
            item_code=centry.item_code,
            accounts_code=centry.accounts_code,
            component=centry.component,
            description=centry.description,
            unit=centry.unit,
            material_spec=spec_map.get(centry.material_spec_id)
            if centry.material_spec_id
            else None,
            labour_spec=lspec_map.get(centry.labour_spec_id)
            if centry.labour_spec_id
            else None,
            plant_spec=pspec_map.get(centry.plant_spec_id)
            if centry.plant_spec_id
            else None,
            preliminary_spec=prelim_spec_map.get(centry.preliminary_spec_id)
            if centry.preliminary_spec_id
            else None,
            display_order=centry.display_order,
        )
        lib_count += 1
    results["item_library_entries"] = lib_count

    results["status"] = "initialized"
    return results


def clone_from_project(target_project, source_project):
    """Clone all Project* library records from source_project into target_project.

    Clears existing library data on target_project first (but NOT BOQItems).
    Returns a dict of counts per entity type.
    """
    # Clear existing library data on target (not BoQ items)
    ProjectItemLibraryEntry.objects.filter(project=target_project).delete()
    ProjectSpecificationComponent.objects.filter(
        specification__project=target_project
    ).delete()
    ProjectSpecification.objects.filter(project=target_project).delete()
    ProjectLabourSpecification.objects.filter(project=target_project).delete()
    ProjectLabourCrew.objects.filter(project=target_project).delete()
    ProjectMaterial.objects.filter(project=target_project).delete()
    ProjectTradeCode.objects.filter(project=target_project).delete()
    ProjectPlantSpecification.objects.filter(project=target_project).delete()
    ProjectPlantCost.objects.filter(project=target_project).delete()
    ProjectPreliminaryCost.objects.filter(project=target_project).delete()
    ProjectPreliminarySpecification.objects.filter(project=target_project).delete()

    results = {}

    # ── Trade Codes ──
    tc_map = {}
    for stc in ProjectTradeCode.objects.filter(project=source_project):
        ptc = ProjectTradeCode.objects.create(
            project=target_project,
            source=stc.source,
            prefix=stc.prefix,
            trade_name=stc.trade_name,
        )
        tc_map[stc.pk] = ptc
    results["trade_codes"] = len(tc_map)

    # ── Materials ──
    mat_map = {}
    for sm in ProjectMaterial.objects.filter(project=source_project):
        pm = ProjectMaterial.objects.create(
            project=target_project,
            source=sm.source,
            trade_name=sm.trade_name,
            material_code=sm.material_code,
            unit=sm.unit,
            pack_qty=sm.pack_qty,
            pack_cost=sm.pack_cost,
            material_variety=sm.material_variety,
            market_spec=sm.market_spec,
        )
        mat_map[sm.pk] = pm
    results["materials"] = len(mat_map)

    # ── Labour Crews ──
    crew_map = {}
    for slc in ProjectLabourCrew.objects.filter(project=source_project):
        plc = ProjectLabourCrew.objects.create(
            project=target_project,
            source=slc.source,
            crew_type=slc.crew_type,
            crew_size=slc.crew_size,
            skilled=slc.skilled,
            semi_skilled=slc.semi_skilled,
            general=slc.general,
            daily_production=slc.daily_production,
            skilled_rate=slc.skilled_rate,
            semi_skilled_rate=slc.semi_skilled_rate,
            general_rate=slc.general_rate,
        )
        crew_map[slc.pk] = plc
    results["labour_crews"] = len(crew_map)

    # ── Labour Specifications ──
    lspec_map = {}
    for sls in ProjectLabourSpecification.objects.filter(
        project=source_project
    ).select_related("crew"):
        pls = ProjectLabourSpecification.objects.create(
            project=target_project,
            source=sls.source,
            section=sls.section,
            trade_name=sls.trade_name,
            name=sls.name,
            unit=sls.unit,
            crew=crew_map.get(sls.crew_id) if sls.crew_id else None,  # ty:ignore[unresolved-attribute]
            daily_production=sls.daily_production,
            team_mix=sls.team_mix,
            site_factor=sls.site_factor,
            tools_factor=sls.tools_factor,
            leadership_factor=sls.leadership_factor,
        )
        lspec_map[sls.pk] = pls
    results["labour_specs"] = len(lspec_map)

    # ── Specifications + Components ──
    spec_map = {}
    for ss in ProjectSpecification.objects.filter(
        project=source_project
    ).prefetch_related("spec_components"):
        ps = ProjectSpecification.objects.create(
            project=target_project,
            source=ss.source,
            section=ss.section,
            trade_code=tc_map.get(getattr(ss, "trade_code_id", None))
            if getattr(ss, "trade_code_id", None)
            else None,
            unit_label=ss.unit_label,
            name=ss.name,
        )
        for comp in ss.spec_components.all():
            ProjectSpecificationComponent.objects.create(
                specification=ps,
                material=mat_map.get(getattr(comp, "material_id", None))
                if getattr(comp, "material_id", None)
                else None,
                label=comp.label,
                qty_per_unit=comp.qty_per_unit,
                sort_order=comp.sort_order,
            )
        spec_map[ss.pk] = ps
    results["specifications"] = len(spec_map)

    # ── Plant Costs ──
    plant_map = {}
    for spc in ProjectPlantCost.objects.filter(project=source_project):
        ppc = ProjectPlantCost.objects.create(
            project=target_project,
            source=spc.source,
            name=spc.name,
            hourly_production=spc.hourly_production,
            hourly_rate=spc.hourly_rate,
        )
        plant_map[spc.pk] = ppc
    results["plant_costs"] = len(plant_map)

    # ── Plant Specifications ──
    pspec_map = {}
    for sps in ProjectPlantSpecification.objects.filter(
        project=source_project
    ).prefetch_related("components"):
        pps = ProjectPlantSpecification.objects.create(
            project=target_project,
            source=sps.source,
            section=sps.section,
            trade_name=sps.trade_name,
            name=sps.name,
            unit=sps.unit,
            daily_production=sps.daily_production,
            operator_factor=sps.operator_factor,
            site_factor=sps.site_factor,
        )
        for comp in sps.components.all():
            ProjectPlantSpecificationComponent.objects.create(
                specification=pps,
                plant_type=plant_map.get(comp.plant_type_id)
                if comp.plant_type_id
                else None,  # ty:ignore[unresolved-attribute]
                hours=comp.hours,
                sort_order=comp.sort_order,
            )
        pspec_map[sps.pk] = pps
    results["plant_specs"] = len(pspec_map)

    # ── Preliminary Costs ──
    prelim_count = 0
    for spc in ProjectPreliminaryCost.objects.filter(project=source_project):
        ProjectPreliminaryCost.objects.create(
            project=target_project,
            source=spc.source,
            name=spc.name,
            preliminary_type=spc.preliminary_type,
            sum_value=spc.sum_value,
            amount=spc.amount,
            number_per_month=spc.number_per_month,
            monthly_rate=spc.monthly_rate,
            months=spc.months,
        )
        prelim_count += 1
    results["preliminary_costs"] = prelim_count

    # ── Preliminary Specifications ──
    prelim_spec_map = {}
    for sps in ProjectPreliminarySpecification.objects.filter(project=source_project):
        pps = ProjectPreliminarySpecification.objects.create(
            project=target_project,
            source=sps.source,
            section=sps.section,
            trade_name=sps.trade_name,
            name=sps.name,
            unit=sps.unit,
            preliminary_type=sps.preliminary_type,
        )
        prelim_spec_map[sps.pk] = pps
    results["preliminary_specs"] = len(prelim_spec_map)

    # ── Item Library Entries ──
    lib_count = 0
    for sentry in ProjectItemLibraryEntry.objects.filter(
        project=source_project
    ).select_related(
        "trade_code", "material_spec", "labour_spec", "plant_spec", "preliminary_spec"
    ):
        ProjectItemLibraryEntry.objects.create(
            project=target_project,
            source_system=sentry.source_system,
            source_contractor=sentry.source_contractor,
            trade_code=tc_map.get(sentry.trade_code_id)
            if sentry.trade_code_id
            else None,
            item_code=sentry.item_code,
            accounts_code=sentry.accounts_code,
            component=sentry.component,
            description=sentry.description,
            unit=sentry.unit,
            material_spec=spec_map.get(sentry.material_spec_id)
            if sentry.material_spec_id
            else None,
            labour_spec=lspec_map.get(sentry.labour_spec_id)
            if sentry.labour_spec_id
            else None,
            plant_spec=pspec_map.get(sentry.plant_spec_id)
            if sentry.plant_spec_id
            else None,
            preliminary_spec=prelim_spec_map.get(sentry.preliminary_spec_id)
            if sentry.preliminary_spec_id
            else None,
            display_order=sentry.display_order,
        )
        lib_count += 1
    results["item_library_entries"] = lib_count

    results["status"] = "cloned"
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
    for ptc in ProjectTradeCode.objects.filter(
        project=project, source__isnull=False
    ).select_related("source"):
        ptc.prefix = ptc.source.prefix
        ptc.trade_name = ptc.source.trade_name
        ptc.save()
        count += 1
    results["trade_codes"] = count

    # ── Materials ──
    count = 0
    for pm in ProjectMaterial.objects.filter(
        project=project, source__isnull=False
    ).select_related("source"):
        pm.trade_name = pm.source.trade_name
        pm.unit = pm.source.unit
        pm.pack_qty = pm.source.pack_qty
        pm.pack_cost = pm.source.pack_cost
        pm.material_variety = pm.source.material_variety
        pm.market_spec = pm.source.market_spec
        pm.save()
        count += 1
    results["materials"] = count

    # ── Labour Crews ──
    count = 0
    for plc in ProjectLabourCrew.objects.filter(
        project=project, source__isnull=False
    ).select_related("source"):
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
    results["labour_crews"] = count

    # ── Labour Specifications ──
    count = 0
    for pls in ProjectLabourSpecification.objects.filter(
        project=project, source__isnull=False
    ).select_related("source"):
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
    results["labour_specs"] = count

    # ── Specifications (sync components from SystemMaterialSpec source) ──
    count = 0
    for ps in ProjectSpecification.objects.filter(
        project=project, source__isnull=False
    ).select_related("source"):
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
                specification=ps,
                material=mat,
                label=comp.label,
                qty_per_unit=comp.qty_per_unit,
                sort_order=comp.sort_order,
            )
        count += 1
    results["specifications"] = count

    return results


def sync_materials_from_contractor(project):
    """Sync project material costs with the project's Contractor Library.

    The project must be linked to a contractor Company (project.contractor).
    Matches existing project rows by `material_code` and upserts.
    Returns count of updated + created rows.
    """
    company = project.contractor
    if company is None:
        return {"updated": 0, "created": 0, "skipped_no_contractor": True}

    created = updated = 0
    for cm in ContractorMaterial.objects.filter(company=company):
        defaults = {
            "trade_name": cm.trade_name,
            "unit": cm.unit,
            "pack_qty": cm.pack_qty,
            "pack_cost": cm.pack_cost,
            "material_variety": cm.material_variety,
            "market_spec": cm.market_spec,
        }
        _, was_created = ProjectMaterial.objects.update_or_create(
            project=project,
            material_code=cm.material_code,
            defaults=defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"updated": updated, "created": created}


def sync_labour_costs_from_contractor(project):
    """Sync project labour crews with the project's Contractor Library."""
    company = project.contractor
    if company is None:
        return {"updated": 0, "created": 0, "skipped_no_contractor": True}

    created = updated = 0
    for clc in ContractorLabourCrew.objects.filter(company=company):
        defaults = {
            "crew_size": clc.crew_size,
            "skilled": clc.skilled,
            "semi_skilled": clc.semi_skilled,
            "general": clc.general,
            "daily_production": clc.daily_production,
            "skilled_rate": clc.skilled_rate,
            "semi_skilled_rate": clc.semi_skilled_rate,
            "general_rate": clc.general_rate,
        }
        _, was_created = ProjectLabourCrew.objects.update_or_create(
            project=project,
            crew_type=clc.crew_type,
            defaults=defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"updated": updated, "created": created}


def sync_plant_costs_from_contractor(project):
    """Sync project plant costs with the project's Contractor Library."""
    company = project.contractor
    if company is None:
        return {"updated": 0, "created": 0, "skipped_no_contractor": True}

    created = updated = 0
    for cpc in ContractorPlantCost.objects.filter(company=company):
        defaults = {
            "hourly_production": cpc.hourly_production,
            "hourly_rate": cpc.hourly_rate,
        }
        _, was_created = ProjectPlantCost.objects.update_or_create(
            project=project,
            name=cpc.name,
            defaults=defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"updated": updated, "created": created}


def sync_preliminary_costs_from_contractor(project):
    """Sync project preliminary costs with the project's Contractor Library.

    Matched by (name, preliminary_type) since the same name can legitimately
    appear under different types.
    """
    company = project.contractor
    if company is None:
        return {"updated": 0, "created": 0, "skipped_no_contractor": True}

    created = updated = 0
    for cpc in ContractorPreliminaryCost.objects.filter(company=company):
        defaults = {
            "sum_value": cpc.sum_value,
            "amount": cpc.amount,
            "number_per_month": cpc.number_per_month,
            "monthly_rate": cpc.monthly_rate,
            "months": cpc.months,
        }
        _, was_created = ProjectPreliminaryCost.objects.update_or_create(
            project=project,
            name=cpc.name,
            preliminary_type=cpc.preliminary_type,
            defaults=defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"updated": updated, "created": created}


def _resolve_project_material(project, system_material):
    """Match a system material to the project copy by `source` FK, falling back
    to `material_code` for materials imported via Excel (which don't set
    source)."""
    if not system_material:
        return None
    return (
        ProjectMaterial.objects.filter(
            project=project, source_id=system_material.pk
        ).first()
        or ProjectMaterial.objects.filter(
            project=project, material_code=system_material.material_code
        ).first()
    )


def _resolve_project_trade_code(project, system_trade_code):
    if not system_trade_code:
        return None
    return ProjectTradeCode.objects.filter(
        project=project, prefix=system_trade_code.prefix
    ).first()


def _resolve_project_trade_code_by_prefix(project, prefix):
    if not prefix:
        return None
    return ProjectTradeCode.objects.filter(project=project, prefix=prefix).first()


def _resolve_project_material_by_code(project, material_code):
    if not material_code:
        return None
    return ProjectMaterial.objects.filter(
        project=project, material_code=material_code
    ).first()


def sync_material_specs_from_contractor(project):
    """Sync project material specifications with the project's Contractor Library.

    Specs are matched by name. Each sync rebuilds the component list from the
    contractor source.
    """
    company = project.contractor
    if company is None:
        return {"updated": 0, "created": 0, "skipped_no_contractor": True}

    existing_by_name = {
        ps.name: ps for ps in ProjectSpecification.objects.filter(project=project)
    }

    updated = 0
    created = 0
    for cs in (
        ContractorSpecification.objects.filter(company=company)
        .select_related("trade_code")
        .prefetch_related("spec_components__material")
    ):
        prefix = cs.trade_code.prefix if cs.trade_code else None
        trade_code = _resolve_project_trade_code_by_prefix(project, prefix)
        ps = existing_by_name.get(cs.name)
        if ps is None:
            ps = ProjectSpecification.objects.create(
                project=project,
                name=cs.name,
                section=cs.section,
                trade_code=trade_code,
                unit_label=cs.unit_label,
            )
            created += 1
        else:
            ps.section = cs.section
            ps.trade_code = trade_code
            ps.unit_label = cs.unit_label
            ps.save()
            updated += 1

        ps.spec_components.all().delete()
        for comp in cs.spec_components.all():
            mat_code = comp.material.material_code if comp.material else ""
            ProjectSpecificationComponent.objects.create(
                specification=ps,
                material=_resolve_project_material_by_code(project, mat_code),
                label=comp.label,
                qty_per_unit=comp.qty_per_unit,
                sort_order=comp.sort_order,
            )

    return {"updated": updated, "created": created}


def _resolve_project_labour_crew(project, system_crew):
    """Match a system labour crew to the project copy by `source` FK, falling
    back to `crew_type` name for crews imported via Excel (which don't set
    source)."""
    if not system_crew:
        return None
    return (
        ProjectLabourCrew.objects.filter(
            project=project, source_id=system_crew.pk
        ).first()
        or ProjectLabourCrew.objects.filter(
            project=project, crew_type=system_crew.crew_type
        ).first()
    )


def _resolve_project_labour_crew_by_type(project, crew_type):
    if not crew_type:
        return None
    return ProjectLabourCrew.objects.filter(
        project=project, crew_type=crew_type
    ).first()


def sync_labour_specs_from_contractor(project):
    """Sync project labour specifications with the project's Contractor Library."""
    company = project.contractor
    if company is None:
        return {"updated": 0, "created": 0, "skipped_no_contractor": True}

    created = updated = 0
    for cls in ContractorLabourSpecification.objects.filter(
        company=company
    ).select_related("crew"):
        crew_type = cls.crew.crew_type if cls.crew else ""
        crew = _resolve_project_labour_crew_by_type(project, crew_type)
        defaults = {
            "section": cls.section,
            "trade_name": cls.trade_name,
            "unit": cls.unit,
            "crew": crew,
            "daily_production": cls.daily_production,
            "team_mix": cls.team_mix,
            "site_factor": cls.site_factor,
            "tools_factor": cls.tools_factor,
            "leadership_factor": cls.leadership_factor,
        }
        _, was_created = ProjectLabourSpecification.objects.update_or_create(
            project=project,
            name=cls.name,
            defaults=defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"updated": updated, "created": created}


def _resolve_project_plant_cost(project, system_plant_type_id):
    if not system_plant_type_id:
        return None
    return ProjectPlantCost.objects.filter(
        project=project, source_id=system_plant_type_id
    ).first()


def _rebuild_plant_spec_components_from_source(pps, project):
    """Replace a project plant spec's components with a fresh copy of the
    system source's components."""
    pps.components.all().delete()
    if not pps.source_id:  # ty:ignore[unresolved-attribute]
        return
    for comp in pps.source.components.all():
        ProjectPlantSpecificationComponent.objects.create(
            specification=pps,
            plant_type=_resolve_project_plant_cost(
                project,
                comp.plant_type_id,  # ty:ignore[unresolved-attribute]
            ),
            hours=comp.hours,
            sort_order=comp.sort_order,
        )


def _resolve_project_plant_cost_by_name(project, name):
    if not name:
        return None
    return ProjectPlantCost.objects.filter(project=project, name=name).first()


def sync_plant_specs_from_contractor(project):
    """Sync project plant specifications with the project's Contractor Library."""
    company = project.contractor
    if company is None:
        return {"updated": 0, "created": 0, "skipped_no_contractor": True}

    existing_by_name = {
        pps.name: pps
        for pps in ProjectPlantSpecification.objects.filter(project=project)
    }

    created = updated = 0
    for cps in ContractorPlantSpecification.objects.filter(
        company=company
    ).prefetch_related("components__plant_type"):
        defaults = {
            "section": cps.section,
            "trade_name": cps.trade_name,
            "unit": cps.unit,
            "daily_production": cps.daily_production,
            "operator_factor": cps.operator_factor,
            "site_factor": cps.site_factor,
        }
        pps = existing_by_name.get(cps.name)
        if pps is None:
            pps = ProjectPlantSpecification.objects.create(
                project=project, name=cps.name, **defaults
            )
            created += 1
        else:
            for f, v in defaults.items():
                setattr(pps, f, v)
            pps.save()
            updated += 1

        pps.components.all().delete()
        for comp in cps.components.all():
            pt_name = comp.plant_type.name if comp.plant_type else ""
            ProjectPlantSpecificationComponent.objects.create(
                specification=pps,
                plant_type=_resolve_project_plant_cost_by_name(project, pt_name),
                hours=comp.hours,
                sort_order=comp.sort_order,
            )

    return {"updated": updated, "created": created}


def sync_preliminary_specs_from_contractor(project):
    """Sync project preliminary specifications with the project's Contractor Library."""
    company = project.contractor
    if company is None:
        return {"updated": 0, "created": 0, "skipped_no_contractor": True}

    created = updated = 0
    for cps in ContractorPreliminarySpecification.objects.filter(company=company):
        defaults = {
            "section": cps.section,
            "trade_name": cps.trade_name,
            "unit": cps.unit,
            "preliminary_type": cps.preliminary_type,
        }
        _, was_created = ProjectPreliminarySpecification.objects.update_or_create(
            project=project,
            name=cps.name,
            defaults=defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"updated": updated, "created": created}


# ═══════════════════════════════════════════════════════════════════
# Contractor-library sync (System → Contractor, scoped per Company)
#
# Mirror of the project-level sync_*_from_system functions, but writing
# to Contractor* models filtered by `company`.
# ═══════════════════════════════════════════════════════════════════


def sync_trade_codes_to_contractor(company):
    """Sync contractor trade codes with current system library values."""
    updated = 0
    for ctc in ContractorTradeCode.objects.filter(
        company=company, source__isnull=False
    ).select_related("source"):
        ctc.prefix = ctc.source.prefix
        ctc.trade_name = ctc.source.trade_name
        ctc.save()
        updated += 1

    existing_source_ids = set(
        ContractorTradeCode.objects.filter(
            company=company, source__isnull=False
        ).values_list("source_id", flat=True)
    )
    created = 0
    for stc in SystemTradeCode.objects.exclude(pk__in=existing_source_ids):
        defaults = {
            "source": stc,
            "trade_name": stc.trade_name,
        }
        _, was_created = ContractorTradeCode.objects.update_or_create(
            company=company,
            prefix=stc.prefix,
            defaults=defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"updated": updated, "created": created}


def sync_materials_to_contractor(company):
    """Sync contractor material costs with current system library values."""
    updated = 0
    for cm in ContractorMaterial.objects.filter(
        company=company, source__isnull=False
    ).select_related("source"):
        cm.trade_name = cm.source.trade_name
        cm.unit = cm.source.unit
        cm.pack_qty = cm.source.pack_qty
        cm.pack_cost = cm.source.pack_cost
        cm.material_variety = cm.source.material_variety
        cm.market_spec = cm.source.market_spec
        cm.save()
        updated += 1

    existing_source_ids = set(
        ContractorMaterial.objects.filter(
            company=company, source__isnull=False
        ).values_list("source_id", flat=True)
    )
    created = 0
    for sm in SystemMaterial.objects.exclude(pk__in=existing_source_ids):
        defaults = {
            "source": sm,
            "trade_name": sm.trade_name,
            "unit": sm.unit,
            "pack_qty": sm.pack_qty,
            "pack_cost": sm.pack_cost,
            "material_variety": sm.material_variety,
            "market_spec": sm.market_spec,
        }
        _, was_created = ContractorMaterial.objects.update_or_create(
            company=company,
            material_code=sm.material_code,
            defaults=defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"updated": updated, "created": created}


def sync_labour_costs_to_contractor(company):
    """Sync contractor labour crews with current system library values."""
    updated = 0
    for clc in ContractorLabourCrew.objects.filter(
        company=company, source__isnull=False
    ).select_related("source"):
        clc.crew_type = clc.source.crew_type
        clc.crew_size = clc.source.crew_size
        clc.skilled = clc.source.skilled
        clc.semi_skilled = clc.source.semi_skilled
        clc.general = clc.source.general
        clc.daily_production = clc.source.daily_production
        clc.skilled_rate = clc.source.skilled_rate
        clc.semi_skilled_rate = clc.source.semi_skilled_rate
        clc.general_rate = clc.source.general_rate
        clc.save()
        updated += 1

    existing_source_ids = set(
        ContractorLabourCrew.objects.filter(
            company=company, source__isnull=False
        ).values_list("source_id", flat=True)
    )
    created = 0
    for slc in SystemLabourCrew.objects.exclude(pk__in=existing_source_ids):
        defaults = {
            "source": slc,
            "crew_size": slc.crew_size,
            "skilled": slc.skilled,
            "semi_skilled": slc.semi_skilled,
            "general": slc.general,
            "daily_production": slc.daily_production,
            "skilled_rate": slc.skilled_rate,
            "semi_skilled_rate": slc.semi_skilled_rate,
            "general_rate": slc.general_rate,
        }
        _, was_created = ContractorLabourCrew.objects.update_or_create(
            company=company,
            crew_type=slc.crew_type,
            defaults=defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"updated": updated, "created": created}


def sync_plant_costs_to_contractor(company):
    """Sync contractor plant costs with current system library values."""
    updated = 0
    for cpc in ContractorPlantCost.objects.filter(
        company=company, source__isnull=False
    ).select_related("source"):
        cpc.name = cpc.source.name
        cpc.hourly_production = cpc.source.hourly_production
        cpc.hourly_rate = cpc.source.hourly_rate
        cpc.save()
        updated += 1

    existing_source_ids = set(
        ContractorPlantCost.objects.filter(
            company=company, source__isnull=False
        ).values_list("source_id", flat=True)
    )
    created = 0
    for spc in SystemPlantCost.objects.exclude(pk__in=existing_source_ids):
        defaults = {
            "source": spc,
            "hourly_production": spc.hourly_production,
            "hourly_rate": spc.hourly_rate,
        }
        _, was_created = ContractorPlantCost.objects.update_or_create(
            company=company,
            name=spc.name,
            defaults=defaults,
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return {"updated": updated, "created": created}


def sync_preliminary_costs_to_contractor(company):
    """Sync contractor preliminary costs with current system library values."""
    updated = 0
    for cpc in ContractorPreliminaryCost.objects.filter(
        company=company, source__isnull=False
    ).select_related("source"):
        cpc.name = cpc.source.name
        cpc.preliminary_type = cpc.source.preliminary_type
        cpc.sum_value = cpc.source.sum_value
        cpc.amount = cpc.source.amount
        cpc.number_per_month = cpc.source.number_per_month
        cpc.monthly_rate = cpc.source.monthly_rate
        cpc.months = cpc.source.months
        cpc.save()
        updated += 1

    existing_source_ids = set(
        ContractorPreliminaryCost.objects.filter(
            company=company, source__isnull=False
        ).values_list("source_id", flat=True)
    )
    orphan_by_key = {
        (cpc.name, cpc.preliminary_type): cpc
        for cpc in ContractorPreliminaryCost.objects.filter(
            company=company, source__isnull=True
        )
    }
    created = 0
    for spc in SystemPreliminaryCost.objects.exclude(pk__in=existing_source_ids):
        key = (spc.name, spc.preliminary_type)
        cpc = orphan_by_key.pop(key, None)
        if cpc is not None:
            cpc.source = spc
            cpc.sum_value = spc.sum_value
            cpc.amount = spc.amount
            cpc.number_per_month = spc.number_per_month
            cpc.monthly_rate = spc.monthly_rate
            cpc.months = spc.months
            cpc.save()
            updated += 1
            continue
        ContractorPreliminaryCost.objects.create(
            company=company,
            source=spc,
            name=spc.name,
            preliminary_type=spc.preliminary_type,
            sum_value=spc.sum_value,
            amount=spc.amount,
            number_per_month=spc.number_per_month,
            monthly_rate=spc.monthly_rate,
            months=spc.months,
        )
        created += 1

    return {"updated": updated, "created": created}


def _resolve_contractor_material(company, system_material):
    if not system_material:
        return None
    return (
        ContractorMaterial.objects.filter(
            company=company, source_id=system_material.pk
        ).first()
        or ContractorMaterial.objects.filter(
            company=company, material_code=system_material.material_code
        ).first()
    )


def _resolve_contractor_trade_code(company, system_trade_code):
    if not system_trade_code:
        return None
    return ContractorTradeCode.objects.filter(
        company=company, prefix=system_trade_code.prefix
    ).first()


def sync_material_specs_to_contractor(company):
    """Sync contractor material specifications with the SystemSpecification
    library. Specs are matched by name; each sync rebuilds the component
    list from the system source."""
    existing_by_name = {
        cs.name: cs for cs in ContractorSpecification.objects.filter(company=company)
    }

    updated = 0
    created = 0
    for ss in SystemSpecification.objects.select_related("trade_code").prefetch_related(
        "spec_components__material"
    ):
        trade_code = _resolve_contractor_trade_code(company, ss.trade_code)
        cs = existing_by_name.get(ss.name)
        if cs is None:
            cs = ContractorSpecification.objects.create(
                company=company,
                source=ss,
                name=ss.name,
                section=ss.section,
                trade_code=trade_code,
                unit_label=ss.unit_label,
            )
            created += 1
        else:
            cs.source = ss
            cs.section = ss.section
            cs.trade_code = trade_code
            cs.unit_label = ss.unit_label
            cs.save()
            updated += 1

        cs.spec_components.all().delete()
        for comp in ss.spec_components.all():
            ContractorSpecificationComponent.objects.create(
                specification=cs,
                material=_resolve_contractor_material(company, comp.material),
                label=comp.label,
                qty_per_unit=comp.qty_per_unit,
                sort_order=comp.sort_order,
            )

    return {"updated": updated, "created": created}


def _resolve_contractor_labour_crew(company, system_crew):
    if not system_crew:
        return None
    return (
        ContractorLabourCrew.objects.filter(
            company=company, source_id=system_crew.pk
        ).first()
        or ContractorLabourCrew.objects.filter(
            company=company, crew_type=system_crew.crew_type
        ).first()
    )


def sync_labour_specs_to_contractor(company):
    """Sync contractor labour specifications with current system library values."""
    updated = 0
    for cls in ContractorLabourSpecification.objects.filter(
        company=company, source__isnull=False
    ).select_related("source", "source__crew"):
        cls.section = cls.source.section
        cls.trade_name = cls.source.trade_name
        cls.name = cls.source.name
        cls.unit = cls.source.unit
        cls.daily_production = cls.source.daily_production
        cls.team_mix = cls.source.team_mix
        cls.site_factor = cls.source.site_factor
        cls.tools_factor = cls.source.tools_factor
        cls.leadership_factor = cls.source.leadership_factor
        cls.crew = _resolve_contractor_labour_crew(company, cls.source.crew)
        cls.save()
        updated += 1

    existing_source_ids = set(
        ContractorLabourSpecification.objects.filter(
            company=company, source__isnull=False
        ).values_list("source_id", flat=True)
    )
    orphan_by_name = {
        cls.name: cls
        for cls in ContractorLabourSpecification.objects.filter(
            company=company, source__isnull=True
        )
    }
    created = 0
    for sls in SystemLabourSpecification.objects.exclude(
        pk__in=existing_source_ids
    ).select_related("crew"):
        crew = _resolve_contractor_labour_crew(company, sls.crew)
        cls = orphan_by_name.pop(sls.name, None)
        if cls is not None:
            cls.source = sls
            cls.section = sls.section
            cls.trade_name = sls.trade_name
            cls.unit = sls.unit
            cls.crew = crew
            cls.daily_production = sls.daily_production
            cls.team_mix = sls.team_mix
            cls.site_factor = sls.site_factor
            cls.tools_factor = sls.tools_factor
            cls.leadership_factor = sls.leadership_factor
            cls.save()
            updated += 1
            continue
        ContractorLabourSpecification.objects.create(
            company=company,
            source=sls,
            section=sls.section,
            trade_name=sls.trade_name,
            name=sls.name,
            unit=sls.unit,
            crew=crew,
            daily_production=sls.daily_production,
            team_mix=sls.team_mix,
            site_factor=sls.site_factor,
            tools_factor=sls.tools_factor,
            leadership_factor=sls.leadership_factor,
        )
        created += 1

    return {"updated": updated, "created": created}


def _resolve_contractor_plant_cost(company, system_plant_type_id):
    if not system_plant_type_id:
        return None
    return ContractorPlantCost.objects.filter(
        company=company, source_id=system_plant_type_id
    ).first()


def _rebuild_contractor_plant_spec_components(cps, company):
    cps.components.all().delete()
    if not cps.source_id:  # ty:ignore[unresolved-attribute]
        return
    for comp in cps.source.components.all():
        ContractorPlantSpecificationComponent.objects.create(
            specification=cps,
            plant_type=_resolve_contractor_plant_cost(
                company,
                comp.plant_type_id,  # ty:ignore[unresolved-attribute]
            ),
            hours=comp.hours,
            sort_order=comp.sort_order,
        )


def sync_plant_specs_to_contractor(company):
    """Sync contractor plant specifications with current system library values."""
    updated = 0
    for cps in ContractorPlantSpecification.objects.filter(
        company=company, source__isnull=False
    ).select_related("source"):
        cps.section = cps.source.section
        cps.trade_name = cps.source.trade_name
        cps.name = cps.source.name
        cps.unit = cps.source.unit
        cps.daily_production = cps.source.daily_production
        cps.operator_factor = cps.source.operator_factor
        cps.site_factor = cps.source.site_factor
        cps.save()
        _rebuild_contractor_plant_spec_components(cps, company)
        updated += 1

    existing_source_ids = set(
        ContractorPlantSpecification.objects.filter(
            company=company, source__isnull=False
        ).values_list("source_id", flat=True)
    )
    orphan_by_name = {
        cps.name: cps
        for cps in ContractorPlantSpecification.objects.filter(
            company=company, source__isnull=True
        )
    }
    created = 0
    for sps in SystemPlantSpecification.objects.exclude(
        pk__in=existing_source_ids
    ).prefetch_related("components"):
        cps = orphan_by_name.pop(sps.name, None)
        if cps is not None:
            cps.source = sps
            cps.section = sps.section
            cps.trade_name = sps.trade_name
            cps.unit = sps.unit
            cps.daily_production = sps.daily_production
            cps.operator_factor = sps.operator_factor
            cps.site_factor = sps.site_factor
            cps.save()
            _rebuild_contractor_plant_spec_components(cps, company)
            updated += 1
            continue
        cps = ContractorPlantSpecification.objects.create(
            company=company,
            source=sps,
            section=sps.section,
            trade_name=sps.trade_name,
            name=sps.name,
            unit=sps.unit,
            daily_production=sps.daily_production,
            operator_factor=sps.operator_factor,
            site_factor=sps.site_factor,
        )
        for comp in sps.components.all():
            ContractorPlantSpecificationComponent.objects.create(
                specification=cps,
                plant_type=_resolve_contractor_plant_cost(
                    company,
                    comp.plant_type_id,  # ty:ignore[unresolved-attribute]
                ),
                hours=comp.hours,
                sort_order=comp.sort_order,
            )
        created += 1

    return {"updated": updated, "created": created}


def sync_preliminary_specs_to_contractor(company):
    """Sync contractor preliminary specifications with current system library values."""
    updated = 0
    for cps in ContractorPreliminarySpecification.objects.filter(
        company=company, source__isnull=False
    ).select_related("source"):
        cps.section = cps.source.section
        cps.trade_name = cps.source.trade_name
        cps.name = cps.source.name
        cps.unit = cps.source.unit
        cps.preliminary_type = cps.source.preliminary_type
        cps.save()
        updated += 1

    existing_source_ids = set(
        ContractorPreliminarySpecification.objects.filter(
            company=company, source__isnull=False
        ).values_list("source_id", flat=True)
    )
    orphan_by_name = {
        cps.name: cps
        for cps in ContractorPreliminarySpecification.objects.filter(
            company=company, source__isnull=True
        )
    }
    created = 0
    for sps in SystemPreliminarySpecification.objects.exclude(
        pk__in=existing_source_ids
    ):
        cps = orphan_by_name.pop(sps.name, None)
        if cps is not None:
            cps.source = sps
            cps.section = sps.section
            cps.trade_name = sps.trade_name
            cps.unit = sps.unit
            cps.preliminary_type = sps.preliminary_type
            cps.save()
            updated += 1
            continue
        ContractorPreliminarySpecification.objects.create(
            company=company,
            source=sps,
            section=sps.section,
            trade_name=sps.trade_name,
            name=sps.name,
            unit=sps.unit,
            preliminary_type=sps.preliminary_type,
        )
        created += 1

    return {"updated": updated, "created": created}


# ── Item Library Sync ────────────────────────────────────────────


def sync_item_library_to_contractor(company):
    """Mirror SystemItemLibraryEntry into ContractorItemLibraryEntry for a
    company. Match on existing source FK; fall back to (component, description).
    Spec FKs resolve by name into the contractor's scoped tables.
    """
    by_source = {
        e.source_id: e
        for e in ContractorItemLibraryEntry.objects.filter(
            company=company, source__isnull=False
        )
    }
    by_key = {
        (e.component, e.description): e
        for e in ContractorItemLibraryEntry.objects.filter(
            company=company, source__isnull=True
        )
    }

    created = updated = 0
    for sysentry in SystemItemLibraryEntry.objects.select_related(
        "trade_code",
        "material_spec",
        "labour_spec",
        "plant_spec",
        "preliminary_spec",
    ):
        trade_code = _resolve_contractor_trade_code(company, sysentry.trade_code)
        material_spec = (
            ContractorMaterialSpec.objects.filter(
                company=company, name=sysentry.material_spec.name
            ).first()
            if sysentry.material_spec
            else None
        )
        labour_spec = (
            ContractorLabourSpecification.objects.filter(
                company=company, name=sysentry.labour_spec.name
            ).first()
            if sysentry.labour_spec
            else None
        )
        plant_spec = (
            ContractorPlantSpecification.objects.filter(
                company=company, name=sysentry.plant_spec.name
            ).first()
            if sysentry.plant_spec
            else None
        )
        prelim_spec = (
            ContractorPreliminarySpecification.objects.filter(
                company=company, name=sysentry.preliminary_spec.name
            ).first()
            if sysentry.preliminary_spec
            else None
        )

        defaults = {
            "trade_code": trade_code,
            "item_code": sysentry.item_code,
            "accounts_code": sysentry.accounts_code,
            "component": sysentry.component,
            "description": sysentry.description,
            "unit": sysentry.unit,
            "material_spec": material_spec,
            "labour_spec": labour_spec,
            "plant_spec": plant_spec,
            "preliminary_spec": prelim_spec,
            "display_order": sysentry.display_order,
        }

        target = by_source.get(sysentry.pk) or by_key.get(
            (sysentry.component, sysentry.description)
        )
        if target is None:
            ContractorItemLibraryEntry.objects.create(
                company=company, source=sysentry, **defaults
            )
            created += 1
        else:
            target.source = sysentry
            for k, v in defaults.items():
                setattr(target, k, v)
            target.save()
            updated += 1

    return {"created": created, "updated": updated}


def sync_item_library_from_system(project):
    """Clone SystemItemLibraryEntry rows into the project. Spec FKs resolve
    against the project-scoped tables by name; missing targets stay blank."""
    by_source = {
        e.source_system_id: e
        for e in ProjectItemLibraryEntry.objects.filter(
            project=project, source_system__isnull=False
        )
    }
    by_key = {
        (e.component, e.description): e
        for e in ProjectItemLibraryEntry.objects.filter(
            project=project,
            source_system__isnull=True,
            source_contractor__isnull=True,
        )
    }

    created = updated = 0
    for sysentry in SystemItemLibraryEntry.objects.select_related(
        "trade_code",
        "material_spec",
        "labour_spec",
        "plant_spec",
        "preliminary_spec",
    ):
        prefix = sysentry.trade_code.prefix if sysentry.trade_code else None
        trade_code = _resolve_project_trade_code_by_prefix(project, prefix)
        material_spec = (
            ProjectSpecification.objects.filter(
                project=project, name=sysentry.material_spec.name
            ).first()
            if sysentry.material_spec
            else None
        )
        labour_spec = (
            ProjectLabourSpecification.objects.filter(
                project=project, name=sysentry.labour_spec.name
            ).first()
            if sysentry.labour_spec
            else None
        )
        plant_spec = (
            ProjectPlantSpecification.objects.filter(
                project=project, name=sysentry.plant_spec.name
            ).first()
            if sysentry.plant_spec
            else None
        )
        prelim_spec = (
            ProjectPreliminarySpecification.objects.filter(
                project=project, name=sysentry.preliminary_spec.name
            ).first()
            if sysentry.preliminary_spec
            else None
        )

        defaults = {
            "trade_code": trade_code,
            "item_code": sysentry.item_code,
            "accounts_code": sysentry.accounts_code,
            "component": sysentry.component,
            "description": sysentry.description,
            "unit": sysentry.unit,
            "material_spec": material_spec,
            "labour_spec": labour_spec,
            "plant_spec": plant_spec,
            "preliminary_spec": prelim_spec,
            "display_order": sysentry.display_order,
        }

        target = by_source.get(sysentry.pk) or by_key.get(
            (sysentry.component, sysentry.description)
        )
        if target is None:
            ProjectItemLibraryEntry.objects.create(
                project=project, source_system=sysentry, **defaults
            )
            created += 1
        else:
            target.source_system = sysentry
            for k, v in defaults.items():
                setattr(target, k, v)
            target.save()
            updated += 1

    return {"created": created, "updated": updated}


def sync_item_library_from_contractor(project):
    """Clone the project's contractor ItemLibrary into the project. Falls back
    to System if the project has no linked contractor."""
    company = project.contractor
    if company is None:
        return {"updated": 0, "created": 0, "skipped_no_contractor": True}

    by_source = {
        e.source_contractor_id: e
        for e in ProjectItemLibraryEntry.objects.filter(
            project=project, source_contractor__isnull=False
        )
    }
    by_key = {
        (e.component, e.description): e
        for e in ProjectItemLibraryEntry.objects.filter(
            project=project,
            source_contractor__isnull=True,
        )
    }

    created = updated = 0
    for centry in ContractorItemLibraryEntry.objects.filter(
        company=company
    ).select_related(
        "trade_code",
        "material_spec",
        "labour_spec",
        "plant_spec",
        "preliminary_spec",
    ):
        prefix = centry.trade_code.prefix if centry.trade_code else None
        trade_code = _resolve_project_trade_code_by_prefix(project, prefix)
        material_spec = (
            ProjectSpecification.objects.filter(
                project=project, name=centry.material_spec.name
            ).first()
            if centry.material_spec
            else None
        )
        labour_spec = (
            ProjectLabourSpecification.objects.filter(
                project=project, name=centry.labour_spec.name
            ).first()
            if centry.labour_spec
            else None
        )
        plant_spec = (
            ProjectPlantSpecification.objects.filter(
                project=project, name=centry.plant_spec.name
            ).first()
            if centry.plant_spec
            else None
        )
        prelim_spec = (
            ProjectPreliminarySpecification.objects.filter(
                project=project, name=centry.preliminary_spec.name
            ).first()
            if centry.preliminary_spec
            else None
        )

        defaults = {
            "trade_code": trade_code,
            "item_code": centry.item_code,
            "accounts_code": centry.accounts_code,
            "component": centry.component,
            "description": centry.description,
            "unit": centry.unit,
            "material_spec": material_spec,
            "labour_spec": labour_spec,
            "plant_spec": plant_spec,
            "preliminary_spec": prelim_spec,
            "display_order": centry.display_order,
        }

        target = by_source.get(centry.pk) or by_key.get(
            (centry.component, centry.description)
        )
        if target is None:
            ProjectItemLibraryEntry.objects.create(
                project=project, source_contractor=centry, **defaults
            )
            created += 1
        else:
            target.source_contractor = centry
            for k, v in defaults.items():
                setattr(target, k, v)
            target.save()
            updated += 1

    return {"created": created, "updated": updated}


def autofill_boq_from_library(project):
    """Fill spec FKs on Output BoQ rows from matching Item Library entries.

    For each non-header BoQ row in `project` that has none of the four spec
    FKs set, find a matching ProjectItemLibraryEntry and copy its spec FKs
    over plus the back-link.

    Match ladder (case-insensitive, trimmed):
      1. component + trade_code + description all match
      2. component + trade_code match (must be unique)
      3. description match (must be unique)

    Rows already carrying any spec are left untouched. Ambiguous tier-2 or
    tier-3 hits are reported, not picked at random.
    """

    def norm(s):
        return (s or "").strip().lower()

    library = list(
        ProjectItemLibraryEntry.objects.filter(project=project).select_related(
            "trade_code"
        )
    )

    by_full = {}
    by_ct = {}
    by_desc = {}
    for e in library:
        by_full[(norm(e.component), e.trade_code_id, norm(e.description))] = e
        by_ct.setdefault((norm(e.component), e.trade_code_id), []).append(e)
        by_desc.setdefault(norm(e.description), []).append(e)

    filled = skipped_already_set = no_match = ambiguous = 0

    for item in BOQItem.objects.filter(
        project=project, is_section_header=False
    ).select_related("trade_code"):
        if (
            item.specification_id
            or item.labour_specification_id
            or item.plant_specification_id
            or item.preliminary_specification_id
        ):
            skipped_already_set += 1
            continue

        comp = norm(item.component)
        desc = norm(item.description)
        tc_id = item.trade_code_id

        match = by_full.get((comp, tc_id, desc))
        if match is None:
            ct_matches = by_ct.get((comp, tc_id), [])
            if len(ct_matches) == 1:
                match = ct_matches[0]
            elif len(ct_matches) > 1:
                ambiguous += 1
                continue
            else:
                desc_matches = by_desc.get(desc, [])
                if len(desc_matches) == 1:
                    match = desc_matches[0]
                elif len(desc_matches) > 1:
                    ambiguous += 1
                    continue
                else:
                    no_match += 1
                    continue

        item.library_entry = match
        item.specification = match.material_spec
        item.labour_specification = match.labour_spec
        item.plant_specification = match.plant_spec
        item.preliminary_specification = match.preliminary_spec
        item.save(
            update_fields=[
                "library_entry",
                "specification",
                "labour_specification",
                "plant_specification",
                "preliminary_specification",
            ]
        )
        filled += 1

    return {
        "filled": filled,
        "skipped_already_set": skipped_already_set,
        "no_match": no_match,
        "ambiguous": ambiguous,
    }


def save_boq_item_to_library(item, item_code=None):
    """Upsert a single BOQItem's spec mapping into the project Item Library.

    Match key (case-insensitive, trimmed): (component, trade_code_id, description).
    If an entry exists, its spec FKs are overwritten; otherwise a new entry is
    created. The BOQItem's `library_entry` back-link is updated to point at
    whichever entry is now authoritative.

    `item_code` (optional): when provided, set/overwrite the entry's item_code.
    Passing None leaves any existing code untouched; passing "" clears it.

    Returns the dict {"created": bool, "entry_id": int}.
    """
    if item.is_section_header:
        return {"created": False, "entry_id": None, "skipped": True}

    component = (item.component or "").strip()
    description = (item.description or "").strip()
    trade_code_id = item.trade_code_id
    normalized_code = item_code.strip() if isinstance(item_code, str) else None

    existing = (
        ProjectItemLibraryEntry.objects.filter(
            project=item.project,
            trade_code_id=trade_code_id,
            component__iexact=component,
            description__iexact=description,
        )
        .order_by("id")
        .first()
    )

    if existing is None:
        entry = ProjectItemLibraryEntry.objects.create(
            project=item.project,
            trade_code_id=trade_code_id,
            component=component,
            description=description,
            unit=item.unit or "",
            item_code=normalized_code or "",
            material_spec=item.specification,
            labour_spec=item.labour_specification,
            plant_spec=item.plant_specification,
            preliminary_spec=item.preliminary_specification,
        )
        created = True
    else:
        existing.unit = item.unit or existing.unit
        existing.material_spec = item.specification
        existing.labour_spec = item.labour_specification
        existing.plant_spec = item.plant_specification
        existing.preliminary_spec = item.preliminary_specification
        update_fields = [
            "unit",
            "material_spec",
            "labour_spec",
            "plant_spec",
            "preliminary_spec",
        ]
        if normalized_code is not None:
            existing.item_code = normalized_code
            update_fields.append("item_code")
        existing.save(update_fields=update_fields)
        entry = existing
        created = False

    item.library_entry = entry
    item.save(update_fields=["library_entry"])

    return {"created": created, "entry_id": entry.id, "skipped": False}


def apply_library_entry_to_boq_item(item, entry):
    """Overwrite a BOQItem's spec FKs from a ProjectItemLibraryEntry.

    Sets library_entry + the four spec FKs (specification, labour_specification,
    plant_specification, preliminary_specification). Trade code, component,
    description, and unit on the BoQ row are left untouched.
    """
    item.library_entry = entry
    item.specification = entry.material_spec
    item.labour_specification = entry.labour_spec
    item.plant_specification = entry.plant_spec
    item.preliminary_specification = entry.preliminary_spec
    item.save(
        update_fields=[
            "library_entry",
            "specification",
            "labour_specification",
            "plant_specification",
            "preliminary_specification",
        ]
    )
