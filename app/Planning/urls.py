"""URL configuration for Planning & Procurement app."""

from django.urls import path

from app.Planning.views import (
    DesignCategoryCreateView,
    DesignCategoryFileUploadView,
    DesignDisciplineCreateView,
    DesignDisciplineFileUploadView,
    DesignGroupCreateView,
    DesignGroupFileUploadView,
    DesignListView,
    DesignSubCategoryCreateView,
    DesignSubCategoryFileUploadView,
    TenderDocumentCreateView,
    TenderDocumentDeleteView,
    TenderDocumentUpdateView,
    WorkPackageCreateView,
    WorkPackageDeleteView,
    WorkPackageDetailView,
    WorkPackageListView,
    WorkPackageUpdateView,
)

app_name = "planning"

urlpatterns = [
    # Work Packages
    path(
        "<int:project_pk>/work-packages/",
        WorkPackageListView.as_view(),
        name="work-package-list",
    ),
    path(
        "<int:project_pk>/work-packages/create/",
        WorkPackageCreateView.as_view(),
        name="work-package-create",
    ),
    path(
        "<int:project_pk>/work-packages/<int:pk>/",
        WorkPackageDetailView.as_view(),
        name="work-package-detail",
    ),
    path(
        "<int:project_pk>/work-packages/<int:pk>/edit/",
        WorkPackageUpdateView.as_view(),
        name="work-package-update",
    ),
    path(
        "<int:project_pk>/work-packages/<int:pk>/delete/",
        WorkPackageDeleteView.as_view(),
        name="work-package-delete",
    ),
    # Tender Documents
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/documents/create/",
        TenderDocumentCreateView.as_view(),
        name="tender-document-create",
    ),
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/documents/<int:pk>/edit/",
        TenderDocumentUpdateView.as_view(),
        name="tender-document-update",
    ),
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/documents/<int:pk>/delete/",
        TenderDocumentDeleteView.as_view(),
        name="tender-document-delete",
    ),
    # Design Development
    path(
        "<int:project_pk>/work-packages/<int:pk>/design/",
        DesignListView.as_view(),
        name="design-list",
    ),
    # Design Category (L1)
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/design/category/create/",
        DesignCategoryCreateView.as_view(),
        name="design-category-create",
    ),
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/design/category/<int:design_pk>/upload/",
        DesignCategoryFileUploadView.as_view(),
        name="design-category-upload",
    ),
    # Design SubCategory (L2)
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/design/subcategory/create/",
        DesignSubCategoryCreateView.as_view(),
        name="design-subcategory-create",
    ),
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/design/subcategory/<int:design_pk>/upload/",
        DesignSubCategoryFileUploadView.as_view(),
        name="design-subcategory-upload",
    ),
    # Design Group (L3)
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/design/group/create/",
        DesignGroupCreateView.as_view(),
        name="design-group-create",
    ),
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/design/group/<int:design_pk>/upload/",
        DesignGroupFileUploadView.as_view(),
        name="design-group-upload",
    ),
    # Design Discipline (L4)
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/design/discipline/create/",
        DesignDisciplineCreateView.as_view(),
        name="design-discipline-create",
    ),
    path(
        "<int:project_pk>/work-packages/<int:wp_pk>/design/discipline/<int:design_pk>/upload/",
        DesignDisciplineFileUploadView.as_view(),
        name="design-discipline-upload",
    ),
]
