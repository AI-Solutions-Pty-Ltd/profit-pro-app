"""Tests for Production Activity views."""

from decimal import Decimal

import pytest
from django.urls import reverse

from app.Estimator.models import (
    BOQItem,
    ProjectLabourSpecification,
    ProjectPlantCost,
    ProjectPlantSpecification,
    ProjectPlantSpecificationComponent,
)
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestLaborActivityViews:
    """Test cases for Labor Activity views."""

    def test_activity_list_view_with_plant_only_item(self, client):
        """Test that BOQ items with only plant specs appear in the list."""
        project = ProjectFactory()
        user = project.users.first()
        client.force_login(user)

        # Create a plant spec
        plant_spec = ProjectPlantSpecification.objects.create(
            project=project,
            name="Excavation Plant Only",
            section="Section A",
            unit="m3",
        )

        # Create a plant cost
        plant_cost = ProjectPlantCost.objects.create(
            project=project, name="Excavator", hourly_rate=Decimal("500.00")
        )

        # Link them
        ProjectPlantSpecificationComponent.objects.create(
            specification=plant_spec, plant_type=plant_cost, hours=Decimal("1.0")
        )

        # Create a BOQ item with only plant spec
        BOQItem.objects.create(
            project=project,
            description="Plant Only Activity",
            section="Section A",
            bill_no="Bill 1",
            plant_specification=plant_spec,
            unit="m3",
            contract_quantity=Decimal("100.00"),
        )

        url = reverse("project:labor-activity-list", kwargs={"project_pk": project.pk})
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "Excavation Plant Only" in content
        # Check cost - plant hourly rate is 500. Total daily cost should be 500 (since only 1 component with 1 hour)
        # Note: In the view, plant_cost_sum is Sum('plant_specification__components__plant_type__hourly_rate')
        # Wait, the view does Sum('plant_specification__components__plant_type__hourly_rate').
        # If I have 1 component with hourly_rate 500, it should be 500.
        assert "500.00" in content

    def test_activity_list_grouping(self, client):
        """Test that items with the same name are grouped together."""
        project = ProjectFactory()
        user = project.users.first()
        client.force_login(user)

        labour_spec = ProjectLabourSpecification.objects.create(
            project=project, name="Shared Name", section="Section A", unit="m2"
        )

        # Two BOQ items with same spec (effectively same name)
        BOQItem.objects.create(
            project=project,
            description="Item 1",
            section="Section A",
            bill_no="Bill 1",
            labour_specification=labour_spec,
            unit="m2",
            contract_quantity=Decimal("100.00"),
        )
        BOQItem.objects.create(
            project=project,
            description="Item 2",
            section="Section A",
            bill_no="Bill 1",
            labour_specification=labour_spec,
            unit="m2",
            contract_quantity=Decimal("50.00"),
        )

        url = reverse("project:labor-activity-list", kwargs={"project_pk": project.pk})
        response = client.get(url)

        assert response.status_code == 200
        # Should only see "Shared Name" once in the list (as a group)
        # We can check the context 'activities' length
        activities = response.context["activities"]
        # Grouping is by (section, bill_no, act_name)
        assert len(activities) == 1
        assert activities[0]["act_name"] == "Shared Name"
        assert activities[0]["total_tracker"] == Decimal("150.00")

    def test_activity_detail_view(self, client):
        """Test the detail view with unified act_name."""
        project = ProjectFactory()
        user = project.users.first()
        client.force_login(user)

        plant_spec = ProjectPlantSpecification.objects.create(
            project=project, name="Plant Detail Test", section="Section A", unit="m3"
        )

        BOQItem.objects.create(
            project=project,
            description="Detail Test",
            section="Section A",
            bill_no="Bill 1",
            plant_specification=plant_spec,
            unit="m3",
            contract_quantity=Decimal("100.00"),
        )

        url = reverse(
            "project:labor-activity-detail", kwargs={"project_pk": project.pk}
        )
        # Add query params for act_name, section and bill_no
        response = client.get(
            f"{url}?act_name=Plant Detail Test&section=Section A&bill_no=Bill 1"
        )

        assert response.status_code == 200
        content = response.content.decode()
        assert "Plant Detail Test" in content
        assert "Section A" in content
        assert "Bill 1" in content
        assert response.context["act_unit"] == "m3"
