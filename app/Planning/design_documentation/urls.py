"""URL configuration for Planning & Procurement app."""

from django.urls import path

from .file_delete_views import (
    DesignCategoryFileDeleteView,
    DesignDisciplineFileDeleteView,
    DesignGroupFileDeleteView,
    DesignSubCategoryFileDeleteView,
)
from .views import (
    DesignCategoryCreateView,
    DesignCategoryDeleteView,
    DesignCategoryFileUploadView,
    DesignCategoryUpdateView,
    DesignDevelopmentOverviewView,
    DesignDisciplineCreateView,
    DesignDisciplineDeleteView,
    DesignDisciplineFileUploadView,
    DesignDisciplineUpdateView,
    DesignGroupCreateView,
    DesignGroupDeleteView,
    DesignGroupFileUploadView,
    DesignGroupUpdateView,
    DesignSubCategoryCreateView,
    DesignSubCategoryDeleteView,
    DesignSubCategoryFileUploadView,
    DesignSubCategoryUpdateView,
)

_app_name = "planning"

urlpatterns = [
    # Overview Pages
    path(
        "<int:project_pk>/overview/design-development/",
        DesignDevelopmentOverviewView.as_view(),
        name="design-development-overview",
    ),
    # Design Category (L1)
    path(
        "<int:project_pk>/design/category/create/",
        DesignCategoryCreateView.as_view(),
        name="design-category-create",
    ),
    path(
        "<int:project_pk>/design/category/<int:design_pk>/upload/",
        DesignCategoryFileUploadView.as_view(),
        name="design-category-upload",
    ),
    path(
        "<int:project_pk>/design/category/<int:pk>/edit/",
        DesignCategoryUpdateView.as_view(),
        name="design-category-edit",
    ),
    path(
        "<int:project_pk>/design/category/<int:pk>/delete/",
        DesignCategoryDeleteView.as_view(),
        name="design-category-delete",
    ),
    # Design SubCategory (L2)
    path(
        "<int:project_pk>/design/subcategory/create/",
        DesignSubCategoryCreateView.as_view(),
        name="design-subcategory-create",
    ),
    path(
        "<int:project_pk>/design/subcategory/<int:design_pk>/upload/",
        DesignSubCategoryFileUploadView.as_view(),
        name="design-subcategory-upload",
    ),
    path(
        "<int:project_pk>/design/subcategory/<int:pk>/edit/",
        DesignSubCategoryUpdateView.as_view(),
        name="design-subcategory-edit",
    ),
    path(
        "<int:project_pk>/design/subcategory/<int:pk>/delete/",
        DesignSubCategoryDeleteView.as_view(),
        name="design-subcategory-delete",
    ),
    # Design Group (L3)
    path(
        "<int:project_pk>/design/group/create/",
        DesignGroupCreateView.as_view(),
        name="design-group-create",
    ),
    path(
        "<int:project_pk>/design/group/<int:design_pk>/upload/",
        DesignGroupFileUploadView.as_view(),
        name="design-group-upload",
    ),
    path(
        "<int:project_pk>/design/group/<int:pk>/edit/",
        DesignGroupUpdateView.as_view(),
        name="design-group-edit",
    ),
    path(
        "<int:project_pk>/design/group/<int:pk>/delete/",
        DesignGroupDeleteView.as_view(),
        name="design-group-delete",
    ),
    # Design Discipline (L4)
    path(
        "<int:project_pk>/design/discipline/create/",
        DesignDisciplineCreateView.as_view(),
        name="design-discipline-create",
    ),
    path(
        "<int:project_pk>/design/discipline/<int:design_pk>/upload/",
        DesignDisciplineFileUploadView.as_view(),
        name="design-discipline-upload",
    ),
    path(
        "<int:project_pk>/design/discipline/<int:pk>/edit/",
        DesignDisciplineUpdateView.as_view(),
        name="design-discipline-edit",
    ),
    path(
        "<int:project_pk>/design/discipline/<int:pk>/delete/",
        DesignDisciplineDeleteView.as_view(),
        name="design-discipline-delete",
    ),
    # Design File Deletions
    path(
        "<int:project_pk>/design/category/file/<int:pk>/delete/",
        DesignCategoryFileDeleteView.as_view(),
        name="design-category-file-delete",
    ),
    path(
        "<int:project_pk>/design/subcategory/file/<int:pk>/delete/",
        DesignSubCategoryFileDeleteView.as_view(),
        name="design-subcategory-file-delete",
    ),
    path(
        "<int:project_pk>/design/group/file/<int:pk>/delete/",
        DesignGroupFileDeleteView.as_view(),
        name="design-group-file-delete",
    ),
    path(
        "<int:project_pk>/design/discipline/file/<int:pk>/delete/",
        DesignDisciplineFileDeleteView.as_view(),
        name="design-discipline-file-delete",
    ),
]
