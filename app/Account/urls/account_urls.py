from django.urls import path

from app.Account.views import account_views

app_name = "account"
_app_prefix = "users"  # reference only
_path_prefix = "users/account/"  # reference only

urlpatterns = [
    path(
        "",
        account_views.UserDetailView.as_view(),
        name="user_detail",
    ),
    path(
        "edit/",
        account_views.UserEditView.as_view(),
        name="user_edit",
    ),
]
