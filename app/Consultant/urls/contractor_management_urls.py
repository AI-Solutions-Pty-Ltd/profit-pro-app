from django.urls import path

from app.Consultant.views import contractor_management_views

app_name = "contractor-management"

urlpatterns = [
    # Contractor Allocation
    path(
        "project/<int:project_pk>/",
        contractor_management_views.ContractorListView.as_view(),
        name="contractor-list",
    ),
    path(
        "project/<int:project_pk>/create/",
        contractor_management_views.ContractorCreateView.as_view(),
        name="contractor-create",
    ),
    path(
        "project/<int:project_pk>/update/<int:pk>/",
        contractor_management_views.ContractorUpdateView.as_view(),
        name="contractor-update",
    ),
]
