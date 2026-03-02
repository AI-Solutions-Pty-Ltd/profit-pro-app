"""URL configuration for Project Category management."""

from django.urls import path

from app.Project.views import category_views

_prefix = "categories/"

urlpatterns = [
    path(
        "",
        category_views.ProjectCategoryListView.as_view(),
        name="category-list",
    ),
    path(
        "create/",
        category_views.ProjectCategoryCreateView.as_view(),
        name="category-create",
    ),
    path(
        "<int:pk>/delete/",
        category_views.ProjectCategoryDeleteView.as_view(),
        name="category-delete",
    ),
]
