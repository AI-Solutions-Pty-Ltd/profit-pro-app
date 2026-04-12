"""URL configuration for Project Entity Management."""

from django.urls import path

from app.Project.views import entity_views

urlpatterns = [
    # Labour Entities
    path(
        "<int:project_pk>/entities/labour/",
        entity_views.LabourEntityListView.as_view(),
        name="entity-labour-list",
    ),
    path(
        "<int:project_pk>/entities/labour/create/",
        entity_views.LabourEntityCreateView.as_view(),
        name="entity-labour-create",
    ),
    path(
        "<int:project_pk>/entities/labour/<int:pk>/update/",
        entity_views.LabourEntityUpdateView.as_view(),
        name="entity-labour-update",
    ),
    path(
        "<int:project_pk>/entities/labour/<int:pk>/delete/",
        entity_views.LabourEntityDeleteView.as_view(),
        name="entity-labour-delete",
    ),
    # Material Entities
    path(
        "<int:project_pk>/entities/material/",
        entity_views.MaterialEntityListView.as_view(),
        name="entity-material-list",
    ),
    path(
        "<int:project_pk>/entities/material/create/",
        entity_views.MaterialEntityCreateView.as_view(),
        name="entity-material-create",
    ),
    path(
        "<int:project_pk>/entities/material/<int:pk>/update/",
        entity_views.MaterialEntityUpdateView.as_view(),
        name="entity-material-update",
    ),
    path(
        "<int:project_pk>/entities/material/<int:pk>/delete/",
        entity_views.MaterialEntityDeleteView.as_view(),
        name="entity-material-delete",
    ),
    # Plant Entities
    path(
        "<int:project_pk>/entities/plant/",
        entity_views.PlantEntityListView.as_view(),
        name="entity-plant-list",
    ),
    path(
        "<int:project_pk>/entities/plant/create/",
        entity_views.PlantEntityCreateView.as_view(),
        name="entity-plant-create",
    ),
    path(
        "<int:project_pk>/entities/plant/<int:pk>/update/",
        entity_views.PlantEntityUpdateView.as_view(),
        name="entity-plant-update",
    ),
    path(
        "<int:project_pk>/entities/plant/<int:pk>/delete/",
        entity_views.PlantEntityDeleteView.as_view(),
        name="entity-plant-delete",
    ),
    # Subcontractor Entities
    path(
        "<int:project_pk>/entities/subcontractor/",
        entity_views.SubcontractorEntityListView.as_view(),
        name="entity-subcontractor-list",
    ),
    path(
        "<int:project_pk>/entities/subcontractor/create/",
        entity_views.SubcontractorEntityCreateView.as_view(),
        name="entity-subcontractor-create",
    ),
    path(
        "<int:project_pk>/entities/subcontractor/<int:pk>/update/",
        entity_views.SubcontractorEntityUpdateView.as_view(),
        name="entity-subcontractor-update",
    ),
    path(
        "<int:project_pk>/entities/subcontractor/<int:pk>/delete/",
        entity_views.SubcontractorEntityDeleteView.as_view(),
        name="entity-subcontractor-delete",
    ),
    # Overhead Entities
    path(
        "<int:project_pk>/entities/overhead/",
        entity_views.OverheadEntityListView.as_view(),
        name="entity-overhead-list",
    ),
    path(
        "<int:project_pk>/entities/overhead/create/",
        entity_views.OverheadEntityCreateView.as_view(),
        name="entity-overhead-create",
    ),
    path(
        "<int:project_pk>/entities/overhead/<int:pk>/update/",
        entity_views.OverheadEntityUpdateView.as_view(),
        name="entity-overhead-update",
    ),
    path(
        "<int:project_pk>/entities/overhead/<int:pk>/delete/",
        entity_views.OverheadEntityDeleteView.as_view(),
        name="entity-overhead-delete",
    ),
    # API for form auto-fill
    path(
        "<int:project_pk>/entities/<str:entity_type>/<int:pk>/detail/",
        entity_views.EntityDetailView.as_view(),
        name="entity-detail-json",
    ),
]
