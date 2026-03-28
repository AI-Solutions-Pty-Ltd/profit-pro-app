"""URL configuration for Planning & Procurement app."""

from django.urls import include, path

from .views import BudgetPlanningView, ScopePlanningView

app_name = "planning"

urlpatterns = [
    # Overview Pages
    path(
        "<int:project_pk>/scope-planning/",
        ScopePlanningView.as_view(),
        name="scope-planning",
    ),
    path(
        "<int:project_pk>/overview/budget-planning/",
        BudgetPlanningView.as_view(),
        name="budget-planning",
    ),
    path("work-packages/", include("app.Planning.work_packages.urls")),
    path("design-documentation/", include("app.Planning.design_documentation.urls")),
    path("tender-process/", include("app.Planning.tender_process.urls")),
    path("tender-documents/", include("app.Planning.tender_documents.urls")),
]
