from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from .views import AboutView, FeaturesView, HomeView, PricingView, RegisterView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("features/", FeaturesView.as_view(), name="features"),
    path("pricing/", PricingView.as_view(), name="pricing"),
    path("about/", AboutView.as_view(), name="about"),
    path("", HomeView.as_view(), name="home"),
    path("", include("app.core.auth_urls")),
    path("register/", RegisterView.as_view(), name="register"),
    # app urls
    path("project/", include("app.Project.urls", namespace="project")),
    path(
        "bill-of-quantities/",
        include("app.BillOfQuantities.urls", namespace="bill-of-quantities"),
    ),
]


if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
