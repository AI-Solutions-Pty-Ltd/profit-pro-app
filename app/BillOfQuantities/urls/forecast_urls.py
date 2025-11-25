"""URL configuration for Structure app."""

from django.urls import path

from app.BillOfQuantities.views import (
    forecast_views,
)

forecast_urls = [
    path(
        "project/<int:project_pk>/forecasts/",
        forecast_views.ForecastListView.as_view(),
        name="forecast-list",
    ),
    path(
        "project/<int:project_pk>/forecasts/create/",
        forecast_views.ForecastCreateView.as_view(),
        name="forecast-create",
    ),
    path(
        "project/<int:project_pk>/forecasts/<int:pk>/edit/",
        forecast_views.ForecastEditView.as_view(),
        name="forecast-edit",
    ),
    path(
        "project/<int:project_pk>/forecasts/<int:pk>/approve/",
        forecast_views.ForecastApproveView.as_view(),
        name="forecast-approve",
    ),
    path(
        "project/<int:project_pk>/forecasts/report/",
        forecast_views.ForecastReportView.as_view(),
        name="forecast-report",
    ),
]
