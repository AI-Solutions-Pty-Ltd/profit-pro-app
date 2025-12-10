"""URL configuration for Project app."""

from app.Project.urls.category_urls import category_urls
from app.Project.urls.client_urls import client_urls
from app.Project.urls.document_urls import document_urls
from app.Project.urls.forecast_hub_urls import forecast_hub_urls
from app.Project.urls.planned_value_urls import planned_value_urls
from app.Project.urls.portfolio_urls import portfolio_urls
from app.Project.urls.project_urls import project_urls
from app.Project.urls.signatory_urls import signatory_urls

app_name = "project"

# Combine all URL patterns
urlpatterns = (
    project_urls
    + category_urls
    + client_urls
    + document_urls
    + signatory_urls
    + planned_value_urls
    + portfolio_urls
    + forecast_hub_urls
)
