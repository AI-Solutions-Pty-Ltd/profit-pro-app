from django.contrib import admin
from django.urls import path
from .views import HomeView, FeaturesView, PricingView, AboutView, RegisterView
from django.conf import settings
from django.urls import include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("features/", FeaturesView.as_view(), name="features"),
    path("pricing/", PricingView.as_view(), name="pricing"),
    path("about/", AboutView.as_view(), name="about"),
    path("", HomeView.as_view(), name="home"),
    path("", include("app.core.auth_urls")),
    path("register/", RegisterView.as_view(), name="register"),
]


if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]