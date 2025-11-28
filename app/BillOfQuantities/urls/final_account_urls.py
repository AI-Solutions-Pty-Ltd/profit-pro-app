from django.urls import path

from app.BillOfQuantities.views.final_account_views import FinalAccountDetailView

final_account_urls = [
    path(
        "project/<int:project_pk>/final-account/<int:pk>/",
        FinalAccountDetailView.as_view(),
        name="final-account-detail",
    ),
]
