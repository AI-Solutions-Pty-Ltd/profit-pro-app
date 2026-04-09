from decimal import Decimal

from django.db import transaction
from django.db.models import F, Sum, Q

from app.Project.models import LabourCostTracker, SubcontractorCostTracker
from app.SiteManagement.models import LabourLog, SubcontractorLog


def import_subcontractor_logs_to_profitability(project):
    """
    Import subcontractor site logs into the profitability cost tracker.
    Prevents duplicate imports based on subcontractor_entity and date.
    """
    logs = SubcontractorLog.objects.filter(project=project)
    count = 0

    with transaction.atomic():
        for log in logs:
            # Check if an entry already exists for this subcontractor and date
            exists = SubcontractorCostTracker.objects.filter(
                project=project,
                subcontractor_entity=log.subcontractor_entity,
                date=log.date,
            ).exists()

            if not exists:
                # Assuming 1 day for each log entry if not specified
                # Some logs have hours_worked, we could convert to days (8hrs = 1 day)
                days = 1.0
                if log.hours_worked:
                    days = float(log.hours_worked / 8)

                SubcontractorCostTracker.objects.create(
                    project=project,
                    subcontractor_entity=log.subcontractor_entity,
                    date=log.date,
                    amount_of_days=days,
                    rate=log.subcontractor_entity.rate
                    if log.subcontractor_entity
                    else 0,
                    # Other fields like reference_no come from log or entity
                    reference_no=log.subcontractor_entity.reference_no
                    if log.subcontractor_entity
                    else "",
                )
                count += 1
    return count


def import_labour_logs_to_profitability(project):
    """
    Import labour site logs into the profitability cost tracker.
    """
    logs = LabourLog.objects.filter(project=project)
    count = 0

    with transaction.atomic():
        for log in logs:
            exists = LabourCostTracker.objects.filter(
                project=project, labour_entity=log.labour_entity, date=log.date
            ).exists()

            if not exists:
                days = float(log.hours_worked / 8) if log.hours_worked else 1.0
                LabourCostTracker.objects.create(
                    project=project,
                    labour_entity=log.labour_entity,
                    date=log.date,
                    amount_of_days=days,
                    salary=log.labour_entity.rate if log.labour_entity else 0,
                )
                count += 1
    return count


def import_material_logs_to_profitability(project):
    """
    Import material site logs into the profitability cost tracker.
    """
    from app.Project.models import MaterialCostTracker
    from app.SiteManagement.models import MaterialsLog

    logs = MaterialsLog.objects.filter(project=project)
    count = 0

    with transaction.atomic():
        for log in logs:
            exists = MaterialCostTracker.objects.filter(
                project=project,
                material_entity=log.material_entity,
                date=log.date_received,
            ).exists()

            if not exists:
                MaterialCostTracker.objects.create(
                    project=project,
                    material_entity=log.material_entity,
                    date=log.date_received,
                    quantity=log.quantity,
                    invoice_number=log.invoice_number
                    or (
                        log.material_entity.invoice_number
                        if log.material_entity
                        else ""
                    ),
                    rate=log.material_entity.rate if log.material_entity else 0,
                )
                count += 1
    return count


def import_plant_logs_to_profitability(project):
    """
    Import plant equipment site logs into the profitability cost tracker.
    """
    from app.Project.models import PlantCostTracker
    from app.SiteManagement.models import PlantEquipment

    # Only import logs that are linked to a master plant definition (PlantEntity)
    logs = PlantEquipment.objects.filter(project=project, plant_entity__isnull=False)
    count = 0

    with transaction.atomic():
        for log in logs:
            exists = PlantCostTracker.objects.filter(
                project=project, plant_entity=log.plant_entity, date=log.date
            ).exists()

            if not exists:
                rate = log.plant_entity.rate if log.plant_entity else 0
                # Fallback to hourly_rate if specifically defined on PlantType (optional)
                if rate == 0 and log.plant_entity and log.plant_entity.plant_type:
                    rate = log.plant_entity.plant_type.hourly_rate

                PlantCostTracker.objects.create(
                    project=project,
                    plant_entity=log.plant_entity,
                    date=log.date,
                    usage_hours=log.usage_hours or 0,
                    hourly_rate=rate,
                )
                count += 1
    return count


