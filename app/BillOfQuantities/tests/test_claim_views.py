"""Tests for Claim views."""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.models import Claim
from app.BillOfQuantities.tests.factories import ClaimFactory, LineItemFactory
from app.Project.models import Role
from app.Project.tests.factories import (
    PlannedValueFactory,
    ProjectFactory,
    ProjectRoleFactory,
)

Account = get_user_model()


class TestClaimViews(TestCase):
    """Test cases for Claim views."""

    def setUp(self):
        """Set up test data."""
        self.user = AccountFactory.create()
        self.project = ProjectFactory.create(
            start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )
        # Create required items for project setup
        LineItemFactory.create_batch(3, project=self.project)
        PlannedValueFactory.create(project=self.project, period=date(2024, 1, 1))
        PlannedValueFactory.create(project=self.project, period=date(2024, 2, 1))

        self.client.force_login(self.user)

        # Create project role for user
        ProjectRoleFactory.create(
            user=self.user, project=self.project, role=Role.CLAIMS
        )

    def test_claim_list_view(self):
        """Test claim list view."""
        # Create some claims with different periods
        ClaimFactory.create(project=self.project, period=date(2024, 1, 1))
        ClaimFactory.create(project=self.project, period=date(2024, 2, 1))
        ClaimFactory.create(project=self.project, period=date(2024, 3, 1))

        url = reverse(
            "bill_of_quantities:claim-list", kwargs={"project_pk": self.project.pk}
        )
        response = self.client.get(url)

        assert response.status_code == 200
        assert "claims" in response.context
        assert "project" in response.context
        assert len(response.context["claims"]) == 3
        assert response.context["project"] == self.project

    def test_claim_list_view_empty(self):
        """Test claim list view with no claims."""
        url = reverse(
            "bill_of_quantities:claim-list", kwargs={"project_pk": self.project.pk}
        )
        response = self.client.get(url)

        assert response.status_code == 200
        assert len(response.context["claims"]) == 0

    def test_claim_create_view_get(self):
        """Test claim create view GET request."""
        url = reverse(
            "bill_of_quantities:claim-create", kwargs={"project_pk": self.project.pk}
        )
        response = self.client.get(url)

        assert response.status_code == 200
        assert "form" in response.context
        assert "project" in response.context
        assert response.context["title"] == "Create Claim"

    def test_claim_create_view_post_valid(self):
        """Test claim create view POST with valid data."""
        # Check initial claim count
        initial_count = Claim.objects.count()

        url = reverse(
            "bill_of_quantities:claim-create", kwargs={"project_pk": self.project.pk}
        )
        data = {
            "period": "2024-01",  # Month format for type="month" input
            "estimated_claim": "150000.00",
            "notes": "Test claim notes",
        }

        response = self.client.post(url, data)

        # Check redirect
        expected_url = reverse(
            "bill_of_quantities:claim-list", kwargs={"project_pk": self.project.pk}
        )
        assert response.status_code == 302
        assert response["Location"] == expected_url

        # Check claim count after post
        final_count = Claim.objects.count()
        assert final_count == initial_count + 1

        # The save method normalizes the period to the first day
        claim = Claim.objects.get(project=self.project, period=date(2024, 1, 1))
        assert claim.estimated_claim == 150000.00
        assert claim.notes == "Test claim notes"

    def test_claim_create_view_post_invalid(self):
        """Test claim create view POST with invalid data."""
        url = reverse(
            "bill_of_quantities:claim-create", kwargs={"project_pk": self.project.pk}
        )
        data = {
            "period": "2024-01",  # Month format for type="month" input
            "estimated_claim": "-100",  # Invalid negative amount
            "notes": "Test claim notes",
        }
        response = self.client.post(url, data)

        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["form"].errors
        assert "estimated_claim" in response.context["form"].errors

    def test_claim_update_view_get(self):
        """Test claim update view GET request."""
        claim = ClaimFactory.create(project=self.project)

        url = reverse(
            "bill_of_quantities:claim-update",
            kwargs={"project_pk": self.project.pk, "pk": claim.pk},
        )
        response = self.client.get(url)

        assert response.status_code == 200
        assert "form" in response.context
        assert "project" in response.context
        assert response.context["title"] == "Update Claim"
        assert response.context["form"].instance == claim

    def test_claim_update_view_post_valid(self):
        """Test claim update view POST with valid data."""
        claim = ClaimFactory.create(project=self.project, period=date(2024, 1, 1))

        url = reverse(
            "bill_of_quantities:claim-update",
            kwargs={"project_pk": self.project.pk, "pk": claim.pk},
        )
        data = {
            "period": "2024-02",  # Month format for type="month" input
            "estimated_claim": "200000.00",
            "notes": "Updated claim notes",
        }
        response = self.client.post(url, data)

        assert response.status_code == 302
        claim.refresh_from_db()
        assert claim.period == date(2024, 2, 1)  # Normalized to first day
        assert claim.estimated_claim == 200000.00
        assert claim.notes == "Updated claim notes"

        # Check redirect
        expected_url = reverse(
            "bill_of_quantities:claim-list", kwargs={"project_pk": self.project.pk}
        )
        assert response["Location"] == expected_url

    def test_claim_delete_view_get(self):
        """Test claim delete view GET request."""
        claim = ClaimFactory.create(project=self.project)

        url = reverse(
            "bill_of_quantities:claim-delete",
            kwargs={"project_pk": self.project.pk, "pk": claim.pk},
        )
        response = self.client.get(url)

        assert response.status_code == 200
        assert "claim" in response.context
        assert "project" in response.context

    def test_claim_delete_view_post(self):
        """Test claim delete view POST request."""
        claim = ClaimFactory.create(project=self.project)
        claim_id = claim.id

        url = reverse(
            "bill_of_quantities:claim-delete",
            kwargs={"project_pk": self.project.pk, "pk": claim.pk},
        )
        response = self.client.post(url)

        assert response.status_code == 302
        assert not Claim.objects.filter(id=claim_id).exists()

        # Check redirect
        expected_url = reverse(
            "bill_of_quantities:claim-list", kwargs={"project_pk": self.project.pk}
        )
        assert response["Location"] == expected_url

    def test_claim_permissions(self):
        """Test that users without correct permissions cannot access claims."""
        # Remove project role from user
        self.user.project_roles.all().delete()

        url = reverse(
            "bill_of_quantities:claim-list", kwargs={"project_pk": self.project.pk}
        )
        response = self.client.get(url)

        # Should be redirected (permission denied)
        assert response.status_code == 302

    def test_claim_form_date_validation(self):
        """Test that claim form validates date range based on project dates."""
        # Set project dates
        self.project.start_date = date(2024, 2, 1)
        self.project.end_date = date(2024, 6, 30)
        self.project.save()

        url = reverse(
            "bill_of_quantities:claim-create", kwargs={"project_pk": self.project.pk}
        )

        # Test period before project start
        data = {
            "period": "2024-01-01",  # Before project start
            "estimated_claim": "100000.00",
            "notes": "Test claim",
        }
        response = self.client.post(url, data)
        assert response.status_code == 200
        assert "before project start date" in str(response.content)

        # Test period after project end
        data["period"] = "2024-07-01"  # After project end
        response = self.client.post(url, data)
        assert response.status_code == 200
        assert "after project end date" in str(response.content)
