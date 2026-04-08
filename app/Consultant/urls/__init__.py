from django.urls import include, path

app_name = "client"

urlpatterns = [
    path(
        "consultant/",
        include("app.Consultant.urls.consultant_urls"),
    ),
    path(
        "client-management/",
        include("app.Consultant.urls.client_management_urls"),
    ),
    path(
        "contractor-management/",
        include("app.Consultant.urls.contractor_management_urls"),
    ),
    path(
        "project-client/",
        include("app.Consultant.urls.project_client_urls"),
    ),
    path(
        "project-contractor/",
        include("app.Consultant.urls.project_contractor_urls"),
    ),
    path(
        "project-lead-consultant/",
        include("app.Consultant.urls.project_lead_consultant_urls"),
    ),
]
