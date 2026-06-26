import pytest
from django.urls import reverse

from app.Project.models import ProjectRole, Role
from app.Project.projects.category_forms import (
    CategoryScopeDateForm,
    GroupScopeDateForm,
    SubCategoryScopeDateForm,
)
from app.Project.tests.factories import (
    AccountFactory,
    CategoryFactory,
    DisciplineFactory,
    GroupFactory,
    ProjectFactory,
    SubCategoryFactory,
)


@pytest.mark.django_db
class TestScopePlanningDateForms:
    """Test cases for the scope planning dedicated date forms."""

    def test_category_scope_date_form_fields(self):
        """Test CategoryScopeDateForm has only date fields and correct widgets."""
        form = CategoryScopeDateForm()
        assert "start_date" in form.fields
        assert "end_date" in form.fields
        assert "name" not in form.fields
        assert "description" not in form.fields
        assert form.fields["start_date"].widget.input_type == "date"
        assert form.fields["end_date"].widget.input_type == "date"

    def test_subcategory_scope_date_form_fields(self):
        """Test SubCategoryScopeDateForm has only date fields."""
        form = SubCategoryScopeDateForm()
        assert "start_date" in form.fields
        assert "end_date" in form.fields
        assert "category" not in form.fields
        assert "name" not in form.fields

    def test_group_scope_date_form_fields(self):
        """Test GroupScopeDateForm has only date fields."""
        form = GroupScopeDateForm()
        assert "start_date" in form.fields
        assert "end_date" in form.fields
        assert "sub_category" not in form.fields
        assert "name" not in form.fields


@pytest.mark.django_db
class TestScopePlanningViewContext:
    """Test cases for ScopePlanningView and its context variables."""

    def setup_method(self):
        self.project = ProjectFactory()
        self.user = AccountFactory()
        self.project.users.add(self.user)
        # Assign user ADMIN role for project permissions
        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )
        self.url = reverse(
            "planning:scope-planning",
            kwargs={"project_pk": self.project.pk},
        )

    def test_scope_planning_view_context_includes_new_forms(self, client):
        """Test that ScopePlanningView context contains scope-specific date forms."""
        client.force_login(self.user)
        response = client.get(self.url)
        assert response.status_code == 200

        assert "scope_category_date_form" in response.context
        assert "scope_subcategory_date_form" in response.context
        assert "scope_group_date_form" in response.context

        assert isinstance(
            response.context["scope_category_date_form"], CategoryScopeDateForm
        )
        assert isinstance(
            response.context["scope_subcategory_date_form"], SubCategoryScopeDateForm
        )
        assert isinstance(response.context["scope_group_date_form"], GroupScopeDateForm)

    def test_scope_planning_renders_disciplines(self, client):
        """Test that Category, SubCategory, and Group render assigned disciplines in scope_planning.html."""
        client.force_login(self.user)

        discipline1 = DisciplineFactory(project=self.project, name="Civil Discipline")
        discipline2 = DisciplineFactory(
            project=self.project, name="Electrical Discipline"
        )

        category = CategoryFactory(project=self.project, name="L1 Category A")
        category.disciplines.add(discipline1)

        subcategory = SubCategoryFactory(
            category=category, project=self.project, name="L2 SubCategory B"
        )
        subcategory.disciplines.add(discipline2)

        group = GroupFactory(
            sub_category=subcategory, project=self.project, name="L3 Group C"
        )
        group.disciplines.add(discipline1)

        response = client.get(self.url)
        assert response.status_code == 200

        content = response.content.decode("utf-8")

        # Verify disciplines are displayed under category, subcategory, and group
        assert "Civil Discipline" in content
        assert "Electrical Discipline" in content


