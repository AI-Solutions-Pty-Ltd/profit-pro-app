"""URL routes for notices."""

from django.urls import path

from app.Notices import views

app_name = "notices"

urlpatterns = [
    path("", views.NoticeListView.as_view(), name="list"),
    path("<int:pk>/", views.NoticeDetailView.as_view(), name="detail"),
    path("create/", views.NoticeCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.NoticeUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.NoticeDeleteView.as_view(), name="delete"),
]
