from django.urls import path

from app.Project.views import contractor_company_views

contractor_urls = [
    path(
        "<int:project_pk>/contractor/list/",
        contractor_company_views.ContractorListView.as_view(),
        name="contractor-list",
    ),
    path(
        "<int:project_pk>/contractor/create/",
        contractor_company_views.ContractorCreateView.as_view(),
        name="contractor-create",
    ),
    path(
        "<int:project_pk>/contractor/<int:pk>/update/",
        contractor_company_views.ContractorUpdateView.as_view(),
        name="contractor-update",
    ),
    path(
        "<int:project_pk>/contractor/<int:pk>/delete/",
        contractor_company_views.ContractorDeleteView.as_view(),
        name="contractor-delete",
    ),
    path(
        "<int:pk>/contractor/update/",
        contractor_company_views.ProjectAllocateContractorView.as_view(),
        name="project-contractor-update",
    ),
]
