"""Tests for Plant Type views."""

import pytest
from django.urls import reverse

from app.Project.models import Project
from app.Project.tests.factories import ProjectFactory
from app.SiteManagement.models import PlantType
from app.SiteManagement.tests.factories import PlantTypeFactory

pytestmark = pytest.mark.django_db


class TestPlantTypeViews:
    """Test cases for PlantType views."""

    def test_plant_type_list_view(self, client, superuser):
        """Test the list view."""
        client.force_login(superuser)
        project: Project = ProjectFactory()  # type: ignore
        project.users.add(superuser)

        PlantTypeFactory(project=project, name="Excavator")

        url = reverse(
            "site_management:plant-type-list",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "plant_types" in response.context
        assert any(pt.name == "Excavator" for pt in response.context["plant_types"])

    def test_plant_type_create_view_get(self, client, superuser):
        """Test the create view GET request (this was where the 500 error occurred)."""
        client.force_login(superuser)
        project: Project = ProjectFactory()  # type: ignore
        project.users.add(superuser)

        url = reverse(
            "site_management:plant-type-create",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

    def test_plant_type_create_view_post(self, client, superuser):
        """Test the create view POST request."""
        client.force_login(superuser)
        project: Project = ProjectFactory()  # type: ignore
        project.users.add(superuser)

        url = reverse(
            "site_management:plant-type-create",
            kwargs={"project_pk": project.pk},
        )
        data = {
            "name": "New Plant Type",
            "hourly_rate": "150.00",
        }
        response = client.post(url, data)

        assert response.status_code == 302
        assert PlantType.objects.filter(name="New Plant Type", project=project).exists()

    def test_plant_type_update_view(self, client, superuser):
        """Test the update view."""
        client.force_login(superuser)
        project: Project = ProjectFactory()  # type: ignore
        project.users.add(superuser)
        plant_type: PlantType = PlantTypeFactory(project=project, name="Old Name")  # type: ignore

        url = reverse(
            "site_management:plant-type-update",
            kwargs={"project_pk": project.pk, "pk": plant_type.pk},
        )
        data = {
            "name": "Updated Name",
            "hourly_rate": "200.00",
        }
        response = client.post(url, data)

        assert response.status_code == 302
        plant_type.refresh_from_db()
        assert plant_type.name == "Updated Name"

    def test_plant_type_delete_view(self, client, superuser):
        """Test the delete view."""
        client.force_login(superuser)
        project: Project = ProjectFactory()  # type: ignore
        project.users.add(superuser)
        plant_type: PlantType = PlantTypeFactory(project=project)  # type: ignore

        url = reverse(
            "site_management:plant-type-delete",
            kwargs={"project_pk": project.pk, "pk": plant_type.pk},
        )
        response = client.post(url)

        assert response.status_code == 302
        # Check for soft delete
        deleted_pt = PlantType.all_objects.get(pk=plant_type.pk)
        assert deleted_pt.deleted is True
