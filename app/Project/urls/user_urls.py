from django.urls import path

from app.Project.views import user_views

urlpatterns = [
    # Project User Management
    path(
        "project/<int:pk>/users/",
        user_views.ProjectUserListView.as_view(),
        name="project-users",
    ),
    path(
        "project/<int:pk>/users/<int:user_pk>/",
        user_views.ProjectUserDetailView.as_view(),
        name="project-user-detail",
    ),
    path(
        "project/<int:pk>/users/add/",
        user_views.ProjectUserAddView.as_view(),
        name="project-user-add",
    ),
    path(
        "project/<int:pk>/users/create/",
        user_views.ProjectUserCreateView.as_view(),
        name="project-user-create",
    ),
    path(
        "project/<int:pk>/users/<int:user_pk>/remove/",
        user_views.ProjectUserRemoveView.as_view(),
        name="project-user-remove",
    ),
]
