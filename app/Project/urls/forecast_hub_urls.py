"""URL configuration for Forecast Hub views."""

from django.urls import path

from app.Project.views import forecast_hub_views

urlpatterns = [
    # Main forecast hub
    path(
        "project/<int:project_pk>/forecasts/",
        forecast_hub_views.ForecastHubView.as_view(),
        name="forecast-hub",
    ),
    # Time Forecast tab
    path(
        "project/<int:project_pk>/forecasts/time/",
        forecast_hub_views.TimeForecastView.as_view(),
        name="time-forecast",
    ),
    # Cashflow Forecast tab
    path(
        "project/<int:project_pk>/forecasts/cashflow/",
        forecast_hub_views.CashflowForecastView.as_view(),
        name="cashflow-forecast-tab",
    ),
    # Earned Value Predictions tab
    path(
        "project/<int:project_pk>/forecasts/earned-value/",
        forecast_hub_views.EarnedValueView.as_view(),
        name="earned-value",
    ),
]
