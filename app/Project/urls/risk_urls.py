"""URL configuration for Risk Management."""

from django.urls import path

from app.Project.views import risk_views

urlpatterns = [
    path(
        "project/<int:project_pk>/risks/",
        risk_views.RiskListView.as_view(),
        name="risk-list",
    ),
    path(
        "project/<int:project_pk>/risks/create/",
        risk_views.RiskCreateView.as_view(),
        name="risk-create",
    ),
    path(
        "project/<int:project_pk>/risks/<int:pk>/update/",
        risk_views.RiskUpdateView.as_view(),
        name="risk-update",
    ),
    path(
        "project/<int:project_pk>/risks/<int:pk>/delete/",
        risk_views.RiskDeleteView.as_view(),
        name="risk-delete",
    ),
]
