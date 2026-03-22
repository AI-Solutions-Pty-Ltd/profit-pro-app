"""URL configuration for Forecast Hub views."""

from django.urls import path

from app.Project.views import forecast_hub_views

_path_prefix = "forecast-hub/"

urlpatterns = [
    # Time Forecast tab
    path(
        "<int:project_pk>/time/",
        forecast_hub_views.TimeForecastView.as_view(),
        name="time-forecast",
    ),
    # Budget Forecast tab
    path(
        "<int:project_pk>/budget/",
        forecast_hub_views.BudgetForecastView.as_view(),
        name="budget-forecast",
    ),
    # Cashflow Forecast tab
    path(
        "<int:project_pk>/cashflow/",
        forecast_hub_views.CashflowForecastView.as_view(),
        name="cashflow-forecast-tab",
    ),
    # Earned Value Predictions tab
    path(
        "<int:project_pk>/earned-value/",
        forecast_hub_views.EarnedValueView.as_view(),
        name="earned-value",
    ),
]
