"""URL configuration for Project app."""

from django.urls import include, path

app_name = "project"

# Combine all URL patterns
urlpatterns = [
    path("category/", include("app.Project.urls.category_urls")),
    path("compliance/", include("app.Project.urls.compliance_urls")),
    path("document/", include("app.Project.urls.document_urls")),
    path("forecast-hub/", include("app.Project.urls.forecast_hub_urls")),
    path("milestone/", include("app.Project.urls.milestone_urls")),
    path("planned-value/", include("app.Project.urls.planned_value_urls")),
    path("portfolio/", include("app.Project.urls.portfolio_urls")),
    path("project-role/", include("app.Project.urls.project_role_urls")),
    path("project/", include("app.Project.urls.project_urls")),
    path("report/", include("app.Project.urls.report_urls")),
    path("risk/", include("app.Project.urls.risk_urls")),
    path("signatory/", include("app.Project.urls.signatory_urls")),
    path("user/", include("app.Project.urls.user_urls")),
]
