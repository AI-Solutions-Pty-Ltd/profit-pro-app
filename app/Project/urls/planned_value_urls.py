"""URL configuration for PlannedValue views."""

from django.urls import path

from app.Project.views import planned_value_views

planned_value_urls = [
    path(
        "project/<int:project_pk>/planned-values/",
        planned_value_views.PlannedValueEditView.as_view(),
        name="planned-value-edit",
    ),
]
