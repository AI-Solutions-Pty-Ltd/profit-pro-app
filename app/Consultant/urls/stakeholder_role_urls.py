from django.urls import path
from app.Consultant.views import stakeholder_role_views

app_name = "stakeholder-role"

urlpatterns = [
    path(
        "project/<int:project_pk>/company/<int:company_pk>/allocate/",
        stakeholder_role_views.ProjectCompanyUserRoleAllocateView.as_view(),
        name="allocate",
    ),
    path(
        "project/<int:project_pk>/company/<int:company_pk>/update/<int:pk>/",
        stakeholder_role_views.ProjectCompanyUserRoleUpdateView.as_view(),
        name="update",
    ),
    path(
        "project/<int:project_pk>/company/<int:company_pk>/remove/<int:pk>/",
        stakeholder_role_views.ProjectCompanyUserRoleRemoveView.as_view(),
        name="remove",
    ),
]
