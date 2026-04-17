
import os
import django
import json
from django.test import RequestFactory
from django.urls import reverse

import sys
# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "settings.local"))
sys.path.append(os.getcwd())
django.setup()

from app.Project.production_progress.views.productivity_views import DailyProductivityCreateView
from app.Project.production_progress.production_models import ProductionPlan
from app.Project.models import Project

def verify_prefill():
    # We know Project 3 and Plan 26 have a crew spec (1 skilled, 2 semi, 2 unskilled)
    plan_id = 26
    project_pk = 3
    
    plan = ProductionPlan.objects.get(id=plan_id)
    print(f"Verifying Plan: {plan} (ID: {plan.id})")
    print(f"Crew Spec: Skilled={plan.labour_activity.crew.skilled}, Semi={plan.labour_activity.crew.semi_skilled}, Unskilled={plan.labour_activity.crew.general}")

    factory = RequestFactory()
    # Main view uses 'selected_plans' parameter (getlist)
    url = f"/project/{project_pk}/productivity/add/?selected_plans={plan_id}"
    request = factory.get(url)
    
    print(f"URL: {url}")
    print(f"GET params: {request.GET}")
    
    view = DailyProductivityCreateView()
    view.request = request
    view.kwargs = {'project_pk': project_pk}
    
    print(f"View Request GET: {view.request.GET}")
    print(f"View Kwargs: {view.kwargs}")
    
    context = view.get_context_data()
    labour_initial = context.get('labour_initial', [])
    
    print("\nLabour Initial Data:")
    print(json.dumps(labour_initial, indent=2))
    
    # Assertions
    assert len(labour_initial) > 0, "Initial labour data should not be empty"
    item = labour_initial[0]
    assert item['skilled_number'] == 1, f"Expected 1 skilled, got {item['skilled_number']}"
    assert item['semi_skilled_number'] == 2, f"Expected 2 semi, got {item['semi_skilled_number']}"
    assert item['unskilled_number'] == 2, f"Expected 2 unskilled, got {item['unskilled_number']}"
    assert item['total_hours'] == 8.0, f"Expected 8.0 hours, got {item['total_hours']}"
    
    plan_resources = context.get('plan_resources', {})
    plan_meta = plan_resources.get(plan_id, {})
    assert plan_meta.get('has_crew_spec') is True, "has_crew_spec should be True"
    
    print("\nVerification SUCCESS!")

if __name__ == "__main__":
    verify_prefill()