@pytest.mark.django_db
class TestScopeDateUpdateAPI:
    """Test cases for category, subcategory, and group date update endpoints."""

    def setup_method(self):
        self.project = ProjectFactory()
        self.user = AccountFactory()
        self.project.users.add(self.user)
        # Assign user ADMIN role for project permissions
        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )

    def test_category_date_update(self, client):
        """Test updating category start and end dates via JSON post."""
        client.force_login(self.user)
        category = CategoryFactory(project=self.project, name="Category A")

        url = reverse(
            "project:project-category-update-dates",
            kwargs={"project_pk": self.project.pk, "pk": category.pk},
        )

        data = {"start_date": "2026-07-01", "end_date": "2026-12-31"}

        response = client.post(url, data=data, content_type="application/json")
        assert response.status_code == 200
        assert response.json()["success"] is True

        category.refresh_from_db()
        assert str(category.start_date) == "2026-07-01"
        assert str(category.end_date) == "2026-12-31"

    def test_subcategory_date_update(self, client):
        """Test updating subcategory start and end dates via JSON post."""
        client.force_login(self.user)
        category = CategoryFactory(project=self.project, name="Category A")
        subcategory = SubCategoryFactory(
            category=category, project=self.project, name="Subcategory B"
        )

        url = reverse(
            "project:project-subcategory-update-dates",
            kwargs={
                "project_pk": self.project.pk,
                "category_pk": category.pk,
                "pk": subcategory.pk,
            },
        )

        data = {"start_date": "2026-08-01", "end_date": "2026-11-30"}

        response = client.post(url, data=data, content_type="application/json")
        assert response.status_code == 200
        assert response.json()["success"] is True

        subcategory.refresh_from_db()
        assert str(subcategory.start_date) == "2026-08-01"
        assert str(subcategory.end_date) == "2026-11-30"

    def test_group_date_update(self, client):
        """Test updating group start and end dates via JSON post."""
        client.force_login(self.user)
        category = CategoryFactory(project=self.project, name="Category A")
        subcategory = SubCategoryFactory(
            category=category, project=self.project, name="Subcategory B"
        )
        group = GroupFactory(
            sub_category=subcategory, project=self.project, name="Group C"
        )

        url = reverse(
            "project:project-group-update-dates",
            kwargs={
                "project_pk": self.project.pk,
                "subcategory_pk": subcategory.pk,
                "pk": group.pk,
            },
        )

        data = {"start_date": "2026-09-01", "end_date": "2026-10-31"}

        response = client.post(url, data=data, content_type="application/json")
        assert response.status_code == 200
        assert response.json()["success"] is True

        group.refresh_from_db()
        assert str(group.start_date) == "2026-09-01"
        assert str(group.end_date) == "2026-10-31"


@pytest.mark.django_db
class TestScopeDisciplinesUpdateAPI:
    """Test cases for category, subcategory, and group disciplines assignment endpoints."""

    def setup_method(self):
        self.project = ProjectFactory()
        self.user = AccountFactory()
        self.project.users.add(self.user)
        # Assign user ADMIN role for project permissions
        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )
        self.discipline1 = DisciplineFactory(project=self.project, name="Civil")
        self.discipline2 = DisciplineFactory(project=self.project, name="Structural")

    def test_category_disciplines_update(self, client):
        """Test assigning disciplines to a category."""
        client.force_login(self.user)
        category = CategoryFactory(project=self.project, name="Category A")

        url = reverse(
            "project:project-category-update-disciplines",
            kwargs={"project_pk": self.project.pk, "pk": category.pk},
        )

        data = {"disciplines": [self.discipline1.pk, self.discipline2.pk]}

        response = client.post(url, data=data, content_type="application/json")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert set(response.json()["disciplines"]) == {
            self.discipline1.pk,
            self.discipline2.pk,
        }

        category.refresh_from_db()
        assert category.disciplines.count() == 2
        assert self.discipline1 in category.disciplines.all()
        assert self.discipline2 in category.disciplines.all()

    def test_subcategory_disciplines_update(self, client):
        """Test assigning disciplines to a subcategory."""
        client.force_login(self.user)
        category = CategoryFactory(project=self.project, name="Category A")
        subcategory = SubCategoryFactory(
            category=category, project=self.project, name="Subcategory B"
        )

        url = reverse(
            "project:project-subcategory-update-disciplines",
            kwargs={
                "project_pk": self.project.pk,
                "category_pk": category.pk,
                "pk": subcategory.pk,
            },
        )

        data = {"disciplines": [self.discipline1.pk]}

        response = client.post(url, data=data, content_type="application/json")
        assert response.status_code == 200
        assert response.json()["success"] is True

        subcategory.refresh_from_db()
        assert subcategory.disciplines.count() == 1
        assert self.discipline1 in subcategory.disciplines.all()

    def test_group_disciplines_update(self, client):
        """Test assigning disciplines to a group."""
        client.force_login(self.user)
        category = CategoryFactory(project=self.project, name="Category A")
        subcategory = SubCategoryFactory(
            category=category, project=self.project, name="Subcategory B"
        )
        group = GroupFactory(
            sub_category=subcategory, project=self.project, name="Group C"
        )

        url = reverse(
            "project:project-group-update-disciplines",
            kwargs={
                "project_pk": self.project.pk,
                "subcategory_pk": subcategory.pk,
                "pk": group.pk,
            },
        )

        data = {"disciplines": [self.discipline2.pk]}

        response = client.post(url, data=data, content_type="application/json")
        assert response.status_code == 200
        assert response.json()["success"] is True

        group.refresh_from_db()
        assert group.disciplines.count() == 1
        assert self.discipline2 in group.disciplines.all()


