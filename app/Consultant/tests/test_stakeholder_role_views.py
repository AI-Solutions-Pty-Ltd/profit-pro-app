import pytest
from django.urls import reverse
from app.Project.models import ProjectCompanyUserRole, StakeholderRole, Role
from app.Project.tests.factories import (
    ProjectFactory,
    ClientFactory,
    ProjectCompanyUserRoleFactory,
    ProjectRoleFactory,
)
from app.Account.tests.factories import UserFactory


@pytest.mark.django_db
class TestStakeholderRoleViews:
    """Integration test cases for stakeholder user and role allocation views."""

    @pytest.fixture(autouse=True)
    def setup_method(self, client):
        self.client = client
        self.user = UserFactory.create(email="admin@test.com")
        self.project = ProjectFactory.create()
        self.company = ClientFactory.create()

        # Grant project admin role to the authenticated user
        ProjectRoleFactory.create(
            project=self.project,
            user=self.user,
            role=Role.ADMIN,
        )
        self.client.force_login(self.user)

        # Link company to the user's list of companies so it is visible in the form
        self.company.users.add(self.user)
        self.company.save()

    def test_allocate_user_role_view_get(self):
        """Test GET request to stakeholder role allocate view."""
        url = reverse(
            "client:stakeholder-role:allocate",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.company.pk,
            },
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["project"] == self.project
        assert response.context["company"] == self.company

    def test_allocate_user_role_view_post_success(self):
        """Test successful POST request to stakeholder role allocate view."""
        # Create another user belonging to the client company to assign them a role
        target_user = UserFactory.create(email="target@test.com")
        self.company.users.add(target_user)
        self.company.save()

        url = reverse(
            "client:stakeholder-role:allocate",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.company.pk,
            },
        )
        data = {
            "user": target_user.pk,
            "role": StakeholderRole.SUPERVISOR,
        }
        response = self.client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse(
            "project:project-setup", kwargs={"pk": self.project.pk}
        )

        # Verify object was created in database
        assignment = ProjectCompanyUserRole.objects.get(
            project=self.project,
            company=self.company,
            user=target_user,
        )
        assert assignment.role == StakeholderRole.SUPERVISOR

    def test_allocate_user_role_view_post_duplicate_error(self):
        """Test that duplicate assignment fails validation."""
        target_user = UserFactory.create(email="target@test.com")
        self.company.users.add(target_user)
        self.company.save()

        # Pre-create assignment
        ProjectCompanyUserRoleFactory.create(
            project=self.project,
            company=self.company,
            user=target_user,
            role=StakeholderRole.CAPTURER,
        )

        url = reverse(
            "client:stakeholder-role:allocate",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.company.pk,
            },
        )
        data = {
            "user": target_user.pk,
            "role": StakeholderRole.SUPERVISOR,
        }
        response = self.client.post(url, data)
        # Should stay on page and show form error due to integrity/duplicate check
        assert response.status_code == 200
        assert ProjectCompanyUserRole.objects.filter(
            project=self.project,
            company=self.company,
            user=target_user,
        ).count() == 1

    def test_update_user_role_view_get(self):
        """Test GET request to stakeholder role update view."""
        target_user = UserFactory.create(email="target@test.com")
        self.company.users.add(target_user)
        self.company.save()

        assignment = ProjectCompanyUserRoleFactory.create(
            project=self.project,
            company=self.company,
            user=target_user,
            role=StakeholderRole.CAPTURER,
        )

        url = reverse(
            "client:stakeholder-role:update",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.company.pk,
                "pk": assignment.pk,
            },
        )
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.context["form"].fields["user"].disabled is True

    def test_update_user_role_view_post(self):
        """Test updating stakeholder role from Capturer to Admin."""
        target_user = UserFactory.create(email="target@test.com")
        self.company.users.add(target_user)
        self.company.save()

        assignment = ProjectCompanyUserRoleFactory.create(
            project=self.project,
            company=self.company,
            user=target_user,
            role=StakeholderRole.CAPTURER,
        )

        url = reverse(
            "client:stakeholder-role:update",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.company.pk,
                "pk": assignment.pk,
            },
        )
        data = {
            "user": target_user.pk,  # disabled but still passed or fallback
            "role": StakeholderRole.ADMIN,
        }
        response = self.client.post(url, data)
        assert response.status_code == 302
        assignment.refresh_from_db()
        assert assignment.role == StakeholderRole.ADMIN

    def test_remove_user_role_view(self):
        """Test removing stakeholder role assignment."""
        target_user = UserFactory.create(email="target@test.com")
        self.company.users.add(target_user)
        self.company.save()

        assignment = ProjectCompanyUserRoleFactory.create(
            project=self.project,
            company=self.company,
            user=target_user,
            role=StakeholderRole.CAPTURER,
        )

        url = reverse(
            "client:stakeholder-role:remove",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.company.pk,
                "pk": assignment.pk,
            },
        )
        # POST/DELETE request
        response = self.client.post(url)
        assert response.status_code == 302
        assert not ProjectCompanyUserRole.objects.filter(pk=assignment.pk).exists()

    def test_view_permission_denied_for_non_admin(self):
        """Test that non-admin project user cannot access allocation views."""
        non_admin_user = UserFactory.create(email="nonadmin@test.com")
        self.client.force_login(non_admin_user)

        # Assign user role (regular User role, not ADMIN)
        ProjectRoleFactory.create(
            project=self.project,
            user=non_admin_user,
            role=Role.USER,
        )

        url = reverse(
            "client:stakeholder-role:allocate",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.company.pk,
            },
        )
        response = self.client.get(url)
        assert response.status_code == 302  # redirects due to lack of permission
