"""Tests for Integrated Control views."""

from decimal import Decimal

import pytest
from django.urls import reverse

from app.Project.production_progress.factories import ProductionPlanFactory
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestIntegratedControlView:
    """Test cases for the Integrated Production Control Center view."""

    def test_integrated_control_view_no_error(self, client):
        """
        Test that the Integrated Control Center view renders without TypeError.
        Regression test for decimal.Decimal and float multiplication error.
        """
        project = ProjectFactory()
        user = project.users.first()
        client.force_login(user)

        # Create a hierarchy: Section -> Bill -> Leaf
        section = ProductionPlanFactory(
            project=project,
            node_type="SECTION",
            is_leaf=False,
            activity="Section 1",
            section="Section 1",
            quantity=Decimal("1.0"),
        )
        bill = ProductionPlanFactory(
            project=project,
            parent=section,
            node_type="BILL",
            is_leaf=False,
            activity="Bill 1",
            section="Section 1",
            bill_no="1",
            quantity=Decimal("1.0"),
        )
        ProductionPlanFactory(
            project=project,
            parent=bill,
            node_type="ACTIVITY",
            is_leaf=True,
            activity="Activity 1",
            section="Section 1",
            bill_no="1",
            quantity=Decimal("100.0"),
        )

        url = reverse(
            "project:production-integrated-control", kwargs={"project_pk": project.pk}
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "Integrated Control Center" in response.content.decode()
