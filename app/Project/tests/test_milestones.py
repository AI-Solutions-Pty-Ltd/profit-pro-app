import pytest
from django.urls import reverse
from app.Project.tests.factories import ProjectFactory, MilestoneFactory, AccountFactory
from app.Project.models import Role

@pytest.mark.django_db
class TestMilestoneRedirects:
    def test_create_respects_next_param(self, client):
        project = ProjectFactory()
        user = AccountFactory()
        project.users.add(user)
        # Grant permission
        project.project_roles.create(user=user, role=Role.ADMIN)
        client.force_login(user)

        url = reverse("project:milestone-create", kwargs={"project_pk": project.pk})
        next_url = "/some/redirect/url/"
        response = client.post(
            f"{url}?next={next_url}",
            {
                "name": "New Test Milestone",
                "planned_date": "2026-06-30",
                "sequence": 0,
            }
        )
        assert response.status_code == 302
        assert response.url == next_url
