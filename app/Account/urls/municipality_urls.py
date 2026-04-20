from django.urls import path

from app.Account.views import municipality_views

app_name = "municipality"

urlpatterns = [
    path(
        "municipalities/",
        municipality_views.MunicipalityListView.as_view(),
        name="municipality_list",
    ),
]
