"""URL configuration for Project Category management."""

from django.urls import path

from app.Project.views import category_views

category_urls = [
    path(
        "categories/",
        category_views.ProjectCategoryListView.as_view(),
        name="category-list",
    ),
    path(
        "categories/create/",
        category_views.ProjectCategoryCreateView.as_view(),
        name="category-create",
    ),
    path(
        "categories/<int:pk>/delete/",
        category_views.ProjectCategoryDeleteView.as_view(),
        name="category-delete",
    ),
]
