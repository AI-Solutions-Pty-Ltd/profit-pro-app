from django.urls import path

from app.Consultant.views import project_client_views

app_name = "project-client"

urlpatterns = [
    # Client Allocation
    path(
        "project/<int:project_pk>/allocate/",
        project_client_views.ProjectAllocateExistingClientView.as_view(),
        name="project-client-allocate",
    ),
    path(
        "project/<int:project_pk>/remove/<int:client_pk>/",
        project_client_views.ProjectClientRemoveView.as_view(),
        name="project-client-remove",
    ),
]
