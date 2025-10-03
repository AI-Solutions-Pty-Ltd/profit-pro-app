from app.BillOfQuantities.factories import StructureFactory
from app.BillOfQuantities.models import Structure
from app.Project.factories import ProjectFactory
from app.Project.models import Project


class TestStructureUrls:
    def test_structure_urls_authenticated(self, client, user):
        """Test all structure urls with authenticated user."""
        # Create project and structure owned by the authenticated user
        project: Project = ProjectFactory.create(account=user)
        structure: Structure = StructureFactory.create(project=project)

        detail_url = structure.get_absolute_url()
        update_url = structure.get_update_url()
        delete_url = structure.get_delete_url()

        # Test authenticated access - should all return 200
        client.force_login(user)
        assert client.get(detail_url).status_code == 200
        assert client.get(update_url).status_code == 200
        assert client.get(delete_url).status_code == 200

    def test_structure_urls_unauthenticated(self, client, user):
        """Test all structure urls with unauthenticated user."""
        # Create project and structure owned by the authenticated user
        project: Project = ProjectFactory.create(account=user)
        structure: Structure = StructureFactory.create(project=project)

        detail_url = structure.get_absolute_url()
        update_url = structure.get_update_url()
        delete_url = structure.get_delete_url()

        # Test unauthenticated access - should all return 302 (redirect to login)
        assert client.get(detail_url).status_code == 302
        assert client.get(update_url).status_code == 302
        assert client.get(delete_url).status_code == 302
