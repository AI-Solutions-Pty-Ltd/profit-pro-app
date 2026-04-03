"""Data migration: for each project with BOQItems, clone System* records
into Project* tables and remap BOQItem FK references."""

from django.db import migrations


def clone_system_to_project(apps, schema_editor):
    """Clone all System* records into Project* for each project that has BOQItems."""
    BOQItem = apps.get_model('estimator', 'BOQItem')
    SystemTradeCode = apps.get_model('estimator', 'SystemTradeCode')
    SystemMaterial = apps.get_model('estimator', 'SystemMaterial')
    SystemSpecification = apps.get_model('estimator', 'SystemSpecification')
    SystemSpecificationComponent = apps.get_model('estimator', 'SystemSpecificationComponent')
    SystemLabourCrew = apps.get_model('estimator', 'SystemLabourCrew')
    SystemLabourSpecification = apps.get_model('estimator', 'SystemLabourSpecification')
    ProjectTradeCode = apps.get_model('estimator', 'ProjectTradeCode')
    ProjectMaterial = apps.get_model('estimator', 'ProjectMaterial')
    ProjectSpecification = apps.get_model('estimator', 'ProjectSpecification')
    ProjectSpecificationComponent = apps.get_model('estimator', 'ProjectSpecificationComponent')
    ProjectLabourCrew = apps.get_model('estimator', 'ProjectLabourCrew')
    ProjectLabourSpecification = apps.get_model('estimator', 'ProjectLabourSpecification')
    SystemMaterialSpec = apps.get_model('estimator', 'SystemMaterialSpec')

    # Find all projects that have BOQItems
    project_ids = set(
        BOQItem.objects.exclude(project__isnull=True)
        .values_list('project_id', flat=True)
        .distinct()
    )

    if not project_ids:
        return

    for project_id in project_ids:
        # ── Trade Codes ──
        tc_map = {}  # old system pk → new project pk
        for stc in SystemTradeCode.objects.all():
            ptc = ProjectTradeCode.objects.create(
                project_id=project_id,
                source_id=stc.pk,
                prefix=stc.prefix,
                trade_name=stc.trade_name,
            )
            tc_map[stc.pk] = ptc.pk

        # ── Materials ──
        mat_map = {}
        for sm in SystemMaterial.objects.all():
            pm = ProjectMaterial.objects.create(
                project_id=project_id,
                source_id=sm.pk,
                trade_name=sm.trade_name,
                material_code=sm.material_code,
                unit=sm.unit,
                market_rate=sm.market_rate,
                material_variety=sm.material_variety,
                market_spec=sm.market_spec,
            )
            mat_map[sm.pk] = pm.pk

        # ── Labour Crews ──
        crew_map = {}
        for slc in SystemLabourCrew.objects.all():
            plc = ProjectLabourCrew.objects.create(
                project_id=project_id,
                source_id=slc.pk,
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
            crew_map[slc.pk] = plc.pk

        # ── Labour Specifications ──
        lspec_map = {}
        for sls in SystemLabourSpecification.objects.all():
            pls = ProjectLabourSpecification.objects.create(
                project_id=project_id,
                source_id=sls.pk,
                section=sls.section,
                trade_name=sls.trade_name,
                name=sls.name,
                unit=sls.unit,
                crew_id=crew_map.get(sls.crew_id) if sls.crew_id else None,
                daily_production=sls.daily_production,
                team_mix=sls.team_mix,
                site_factor=sls.site_factor,
                tools_factor=sls.tools_factor,
                leadership_factor=sls.leadership_factor,
            )
            lspec_map[sls.pk] = pls.pk

        # ── Specifications ──
        spec_map = {}  # old SystemSpecification pk → new ProjectSpecification pk
        for ss in SystemSpecification.objects.all():
            # Find matching SystemMaterialSpec source if linked
            source_id = ss.system_spec_id if hasattr(ss, 'system_spec_id') else None
            ps = ProjectSpecification.objects.create(
                project_id=project_id,
                source_id=source_id,
                section=ss.section,
                trade_code_id=tc_map.get(ss.trade_code_id) if ss.trade_code_id else None,
                unit_label=ss.unit_label,
                name=ss.name,
            )
            spec_map[ss.pk] = ps.pk

            # Clone specification components
            for ssc in SystemSpecificationComponent.objects.filter(specification_id=ss.pk):
                ProjectSpecificationComponent.objects.create(
                    specification_id=ps.pk,
                    material_id=mat_map.get(ssc.material_id) if ssc.material_id else None,
                    label=ssc.label,
                    qty_per_unit=ssc.qty_per_unit,
                    sort_order=ssc.sort_order,
                )

        # ── Remap BOQItem FKs ──
        for boq in BOQItem.objects.filter(project_id=project_id):
            changed = False
            if boq.trade_code_id and boq.trade_code_id in tc_map:
                boq.trade_code_id = tc_map[boq.trade_code_id]
                changed = True
            if boq.specification_id and boq.specification_id in spec_map:
                boq.specification_id = spec_map[boq.specification_id]
                changed = True
            if boq.labour_specification_id and boq.labour_specification_id in lspec_map:
                boq.labour_specification_id = lspec_map[boq.labour_specification_id]
                changed = True
            if boq.material_id and boq.material_id in mat_map:
                boq.material_id = mat_map[boq.material_id]
                changed = True
            if changed:
                boq.save()


def reverse_noop(apps, schema_editor):
    """Reverse is a no-op — dropping Project* tables via migration rollback
    handles cleanup. BOQItem FKs will be nulled by the FK alter rollback."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('estimator', '0006_systemlabourcrew_systemmaterial_systemtradecode_and_more'),
    ]

    operations = [
        migrations.RunPython(clone_system_to_project, reverse_noop),
    ]
