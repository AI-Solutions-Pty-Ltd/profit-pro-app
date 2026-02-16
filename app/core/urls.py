import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .views import (
    AboutView,
    FeaturesView,
    HomeView,
)

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("features/", FeaturesView.as_view(), name="features"),
        path("about/", AboutView.as_view(), name="about"),
        path("", HomeView.as_view(), name="home"),
        path("users/", include("app.Account.urls", namespace="users")),
        # app urls
        path("project/", include("app.Project.urls", namespace="project")),
        path(
            "bill-of-quantities/",
            include("app.BillOfQuantities.urls", namespace="bill_of_quantities"),
        ),
        path(
            "cost/",
            include("app.Cost.urls", namespace="cost"),
        ),
        path("client/", include("app.Consultant.urls", namespace="client")),
        path("ledger/", include("app.Ledger.urls", namespace="ledger")),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)

if os.getenv("DJANGO_SETTINGS_MODULE") == "settings.local":
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]

# Custom error handlers
handler404 = "app.core.views.custom_404"
handler500 = "app.core.views.custom_500"
handler403 = "app.core.views.custom_403"
