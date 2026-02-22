from django.urls import path

from app.BillOfQuantities.views import correspondence_views

# Contractual Correspondences
correspondence_urls = [
    path(
        "project/<int:project_pk>/correspondences/",
        correspondence_views.CorrespondenceListView.as_view(),
        name="correspondence-list",
    ),
    path(
        "project/<int:project_pk>/correspondences/new/",
        correspondence_views.CorrespondenceCreateView.as_view(),
        name="correspondence-create",
    ),
    path(
        "project/<int:project_pk>/correspondences/<int:pk>/",
        correspondence_views.CorrespondenceDetailView.as_view(),
        name="correspondence-detail",
    ),
    path(
        "project/<int:project_pk>/correspondences/<int:pk>/edit/",
        correspondence_views.CorrespondenceUpdateView.as_view(),
        name="correspondence-edit",
    ),
    path(
        "project/<int:project_pk>/correspondences/<int:pk>/delete/",
        correspondence_views.CorrespondenceDeleteView.as_view(),
        name="correspondence-delete",
    ),
    path(
        "project/<int:project_pk>/correspondences/<int:pk>/dialog/",
        correspondence_views.CorrespondenceDialog.as_view(),
        name="correspondence-dialog",
    ),
]
