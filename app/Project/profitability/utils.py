from django.db import transaction

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
