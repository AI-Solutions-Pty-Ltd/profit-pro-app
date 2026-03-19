"""URL configuration for Project SubCategory management."""

from django.urls import path

from app.Project.views import subcategory_views

_path_prefix = "subcategories/"

urlpatterns = [
    path(
        "",
        subcategory_views.ProjectSubCategoryListView.as_view(),
        name="subcategory-list",
    ),
    path(
        "create/",
        subcategory_views.ProjectSubCategoryCreateView.as_view(),
        name="subcategory-create",
    ),
    path(
        "<int:pk>/update/",
        subcategory_views.ProjectSubCategoryUpdateView.as_view(),
        name="subcategory-update",
    ),
    path(
        "<int:pk>/delete/",
        subcategory_views.ProjectSubCategoryDeleteView.as_view(),
        name="subcategory-delete",
    ),
]
