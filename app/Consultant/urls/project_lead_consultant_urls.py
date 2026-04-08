from django.urls import path

from app.Consultant.views import project_lead_consultant_views

app_name = "project-lead-consultant"

urlpatterns = [
    # Lead Consultant Allocation
    path(
        "project/<int:project_pk>/allocate/",
        project_lead_consultant_views.ProjectAllocateLeadConsultantView.as_view(),
        name="project-lead-consultant-allocate",
    ),
    path(
        "project/<int:project_pk>/remove/<int:lead_consultant_pk>/",
        project_lead_consultant_views.ProjectLeadConsultantRemoveView.as_view(),
        name="project-lead-consultant-remove",
    ),
]
