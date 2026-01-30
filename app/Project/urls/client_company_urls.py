from django.urls import path

from app.Project.views import allocate_client_view, client_company_views, client_views

client_company_urls = [
    # Client Company Management
    path(
        "<int:project_pk>/client/list/",
        client_company_views.ClientListView.as_view(),
        name="client-list",
    ),
    path(
        "<int:project_pk>/client/create/",
        client_company_views.ClientCreateView.as_view(),
        name="client-create",
    ),
    path(
        "<int:project_pk>/client/<int:pk>/update/",
        client_company_views.ClientUpdateView.as_view(),
        name="client-update",
    ),
    path(
        "<int:project_pk>/client/<int:pk>/delete/",
        client_company_views.ClientDeleteView.as_view(),
        name="client-delete",
    ),
    # Client Allocation
    path(
        "<int:pk>/client/allocate/",
        allocate_client_view.ProjectAllocateClientView.as_view(),
        name="client-allocate",
    ),
    # Client User Management (kept from old system)
    path(
        "<int:project_pk>/client/<int:pk>/invite-user/",
        client_views.ClientInviteUserView.as_view(),
        name="client-invite-user",
    ),
    path(
        "<int:project_pk>/client/<int:pk>/resend-invite/",
        client_views.ClientResendInviteView.as_view(),
        name="client-resend-invite",
    ),
    path(
        "<int:project_pk>/client/<int:pk>/remove-user/",
        client_views.ClientRemoveUserView.as_view(),
        name="client-remove-user",
    ),
]
