import os

from django.contrib import admin
from django.urls import include, path

from .views import AboutView, FeaturesView, HomeView, PricingView, RegisterView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("features/", FeaturesView.as_view(), name="features"),
    path("pricing/", PricingView.as_view(), name="pricing"),
    path("about/", AboutView.as_view(), name="about"),
    path("", HomeView.as_view(), name="home"),
    path("", include("app.Account.auth_urls")),
    path("register/", RegisterView.as_view(), name="register"),
    # app urls
    path("account/", include("app.Account.urls", namespace="account")),
    path("project/", include("app.Project.urls", namespace="project")),
    path(
        "bill-of-quantities/",
        include("app.BillOfQuantities.urls", namespace="bill_of_quantities"),
    ),
    path(
        "cost/",
        include("app.Cost.urls", namespace="cost"),
    ),
    path("consultant/", include("app.Consultant.urls", namespace="consultant")),
]

if os.getenv("DJANGO_SETTINGS_MODULE") == "settings.local":
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]

# Custom error handlers
handler404 = "app.core.views.custom_404"
handler500 = "app.core.views.custom_500"
handler403 = "app.core.views.custom_403"
