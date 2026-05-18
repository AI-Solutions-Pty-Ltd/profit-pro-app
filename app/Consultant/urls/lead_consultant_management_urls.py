from django.urls import path

from app.Consultant.views import lead_consultant_management_views

app_name = "lead-consultant-management"

urlpatterns = [
    path(
        "project/<int:project_pk>/",
        lead_consultant_management_views.LeadConsultantListView.as_view(),
        name="lead-consultant-list",
    ),
    path(
        "project/<int:project_pk>/create/",
        lead_consultant_management_views.LeadConsultantCreateView.as_view(),
        name="lead-consultant-create",
    ),
    path(
        "project/<int:project_pk>/update/<int:pk>/",
        lead_consultant_management_views.LeadConsultantUpdateView.as_view(),
        name="lead-consultant-update",
    ),
    path(
        "project/<int:project_pk>/reveal-field/<int:company_pk>/",
        lead_consultant_management_views.RevealLeadConsultantFieldView.as_view(),
        name="lead-consultant-reveal-field",
    ),
    path(
        "project/<int:project_pk>/delete/<int:pk>/",
        lead_consultant_management_views.LeadConsultantDeleteView.as_view(),
        name="lead-consultant-delete",
    ),
]
