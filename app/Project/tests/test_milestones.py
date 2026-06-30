from datetime import date

import pytest
from django.urls import reverse

from app.Project.models import Role
from app.Project.tests.factories import AccountFactory, MilestoneFactory, ProjectFactory


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
            },
        )
        assert response.status_code == 302
        assert response.url == next_url

    def test_update_respects_next_param(self, client):
        project = ProjectFactory()
        user = AccountFactory()
        project.users.add(user)
        project.project_roles.create(user=user, role=Role.ADMIN)
        milestone = MilestoneFactory(project=project)
        client.force_login(user)

        url = reverse(
            "project:milestone-update",
            kwargs={"project_pk": project.pk, "pk": milestone.pk},
        )
        next_url = "/some/redirect/url/"
        response = client.post(
            f"{url}?next={next_url}",
            {
                "name": "Updated Milestone Name",
                "planned_date": "2026-06-30",
                "sequence": 0,
            },
        )
        assert response.status_code == 302
        assert response.url == next_url

    def test_delete_respects_next_param(self, client):
        project = ProjectFactory()
        user = AccountFactory()
        project.users.add(user)
        project.project_roles.create(user=user, role=Role.ADMIN)
        milestone = MilestoneFactory(project=project)
        client.force_login(user)

        url = reverse(
            "project:milestone-delete",
            kwargs={"project_pk": project.pk, "pk": milestone.pk},
        )
        next_url = "/some/redirect/url/"
        response = client.post(f"{url}?next={next_url}")
        assert response.status_code == 302
        assert response.url == next_url


@pytest.mark.django_db
class TestMilestoneSetup:
    def test_setup_list_view(self, client):
        project = ProjectFactory()
        user = AccountFactory()
        project.users.add(user)
        project.project_roles.create(user=user, role=Role.ADMIN)
        client.force_login(user)

        url = reverse(
            "project:project-milestone-setup", kwargs={"project_pk": project.pk}
        )
        response = client.get(url)
        assert response.status_code == 200

    def test_load_default_milestones(self, client):
        project = ProjectFactory(start_date=date(2026, 6, 1))
        user = AccountFactory()
        project.users.add(user)
        project.project_roles.create(user=user, role=Role.ADMIN)
        client.force_login(user)

        url = reverse(
            "project:project-milestone-load-defaults", kwargs={"project_pk": project.pk}
        )
        response = client.post(url)
        assert response.status_code == 302
        assert project.milestones.count() == 20
        assert project.milestones.filter(name="Earthworks").exists()

    def test_milestone_form_fields_and_filtering(self):
        """Test that MilestoneForm contains only correct select fields and filters them by project."""
        from app.Project.milestone_schedules.milestone_forms import MilestoneForm
        from app.Project.tests.factories import (
            CategoryFactory,
            ProjectFactory,
            SubCategoryFactory,
        )

        project = ProjectFactory()
        category1 = CategoryFactory(project=project, name="Cat A")
        _category2 = CategoryFactory(name="Other Cat")  # Not for this project

        subcat1 = SubCategoryFactory(
            project=project, category=category1, name="SubCat A"
        )
        _subcat2 = SubCategoryFactory(name="Other SubCat")

        form = MilestoneForm(project=project)

        # Assert old date fields are removed
        assert "project_category_start_date" not in form.fields
        assert "project_category_end_date" not in form.fields
        assert "project_sub_category_start_date" not in form.fields
        assert "project_sub_category_end_date" not in form.fields
        assert "project_group_start_date" not in form.fields
        assert "project_group_end_date" not in form.fields
        assert "project_discipline_start_date" not in form.fields
        assert "project_discipline_end_date" not in form.fields

        # Assert classification select fields are present
        assert "project_category" in form.fields
        assert "project_sub_category" in form.fields
        assert "project_group" in form.fields
        assert "area" in form.fields
        assert "project_discipline" in form.fields

        # Assert querysets are filtered by project
        assert list(form.fields["project_category"].queryset) == [category1]
        assert list(form.fields["project_sub_category"].queryset) == [subcat1]
