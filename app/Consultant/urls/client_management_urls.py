from django.urls import path

from app.Consultant.views import client_management_views

app_name = "client-management"

urlpatterns = [
    # Client Allocation
    path(
        "project/<int:project_pk>/",
        client_management_views.ClientListView.as_view(),
        name="client-list",
    ),
    path(
        "project/<int:project_pk>/create/",
        client_management_views.ClientCreateView.as_view(),
        name="client-create",
    ),
    path(
        "project/<int:project_pk>/update/<int:pk>/",
        client_management_views.ClientUpdateView.as_view(),
        name="client-update",
    ),
]