def import_overhead_logs_to_profitability(project):
    """
    Import overhead site logs into the profitability cost tracker.
    """
    from app.Project.models import OverheadCostTracker
    from app.SiteManagement.models import OverheadDailyLog

    logs = OverheadDailyLog.objects.filter(
        project=project, overhead_entity__isnull=False
    )
    count = 0

    with transaction.atomic():
        for log in logs:
            exists = OverheadCostTracker.objects.filter(
                project=project, overhead_entity=log.overhead_entity, date=log.date
            ).exists()

            if not exists:
                OverheadCostTracker.objects.create(
                    project=project,
                    overhead_entity=log.overhead_entity,
                    date=log.date,
                    amount_of_days=log.quantity,
                    rate=log.overhead_entity.rate if log.overhead_entity else 0,
                )
                count += 1
    return count


def get_project_profitability_metrics(project):
    """
    Calculate and return key profitability metrics for a project.
    """
    # Summary Costs
    journal_total = project.journal_entries.aggregate(total=Sum("amount"))["total"] or 0
    subcontractor_total = (
        project.subcontractor_cost_logs.aggregate(
            total=Sum(F("amount_of_days") * F("rate"))
        )["total"]
        or 0
    )
    labour_total = (
        project.labour_cost_logs.aggregate(
            total=Sum(F("amount_of_days") * F("salary"))
        )["total"]
        or 0
    )
    overhead_total = (
        project.overhead_cost_logs.aggregate(
            total=Sum(F("amount_of_days") * F("rate"))
        )["total"]
        or 0
    )
    material_total = (
        project.material_cost_logs.aggregate(total=Sum(F("quantity") * F("rate")))[
            "total"
        ]
        or 0
    )
    plant_total = (
        project.plant_cost_logs.aggregate(
            total=Sum(F("usage_hours") * F("hourly_rate"))
        )["total"]
        or 0
    )

    total_actual_cost = (
        Decimal(journal_total)
        + Decimal(subcontractor_total)
        + Decimal(labour_total)
        + Decimal(overhead_total)
        + Decimal(material_total)
        + Decimal(plant_total)
    )

    # Revenue / Baseline
    # We use contract value as planned revenue, or fall back to dashboard logic
    revenue = project.total_contract_value or Decimal("0.00")

    # If revenue is 0, we can't calculate margin reasonably, so we use a fallback if needed
    # for UI display purposes similar to the dashboard.
    if revenue == 0:
        if total_actual_cost > 0:
            revenue = total_actual_cost * Decimal("1.25")
        else:
            revenue = Decimal("100000.00")

    actual_profit = revenue - total_actual_cost
    actual_margin = (actual_profit / revenue * 100) if revenue > 0 else 0

    return {
        "revenue": revenue,
        "total_actual_cost": total_actual_cost,
        "actual_profit": actual_profit,
        "actual_margin": actual_margin,
        "target_margin": 20.0,  # Default target
        "costs": {
            "labour": labour_total,
            "material": material_total + plant_total,
            "subcontractor": subcontractor_total,
            "overhead": overhead_total,
        },
    }


def import_certificates_to_journal(project):
    """
    Import approved payment certificates into the journal as revenue.
    Ensures entries stay in sync with certificate changes.
    """
    from app.BillOfQuantities.models import PaymentCertificate
    from app.Project.models import JournalEntry

    certificates = PaymentCertificate.objects.filter(
        project=project, status=PaymentCertificate.Status.APPROVED
    )
    count = 0

    with transaction.atomic():
        for cert in certificates:
            # Use current claim total as the revenue amount for this certificate's period
            amount = cert.work_current_claim_total

            if amount > 0:
                JournalEntry.objects.update_or_create(
                    project=project,
                    source_log_id=cert.id,
                    source_log_type="PaymentCertificate",
                    defaults={
                        "date": cert.approved_on.date()
                        if cert.approved_on
                        else cert.created_at.date(),
                        "category": JournalEntry.Category.REVENUE,
                        "description": f"Revenue from Payment Certificate #{cert.certificate_number}",
                        "amount": amount,
                        "transaction_type": JournalEntry.EntryType.CREDIT,
                    },
                )
                count += 1
            else:
                # Remove entry if amount is zeroed out
                JournalEntry.objects.filter(
                    project=project,
                    source_log_id=cert.id,
                    source_log_type="PaymentCertificate",
                ).delete()
    return count


