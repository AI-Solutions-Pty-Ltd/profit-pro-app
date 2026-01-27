import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .views import (
    AboutView,
    FeaturesView,
    HomeView,
    RegisterView,
)

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("features/", FeaturesView.as_view(), name="features"),
        path("about/", AboutView.as_view(), name="about"),
        path("", HomeView.as_view(), name="home"),
        path("", include("app.Account.auth_urls")),
        path("register/", RegisterView.as_view(), name="register"),
        # app urls
        path("account/", include("app.Account.urls", "account")),
        path("project/", include("app.Project.urls", "project")),
        path(
            "bill-of-quantities/",
            include("app.BillOfQuantities.urls", "bill_of_quantities"),
        ),
        path(
            "cost/",
            include("app.Cost.urls", "cost"),
        ),
        path("consultant/", include("app.Consultant.urls", "consultant")),
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
