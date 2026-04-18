import os
import django
import json
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.test')
django.setup()

from app.Project.production_progress.serializers import DailyLogReportSerializer
from app.Project.production_progress.production_models import DailyActivityEntry, DailyActivityReport
from app.Project.production_progress.factories import ProductionPlanFactory
from app.Project.models import Project
from app.Account.factories import AccountFactory

def verify_fix():
    # 1. Setup
    project = Project.objects.first()
    if not project:
        from app.Project.factories import ProjectFactory
        project = ProjectFactory()
    
    plan = ProductionPlanFactory(project=project)
    
    # 2. Test Serializer with hours_on_activity
    payload = {
        "project_id": project.id,
        "date": "2024-04-18",
        "notes": "Scratch verification",
        "entries": [
            {
                "production_plan_id": plan.id,
                "quantity": 100,
                "hours_on_activity": 8.5,
                "labour_details": {
                    "Skilled": {"number": 1, "hours": 8.5}
                },
                "plant_usage": []
            }
        ]
    }
    
    print("Testing Serializer...")
    serializer = DailyLogReportSerializer(data=payload)
    if serializer.is_valid():
        report = serializer.save()
        entry = report.entries.first()
        print(f"Saved hours_on_activity: {entry.hours_on_activity}")
        if entry.hours_on_activity == Decimal('8.50'):
            print("SUCCESS: hours_on_activity saved correctly.")
        else:
            print(f"FAILURE: hours_on_activity is {entry.hours_on_activity}, expected 8.50")
    else:
        print(f"SERIALIZER ERRORS: {serializer.errors}")

    # 3. Test View Annotation Robustness (Simulated)
    # We can't easily call the view method here, but we can verify the SQL/Logic
    # The actual verification will be in the list view.
    
if __name__ == "__main__":
    verify_fix()