def sync_tracker_to_journal(instance, deleted=False):
    """
    Synchronize cost tracker(s) for a specific item/entity with a single JournalEntry.
    Consolidates multiple logs for the same entity on the same day into one aggregate entry.
    """
    from app.Project.models import JournalEntry

    tracker_model = instance.__class__
    tracker_model_name = tracker_model.__name__

    # Map tracker class names to their parent Entity model names and attributes
    mapping = {
        "LabourCostTracker": (
            JournalEntry.Category.LABOUR,
            "Labour Cost",
            "labour_entity",
        ),
        "MaterialCostTracker": (
            JournalEntry.Category.MATERIAL,
            "Material Cost",
            "material_entity",
        ),
        "PlantCostTracker": (
            JournalEntry.Category.PLANT,
            "Plant/Equipment Cost",
            "plant_entity",
        ),
        "OverheadCostTracker": (
            JournalEntry.Category.OVERHEAD,
            "Overhead Cost",
            "overhead_entity",
        ),
        "SubcontractorCostTracker": (
            JournalEntry.Category.SUBCONTRACTOR,
            "Subcontractor Cost",
            "subcontractor_entity",
        ),
    }

    if tracker_model_name not in mapping:
        return

    category, prefix, entity_attr = mapping[tracker_model_name]
    entity = getattr(instance, entity_attr, None)

    if not entity:
        return

    # Use the Entity ID as the link so all logs for this entity share one entry
    source_log_id = entity.id
    source_log_type = entity.__class__.__name__
    target_date = instance.date

    # 1. Fetch all trackers for this Project, Date, and Entity
    # (Checking against the date provided in the instance that triggered the sync)
    filter_kwargs = {
        "project": instance.project,
        "date": target_date,
        entity_attr: entity,
    }
    all_related_trackers = tracker_model.objects.filter(**filter_kwargs)

    # 2. Calculate the aggregate amount
    # Note: Using list comprehension + sum as 'cost' is often a @property
    total_amount = sum(float(t.cost) for t in all_related_trackers)

    if total_amount <= 0 or (deleted and all_related_trackers.count() == 0):
        # Remove journal entry if no costs remain for this item on this day
        JournalEntry.objects.filter(
            project=instance.project,
            date=target_date,
            source_log_id=source_log_id,
            source_log_type=source_log_type,
        ).delete()
        return

    # 3. Create or update the consolidated journal entry
    JournalEntry.objects.update_or_create(
        project=instance.project,
        date=target_date,
        source_log_id=source_log_id,
        source_log_type=source_log_type,
        defaults={
            "category": category,
            "description": f"{prefix}: {entity.name} (Daily Total)",
            "amount": Decimal(str(total_amount)),
            "transaction_type": JournalEntry.EntryType.DEBIT,
        },
    )


def bulk_sync_all_trackers_to_journal(project):
    """
    Process all existing tracker records for a project and sync them to the Journal.
    Uses consolidated item grouping.
    """
    from app.Project.models import (
        LabourCostTracker,
        MaterialCostTracker,
        OverheadCostTracker,
        PlantCostTracker,
        SubcontractorCostTracker,
    )

    tracker_models = [
        LabourCostTracker,
        MaterialCostTracker,
        PlantCostTracker,
        OverheadCostTracker,
        SubcontractorCostTracker,
    ]

    count = 0
    with transaction.atomic():
        # First, we identify all unique (Date, Entity) combinations across all trackers
        for model in tracker_models:
            # We iterate through trackers and call the sync logic.
            # Due to update_or_create, multiple logs for same date/entity will be handled correctly.
            # However, for efficiency in bulk, we could unique them first if logs were massive.
            instances = model.objects.filter(project=project)
            processed_keys = set()
            for instance in instances:
                # Determine entity and attr for grouping
                entity_attr = ""
                if model == LabourCostTracker:
                    entity_attr = "labour_entity"
                elif model == MaterialCostTracker:
                    entity_attr = "material_entity"
                elif model == PlantCostTracker:
                    entity_attr = "plant_entity"
                elif model == OverheadCostTracker:
                    entity_attr = "overhead_entity"
                elif model == SubcontractorCostTracker:
                    entity_attr = "subcontractor_entity"

                entity = getattr(instance, entity_attr)
                key = (instance.date, entity.id, model.__name__)

                if key not in processed_keys:
                    sync_tracker_to_journal(instance)
                    processed_keys.add(key)
                    count += 1

        # Also sync revenue certificates
        count += import_certificates_to_journal(project)

    return count
