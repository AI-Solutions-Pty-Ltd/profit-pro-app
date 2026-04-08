"""URL configuration for Planning & Procurement app."""

from django.urls import include, path

from .views import (
    BudgetPlanningView,
    CategoryFileDeleteView,
    CategoryFileUploadView,
    DisciplineFileDeleteView,
    DisciplineFileUploadView,
    GroupFileDeleteView,
    GroupFileUploadView,
    ScopePlanningView,
    SubCategoryFileDeleteView,
    SubCategoryFileUploadView,
)

app_name = "planning"

urlpatterns = [
    # Overview Pages
    path(
        "<int:project_pk>/scope-planning/",
        ScopePlanningView.as_view(),
        name="scope-planning",
    ),
    path(
        "<int:project_pk>/overview/budget-planning/",
        BudgetPlanningView.as_view(),
        name="budget-planning",
    ),
    # Scope File Uploads
    path(
        "<int:project_pk>/scope/category/<int:pk>/upload/",
        CategoryFileUploadView.as_view(),
        name="scope-category-upload",
    ),
    path(
        "<int:project_pk>/scope/subcategory/<int:pk>/upload/",
        SubCategoryFileUploadView.as_view(),
        name="scope-subcategory-upload",
    ),
    path(
        "<int:project_pk>/scope/group/<int:pk>/upload/",
        GroupFileUploadView.as_view(),
        name="scope-group-upload",
    ),
    path(
        "<int:project_pk>/scope/discipline/<int:pk>/upload/",
        DisciplineFileUploadView.as_view(),
        name="scope-discipline-upload",
    ),
    # Scope File Deletes
    path(
        "<int:project_pk>/scope/category/file/<int:pk>/delete/",
        CategoryFileDeleteView.as_view(),
        name="scope-category-file-delete",
    ),
    path(
        "<int:project_pk>/scope/subcategory/file/<int:pk>/delete/",
        SubCategoryFileDeleteView.as_view(),
        name="scope-subcategory-file-delete",
    ),
    path(
        "<int:project_pk>/scope/group/file/<int:pk>/delete/",
        GroupFileDeleteView.as_view(),
        name="scope-group-file-delete",
    ),
    path(
        "<int:project_pk>/scope/discipline/file/<int:pk>/delete/",
        DisciplineFileDeleteView.as_view(),
        name="scope-discipline-file-delete",
    ),
    path("work-packages/", include("app.Planning.work_packages.urls")),
    path("design-documentation/", include("app.Planning.design_documentation.urls")),
    path("tender-process/", include("app.Planning.tender_process.urls")),
    path("tender-documents/", include("app.Planning.tender_documents.urls")),
]
