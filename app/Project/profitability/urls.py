from django.urls import path

from .dashboard import views as dashboard_views
from .journal import views as journal_views
from .labour import views as labour_views
from .overheads import views as overhead_views
from .subcontractor import views as subcontractor_views
from .views import ComingSoonView, ImportLogsView

urlpatterns = [
    # Dashboard
    path(
        "<int:project_pk>/profitability/",
        dashboard_views.ProfitabilityDashboardView.as_view(),
        name="profitability-dashboard",
    ),
    path(
        "<int:project_pk>/profitability/coming-soon/<str:feature_name>/",
        ComingSoonView.as_view(),
        name="profitability-coming-soon",
    ),
    path(
        "<int:project_pk>/profitability/import/",
        ImportLogsView.as_view(),
        name="profitability-import-logs",
    ),
    # Journal Entries
    path(
        "<int:project_pk>/profitability/journal/",
        journal_views.JournalEntryListView.as_view(),
        name="profitability-journal-list",
    ),
    path(
        "<int:project_pk>/profitability/journal/create/",
        journal_views.JournalEntryCreateView.as_view(),
        name="profitability-journal-create",
    ),
    path(
        "<int:project_pk>/profitability/journal/<int:pk>/update/",
        journal_views.JournalEntryUpdateView.as_view(),
        name="profitability-journal-update",
    ),
    path(
        "<int:project_pk>/profitability/journal/<int:pk>/delete/",
        journal_views.JournalEntryDeleteView.as_view(),
        name="profitability-journal-delete",
    ),
    # Subcontractor Tracker
    path(
        "<int:project_pk>/profitability/subcontractor/",
        subcontractor_views.SubcontractorCostTrackerListView.as_view(),
        name="profitability-subcontractor-list",
    ),
    path(
        "<int:project_pk>/profitability/subcontractor/create/",
        subcontractor_views.SubcontractorCostTrackerCreateView.as_view(),
        name="profitability-subcontractor-create",
    ),
    path(
        "<int:project_pk>/profitability/subcontractor/<int:pk>/update/",
        subcontractor_views.SubcontractorCostTrackerUpdateView.as_view(),
        name="profitability-subcontractor-update",
    ),
    path(
        "<int:project_pk>/profitability/subcontractor/<int:pk>/delete/",
        subcontractor_views.SubcontractorCostTrackerDeleteView.as_view(),
        name="profitability-subcontractor-delete",
    ),
    # Labour Tracker
    path(
        "<int:project_pk>/profitability/labour/",
        labour_views.LabourCostTrackerListView.as_view(),
        name="profitability-labour-list",
    ),
    path(
        "<int:project_pk>/profitability/labour/create/",
        labour_views.LabourCostTrackerCreateView.as_view(),
        name="profitability-labour-create",
    ),
    path(
        "<int:project_pk>/profitability/labour/<int:pk>/update/",
        labour_views.LabourCostTrackerUpdateView.as_view(),
        name="profitability-labour-update",
    ),
    path(
        "<int:project_pk>/profitability/labour/<int:pk>/delete/",
        labour_views.LabourCostTrackerDeleteView.as_view(),
        name="profitability-labour-delete",
    ),
    # Overhead Tracker
    path(
        "<int:project_pk>/profitability/overhead/",
        overhead_views.OverheadCostTrackerListView.as_view(),
        name="profitability-overhead-list",
    ),
    path(
        "<int:project_pk>/profitability/overhead/create/",
        overhead_views.OverheadCostTrackerCreateView.as_view(),
        name="profitability-overhead-create",
    ),
    path(
        "<int:project_pk>/profitability/overhead/<int:pk>/update/",
        overhead_views.OverheadCostTrackerUpdateView.as_view(),
        name="profitability-overhead-update",
    ),
    path(
        "<int:project_pk>/profitability/overhead/<int:pk>/delete/",
        overhead_views.OverheadCostTrackerDeleteView.as_view(),
        name="profitability-overhead-delete",
    ),
]
