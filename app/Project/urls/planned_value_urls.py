"""URL configuration for PlannedValue views."""

from django.urls import path

from app.Project.views import planned_value_views

urlpatterns = [
    path(
        "project/<int:project_pk>/planned-values/",
        planned_value_views.PlannedValueEditView.as_view(),
        name="planned-value-edit",
    ),
    path(
        "project/<int:project_pk>/cashflow-forecast/",
        planned_value_views.CashflowForecastEditView.as_view(),
        name="cashflow-forecast-edit",
    ),
    path(
        "project/<int:project_pk>/cashflow-forecast/extend/",
        planned_value_views.ExtendCashflowForecastView.as_view(),
        name="cashflow-forecast-extend",
    ),
]
