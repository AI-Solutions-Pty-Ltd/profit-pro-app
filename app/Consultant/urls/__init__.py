from django.urls import include, path

app_name = "client"

urlpatterns = [
    path(
        "consultant/",
        include(("app.Consultant.urls.consultant_urls", "consultant")),
    ),
    path(
        "client-management/",
        include(("app.Consultant.urls.client_management_urls", "client-management")),
    ),
    path(
        "contractor-management/",
        include(
            ("app.Consultant.urls.contractor_management_urls", "contractor-management")
        ),
    ),
    path(
        "project-client/",
        include(("app.Consultant.urls.project_client_urls", "project-client")),
    ),
    path(
        "project-contractor/",
        include(("app.Consultant.urls.project_contractor_urls", "project-contractor")),
    ),
]
