from django.urls import path
from .views import profitability_views

urlpatterns = [
    path("<int:project_pk>/", profitability_views.ProfitabilityDashboardView.as_view(), name="profitability-dashboard"),
    
    # Subcontractor
    path("<int:project_pk>/subcontractor/", profitability_views.SubcontractorListView.as_view(), name="profitability-subcontractor-list"),
    path("<int:project_pk>/subcontractor/add/", profitability_views.SubcontractorCreateView.as_view(), name="profitability-subcontractor-add"),

    # Labour
    path("<int:project_pk>/labour/", profitability_views.LabourListView.as_view(), name="profitability-labour-list"),
    path("<int:project_pk>/labour/add/", profitability_views.LabourCreateView.as_view(), name="profitability-labour-add"),

    # Overheads
    path("<int:project_pk>/overheads/", profitability_views.OverheadListView.as_view(), name="profitability-overhead-list"),
    path("<int:project_pk>/overheads/add/", profitability_views.OverheadCreateView.as_view(), name="profitability-overhead-add"),

    # Coming Soon generic
    path("<int:project_pk>/feature/<str:feature_name>/", profitability_views.ComingSoonView.as_view(), name="profitability-coming-soon"),
]
