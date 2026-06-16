import pytest
from django.db import IntegrityError
from app.Project.models import ProjectCompanyUserRole, StakeholderRole
from app.Project.tests.factories import (
    ClientFactory,
    ProjectCompanyUserRoleFactory,
    ProjectFactory,
)
from app.Account.tests.factories import AccountFactory


@pytest.mark.django_db
class TestProjectCompanyUserRoleModel:
    """Test cases for ProjectCompanyUserRole model."""

    def test_role_creation(self):
        """Test creating a project company user role with valid data."""
        project = ProjectFactory.create()
        company = ClientFactory.create()
        user = AccountFactory.create()

        role_assignment = ProjectCompanyUserRoleFactory.create(
            project=project,
            company=company,
            user=user,
            role=StakeholderRole.ADMIN,
        )

        assert role_assignment.id is not None
        assert role_assignment.project == project
        assert role_assignment.company == company
        assert role_assignment.user == user
        assert role_assignment.role == StakeholderRole.ADMIN
        assert role_assignment.created_at is not None

    def test_role_default_value(self):
        """Test default role is Capturer."""
        role_assignment = ProjectCompanyUserRoleFactory.create()
        assert role_assignment.role == StakeholderRole.CAPTURER

    def test_unique_constraint(self):
        """Test unique constraint on project, company, and user."""
        project = ProjectFactory.create()
        company = ClientFactory.create()
        user = AccountFactory.create()

        ProjectCompanyUserRoleFactory.create(
            project=project,
            company=company,
            user=user,
            role=StakeholderRole.ADMIN,
        )

        # Attempting to create another assignment with same project, company, and user should raise IntegrityError
        with pytest.raises(IntegrityError):
            ProjectCompanyUserRole.objects.create(
                project=project,
                company=company,
                user=user,
                role=StakeholderRole.SUPERVISOR,
            )

    def test_str_representation(self):
        """Test the string representation of a role assignment."""
        project = ProjectFactory.create(name="Test Project")
        company = ClientFactory.create(name="Test Client")
        user = AccountFactory.create(email="test@user.com")

        role_assignment = ProjectCompanyUserRoleFactory.create(
            project=project,
            company=company,
            user=user,
            role=StakeholderRole.SUPERVISOR,
        )

        expected_str = f"test@user.com - Test Client - Supervisor (Test Project)"
        assert str(role_assignment) == expected_str

    def test_meta_verbose_names(self):
        """Test meta verbose name options."""
        assert ProjectCompanyUserRole._meta.verbose_name == "Project Company User Role"
        assert ProjectCompanyUserRole._meta.verbose_name_plural == "Project Company User Roles"
