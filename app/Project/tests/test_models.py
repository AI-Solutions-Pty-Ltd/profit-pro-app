"""Tests for Project models."""

import time

import pytest
from django.db import IntegrityError

from app.Account.tests.factories import AccountFactory
from app.Project.models import Project
from app.Project.tests.factories import ProjectFactory


class TestProjectModel:
    """Test cases for Project model."""

    def test_project_creation(self):
        """Test creating a project with valid data."""
        project = ProjectFactory.create(name="New Project")
        assert project.id is not None
        assert project.name == "New Project"
        assert project.users.exists()
        assert project.created_at is not None
        assert project.updated_at is not None
        assert project.deleted is False

    def test_project_str_representation(self):
        """Test the string representation of a project."""
        project = ProjectFactory.create(name="Test Project")
        assert str(project) == "Test Project"

    def test_project_ordering(self):
        """Test that projects are ordered by name in descending order."""
        account = AccountFactory()
        project_a = ProjectFactory.create(account=account, name="A Project")
        project_b = ProjectFactory.create(account=account, name="B Project")
        project_c = ProjectFactory.create(account=account, name="C Project")

        projects = list(Project.objects.all())
        assert projects[0] == project_c
        assert projects[1] == project_b
        assert projects[2] == project_a

    def test_project_account_relationship(self):
        """Test the relationship between project and account."""
        account = AccountFactory.create()
        project = ProjectFactory.create(users=(account,))
        assert project.users.first() == account

        assert project in account.projects.all()

    def test_project_cascade_delete(self):
        """Test that projects are deleted when account is deleted."""
        account = AccountFactory.create()
        project = ProjectFactory.create(users=(account,), name="Test Project")
        project_id = project.id

        account.delete()

        assert not Project.objects.filter(id=project_id).exists()

    def test_project_soft_delete(self):
        """Test soft delete functionality."""
        project = ProjectFactory.create()
        project.soft_delete()
        project.refresh_from_db()

        assert project.deleted is True
        assert project.is_deleted is True

    def test_project_restore(self):
        """Test restore functionality after soft delete."""
        project = ProjectFactory.create()
        project.soft_delete()
        project.refresh_from_db()
        assert project.deleted is True

        project.restore()
        project.refresh_from_db()
        assert project.deleted is False
        assert project.is_deleted is False

    def test_project_meta_verbose_names(self):
        """Test the meta verbose names."""
        assert Project._meta.verbose_name == "Project"
        assert Project._meta.verbose_name_plural == "Projects"

    def test_project_name_max_length(self):
        """Test that project name respects max_length constraint."""
        max_length = Project._meta.get_field("name").max_length  # type: ignore
        assert max_length == 255

        # Test with name at max length
        long_name = "A" * 255
        project = ProjectFactory.create(name=long_name)
        assert len(project.name) == 255

    def test_project_required_fields(self):
        """Test that required fields cannot be null."""
        # Test missing name
        account = AccountFactory()
        with pytest.raises(IntegrityError):
            Project.objects.create(account=account, name=None)

    def test_project_account_required(self):
        """Test that account field is required."""
        with pytest.raises(IntegrityError):
            Project.objects.create(name="Test Project", account=None)

    def test_multiple_projects_same_account(self):
        """Test that an account can have multiple projects."""
        account = AccountFactory.create()
        project1 = ProjectFactory.create(account=account, name="Project 1")
        project2 = ProjectFactory.create(account=account, name="Project 2")
        project3 = ProjectFactory.create(account=account, name="Project 3")

        assert account.projects.count() == 3
        assert project1 in account.projects.all()
        assert project2 in account.projects.all()
        assert project3 in account.projects.all()

    def test_project_timestamps_auto_update(self):
        """Test that updated_at timestamp changes on save."""
        project = ProjectFactory.create()
        time.sleep(0.5)
        original_updated_at = project.updated_at
        project.name = "Updated Project Name"
        project.save()
        project.refresh_from_db()

        assert project.updated_at > original_updated_at
        assert project.created_at != project.updated_at

    def test_project_urls(self):
        """Test project urls."""
        project = ProjectFactory.create()
        assert project.get_absolute_url() == f"/project/{project.id}/"
        assert project.get_update_url() == f"/project/{project.id}/update/"
        assert project.get_delete_url() == f"/project/{project.id}/delete/"
