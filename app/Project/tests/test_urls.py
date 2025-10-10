from app.Project.factories import ProjectFactory
from app.Project.models import Project


class TestProjectUrls:
    def test_project_urls_authenticated(self, client, user):
        """Test all project urls with authenticated user."""
        # Create project owned by the authenticated user
        client.force_login(user)
        project: Project = ProjectFactory.create(account=user)
        list_url = Project.get_list_url()
        create_url = Project.get_create_url()
        detail_url = project.get_absolute_url()
        update_url = project.get_update_url()
        delete_url = project.get_delete_url()

        # structure related urls
        structure_upload_url = project.get_structure_upload_url()

        # Test authenticated access - should all return 200
        assert client.get(list_url).status_code == 200
        assert client.get(create_url).status_code == 200
        assert client.get(detail_url).status_code == 200
        assert client.get(update_url).status_code == 200
        assert client.get(delete_url).status_code == 200

        # structure related urls
        assert client.get(structure_upload_url).status_code == 200

    def test_project_urls_unauthenticated(self, client):
        """Test all project urls without authentication."""
        # Create project but don't log in
        project: Project = ProjectFactory.create()
        list_url = Project.get_list_url()
        create_url = Project.get_create_url()
        detail_url = project.get_absolute_url()
        update_url = project.get_update_url()
        delete_url = project.get_delete_url()

        # structure related urls
        structure_upload_url = project.get_structure_upload_url()

        # Test unauthenticated access - should redirect to login (302)
        assert client.get(list_url).status_code == 302
        assert client.get(create_url).status_code == 302
        assert client.get(detail_url).status_code == 302
        assert client.get(update_url).status_code == 302
        assert client.get(delete_url).status_code == 302

        # structure related urls
        assert client.get(structure_upload_url).status_code == 302
