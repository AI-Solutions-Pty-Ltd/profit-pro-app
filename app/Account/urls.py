from django.urls import path

from .views import user_detail_views

app_name = "account"

urlpatterns = [
    path(
        "user/<int:user_pk>/",
        user_detail_views.UserDetailView.as_view(),
        name="user-detail",
    ),
    path(
        "user/<int:user_pk>/edit/",
        user_detail_views.UserEditView.as_view(),
        name="user-edit",
    ),
    path(
        "user/<int:user_pk>/groups/add/",
        user_detail_views.UserGroupAddView.as_view(),
        name="user-group-add",
    ),
    path(
        "user/<int:user_pk>/groups/<int:group_pk>/remove/",
        user_detail_views.UserGroupRemoveView.as_view(),
        name="user-group-remove",
    ),
]
