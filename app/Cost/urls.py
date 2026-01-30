from django.urls import path

from . import views

app_name = "cost"

urlpatterns = [
    # Project cost tree view
    path(
        "project/<int:project_pk>/",
        views.ProjectCostTreeView.as_view(),
        name="project-cost-tree",
    ),
    # Bill cost detail view
    path(
        "project/<int:project_pk>/bill/<int:bill_pk>/",
        views.BillCostDetailView.as_view(),
        name="bill-cost-detail",
    ),
    # Add cost to bill
    path(
        "project/<int:project_pk>/bill/<int:bill_pk>/add/",
        views.BillCostCreateView.as_view(),
        name="bill-cost-create",
    ),
    # Add multiple costs to bill
    path(
        "project/<int:project_pk>/bill/<int:bill_pk>/add-multiple/",
        views.BillCostFormSetView.as_view(),
        name="bill-cost-formset",
    ),
    # Edit cost
    path(
        "project/<int:project_pk>/bill/<int:bill_pk>/cost/<int:cost_pk>/edit/",
        views.BillCostUpdateView.as_view(),
        name="bill-cost-update",
    ),
    # Delete cost
    path(
        "project/<int:project_pk>/bill/<int:bill_pk>/cost/<int:cost_pk>/delete/",
        views.BillCostDeleteView.as_view(),
        name="bill-cost-delete",
    ),
]
