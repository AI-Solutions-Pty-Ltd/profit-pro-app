from django.urls import path

from app.Consultant.views import project_contractor_views

app_name = "project-contractor"

urlpatterns = [
    # Contractor Allocation
    path(
        "project/<int:project_pk>/allocate/",
        project_contractor_views.ProjectAllocateExistingContractorView.as_view(),
        name="project-contractor-allocate",
    ),
    path(
        "project/<int:project_pk>/remove/<int:contractor_pk>/",
        project_contractor_views.ProjectContractorRemoveView.as_view(),
        name="project-contractor-remove",
    ),
]
