from django.urls import path

from app.Project.views import portfolio_views

portfolio_urls = [
    path(
        "portfolio/",
        portfolio_views.PortfolioDashboardView.as_view(),
        name="portfolio-list",
    ),
]
