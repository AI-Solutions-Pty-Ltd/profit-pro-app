"""URL configuration for Project app."""

from django.urls import include, path

# Hard imports for all URL modules
from ..categories.category_urls import urlpatterns as category_urls
from ..categories.discipline_urls import urlpatterns as discipline_urls
from ..categories.subcategory_urls import urlpatterns as subcategory_urls
from ..company.company_urls import urlpatterns as company_urls
from ..documents.document_urls import urlpatterns as document_urls
from ..milestone_schedules.milestone_urls import urlpatterns as milestone_urls
from ..projects.category_urls import urlpatterns as project_category_urls
from ..projects.project_urls import urlpatterns as project_urls
from .compliance_urls import urlpatterns as compliance_urls
from .forecast_hub_urls import urlpatterns as forecast_hub_urls
from .planned_value_urls import urlpatterns as planned_value_urls
from .portfolio_urls import urlpatterns as portfolio_urls
from .project_role_urls import urlpatterns as project_role_urls
from .report_urls import urlpatterns as report_urls
from .risk_urls import urlpatterns as risk_urls
from .signatory_urls import urlpatterns as signatory_urls
from .user_urls import urlpatterns as user_urls

app_name = "project"
_path_prefix = "project/"


# Combine all URL patterns
urlpatterns = [
    path("portfolio/", include(portfolio_urls)),
    path("", include(project_urls)),
    path("", include(project_category_urls)),
    path("project-categories/", include(category_urls)),
    path("project-subcategories/", include(subcategory_urls)),
    path("project-discipline/", include(discipline_urls)),
    path("project-role/", include(project_role_urls)),
    path("company/", include(company_urls)),
    path("compliance/", include(compliance_urls)),
    path("document/", include(document_urls)),
    path("forecast-hub/", include(forecast_hub_urls)),
    path("milestones/", include(milestone_urls)),
    path("planned-value/", include(planned_value_urls)),
    path("report/", include(report_urls)),
    path("risk/", include(risk_urls)),
    path("signatory/", include(signatory_urls)),
    path("user/", include(user_urls)),
]
