"""Tests for special item views."""

import pytest
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.models import LineItem
from app.BillOfQuantities.tests.factories import LineItemFactory
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestSpecialItemListView:
    """Test cases for SpecialItemListView."""

    def test_special_item_list_view_requires_authentication(self, client):
        """Test that the special item list view requires authentication."""
        project = ProjectFactory.create()
        url = reverse(
            "bill_of_quantities:special-item-list", kwargs={"project_pk": project.pk}
        )
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_special_item_list_view_displays_special_items(self, client):
        """Test that the special item list view displays special items."""
        account = AccountFactory.create()
        project = ProjectFactory.create(account=account)

        # Create special items
        special_item_1 = LineItemFactory.create(
            project=project,
            special_item=True,
            structure=None,
            bill=None,
            package=None,
            item_number="SP-001",
            description="Special Item 1",
        )
        special_item_2 = LineItemFactory.create(
            project=project,
            special_item=True,
            structure=None,
            bill=None,
            package=None,
            item_number="SP-002",
            description="Special Item 2",
        )

        # Create normal item (should not appear)
        LineItemFactory.create(
            project=project,
            special_item=False,
            item_number="NORM-001",
        )

        client.force_login(account)
        url = reverse(
            "bill_of_quantities:special-item-list", kwargs={"project_pk": project.pk}
        )
        response = client.get(url)

        assert response.status_code == 200
        assert special_item_1 in response.context["special_items"]
        assert special_item_2 in response.context["special_items"]
        assert len(response.context["special_items"]) == 2


@pytest.mark.django_db
class TestSpecialItemCreateView:
    """Test cases for SpecialItemCreateView."""

    def test_special_item_create_view_requires_authentication(self, client):
        """Test that the special item create view requires authentication."""
        project = ProjectFactory.create()
        url = reverse(
            "bill_of_quantities:special-item-create", kwargs={"project_pk": project.pk}
        )
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_special_item_create_view_creates_special_item(self, client):
        """Test that the special item create view creates a special item."""
        account = AccountFactory.create()
        project = ProjectFactory.create(account=account)

        # Create some existing line items to test row_index calculation
        LineItemFactory.create(project=project, row_index=0)
        LineItemFactory.create(project=project, row_index=1)

        client.force_login(account)
        url = reverse(
            "bill_of_quantities:special-item-create", kwargs={"project_pk": project.pk}
        )

        data = {
            "item_number": "SP-001",
            "payment_reference": "PAY-001",
            "description": "Test Special Item",
            "is_work": True,
            "unit_measurement": "m2",
            "unit_price": "100.00",
            "budgeted_quantity": "10.00",
        }

        response = client.post(url, data)

        # Should redirect to list view
        assert response.status_code == 302

        # Check that special item was created
        special_item = LineItem.objects.get(item_number="SP-001")
        assert special_item.special_item is True
        assert special_item.structure is None
        assert special_item.bill is None
        assert special_item.package is None
        assert special_item.project == project
        assert special_item.row_index == 2  # Should be after existing items
        assert special_item.total_price == 1000.00  # 100 * 10

    @pytest.mark.skip(
        reason="Transaction issue with permission checking in test environment"
    )
    def test_special_item_create_sets_row_index_correctly(self, client):
        """Test that row_index starts where normal line items end."""
        account = AccountFactory.create()
        project = ProjectFactory.create(account=account)

        # Create existing line items using the factory
        LineItemFactory.create(project=project, row_index=0)
        LineItemFactory.create(project=project, row_index=1)

        client.force_login(account)
        url = reverse(
            "bill_of_quantities:special-item-create", kwargs={"project_pk": project.pk}
        )

        data = {
            "item_number": "SP-001",
            "description": "Test Special Item",
            "is_work": False,
        }

        response = client.post(url, data)
        assert response.status_code == 302

        special_item = LineItem.objects.get(item_number="SP-001")
        assert special_item.row_index == 2  # After the 2 existing items


@pytest.mark.django_db
class TestSpecialItemUpdateView:
    """Test cases for SpecialItemUpdateView."""

    def test_special_item_update_view_requires_authentication(self, client):
        """Test that the special item update view requires authentication."""
        project = ProjectFactory.create()
        special_item = LineItemFactory.create(
            project=project, special_item=True, structure=None, bill=None
        )
        url = reverse(
            "bill_of_quantities:special-item-update",
            kwargs={"project_pk": project.pk, "pk": special_item.pk},
        )
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_special_item_update_view_updates_special_item(self, client):
        """Test that the special item update view updates a special item."""
        account = AccountFactory.create()
        project = ProjectFactory.create(account=account)
        special_item = LineItemFactory.create(
            project=project,
            special_item=True,
            structure=None,
            bill=None,
            package=None,
            item_number="SP-001",
            description="Original Description",
            is_work=True,
            unit_price=100,
            budgeted_quantity=10,
        )

        client.force_login(account)
        url = reverse(
            "bill_of_quantities:special-item-update",
            kwargs={"project_pk": project.pk, "pk": special_item.pk},
        )

        data = {
            "item_number": "SP-001-UPDATED",
            "payment_reference": "PAY-001",
            "description": "Updated Description",
            "is_work": True,
            "unit_measurement": "m2",
            "unit_price": "150.00",
            "budgeted_quantity": "20.00",
        }

        response = client.post(url, data)
        assert response.status_code == 302

        # Refresh from database
        special_item.refresh_from_db()
        assert special_item.item_number == "SP-001-UPDATED"
        assert special_item.description == "Updated Description"
        assert special_item.unit_price == 150
        assert special_item.budgeted_quantity == 20
        assert special_item.total_price == 3000  # 150 * 20
        # Ensure structure and bill remain null
        assert special_item.structure is None
        assert special_item.bill is None
        assert special_item.package is None


@pytest.mark.django_db
class TestSpecialItemDeleteView:
    """Test cases for SpecialItemDeleteView."""

    def test_special_item_delete_view_requires_authentication(self, client):
        """Test that the special item delete view requires authentication."""
        project = ProjectFactory.create()
        special_item = LineItemFactory.create(
            project=project, special_item=True, structure=None, bill=None
        )
        url = reverse(
            "bill_of_quantities:special-item-delete",
            kwargs={"project_pk": project.pk, "pk": special_item.pk},
        )
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_special_item_delete_view_soft_deletes_special_item(self, client):
        """Test that the special item delete view soft deletes a special item."""
        account = AccountFactory.create()
        project = ProjectFactory.create(account=account)
        special_item = LineItemFactory.create(
            project=project,
            special_item=True,
            structure=None,
            bill=None,
            package=None,
            item_number="SP-001",
        )

        client.force_login(account)
        url = reverse(
            "bill_of_quantities:special-item-delete",
            kwargs={"project_pk": project.pk, "pk": special_item.pk},
        )

        response = client.post(url)
        assert response.status_code == 302

        # Refresh from database
        special_item.refresh_from_db()
        assert special_item.is_deleted is True
        assert special_item.deleted is not None
