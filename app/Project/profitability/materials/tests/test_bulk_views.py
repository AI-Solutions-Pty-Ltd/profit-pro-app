import pytest
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.Project.models import MaterialCostTracker
from app.Project.tests.factories import MaterialEntityFactory, ProjectFactory


@pytest.mark.django_db
class TestMaterialCostTrackerBulkCreateView:
    def test_get_bulk_form(self, client):
        user = AccountFactory()
        project = ProjectFactory()
        client.force_login(user)

        url = reverse(
            "project:profitability-material-bulk-create",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "header_form" in response.context
        assert "formset" in response.context

    def test_post_bulk_form_success(self, client):
        user = AccountFactory()
        project = ProjectFactory()
        material = MaterialEntityFactory(project=project)
        client.force_login(user)

        url = reverse(
            "project:profitability-material-bulk-create",
            kwargs={"project_pk": project.pk},
        )

        data = {
            "date": "2023-10-01",
            "invoice_number": "INV-123",
            "supplier": "Test Supplier",
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-material_entity": material.id,
            "form-0-quantity": "10",
            "form-0-rate": "100",
            "form-1-material_entity": material.id,
            "form-1-quantity": "5",
            "form-1-rate": "200",
        }

        response = client.post(url, data)

        assert response.status_code == 302
        assert (
            MaterialCostTracker.objects.filter(
                project=project, invoice_number="INV-123"
            ).count()
            == 2
        )

        trackers = MaterialCostTracker.objects.filter(
            project=project, invoice_number="INV-123"
        ).order_by("quantity")
        assert trackers[0].quantity == 5
        assert trackers[1].quantity == 10
        assert trackers[0].date.strftime("%Y-%m-%d") == "2023-10-01"