@pytest.mark.django_db
class TestScopeBudgetUpdateAPI:
    """Test cases for category, subcategory, and group budget update endpoints."""

    def setup_method(self):
        self.project = ProjectFactory()
        self.user = AccountFactory()
        self.project.users.add(self.user)
        # Assign user ADMIN role for project permissions
        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )

    def test_category_budget_update(self, client):
        """Test updating category budget fields via JSON post."""
        client.force_login(self.user)
        category = CategoryFactory(project=self.project, name="Category A")

        url = reverse(
            "project:project-category-update-budget",
            kwargs={"project_pk": self.project.pk, "pk": category.pk},
        )

        data = {
            "budget": 10000.00,
            "supply_only": 2000.00,
            "install_only": 3000.00,
            "preliminaries": 5000.00,
        }

        response = client.post(url, data=data, content_type="application/json")
        assert response.status_code == 200
        assert response.json()["success"] is True

        category.refresh_from_db()
        assert float(category.budget) == 10000.00
        assert float(category.supply_only) == 2000.00
        assert float(category.install_only) == 3000.00
        assert float(category.preliminaries) == 5000.00

    def test_subcategory_budget_update(self, client):
        """Test updating subcategory budget fields via JSON post."""
        client.force_login(self.user)
        category = CategoryFactory(project=self.project, name="Category A")
        subcategory = SubCategoryFactory(
            category=category, project=self.project, name="Subcategory B"
        )

        url = reverse(
            "project:project-subcategory-update-budget",
            kwargs={
                "project_pk": self.project.pk,
                "category_pk": category.pk,
                "pk": subcategory.pk,
            },
        )

        data = {
            "budget": 5000.00,
            "supply_only": 1000.00,
            "install_only": 1500.00,
            "preliminaries": 2500.00,
        }

        response = client.post(url, data=data, content_type="application/json")
        assert response.status_code == 200
        assert response.json()["success"] is True

        subcategory.refresh_from_db()
        assert float(subcategory.budget) == 5000.00
        assert float(subcategory.supply_only) == 1000.00
        assert float(subcategory.install_only) == 1500.00
        assert float(subcategory.preliminaries) == 2500.00

    def test_group_budget_update(self, client):
        """Test updating group budget fields via JSON post."""
        client.force_login(self.user)
        category = CategoryFactory(project=self.project, name="Category A")
        subcategory = SubCategoryFactory(
            category=category, project=self.project, name="Subcategory B"
        )
        group = GroupFactory(
            sub_category=subcategory, project=self.project, name="Group C"
        )

        url = reverse(
            "project:project-group-update-budget",
            kwargs={
                "project_pk": self.project.pk,
                "subcategory_pk": subcategory.pk,
                "pk": group.pk,
            },
        )

        data = {
            "budget": 2000.00,
            "supply_only": 400.00,
            "install_only": 600.00,
            "preliminaries": 1000.00,
        }

        response = client.post(url, data=data, content_type="application/json")
        assert response.status_code == 200
        assert response.json()["success"] is True

        group.refresh_from_db()
        assert float(group.budget) == 2000.00
        assert float(group.supply_only) == 400.00
        assert float(group.install_only) == 600.00
        assert float(group.preliminaries) == 1000.00
