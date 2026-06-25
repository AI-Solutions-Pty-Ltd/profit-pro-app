"""Tests for Portfolio Dashboard view filtering."""

import pytest
from django.urls import reverse

from app.Account.tests.factories import (
    MunicipalityFactory,
    ProvinceFactory,
    SuperuserFactory,
)
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestPortfolioDashboardFilters:
    """Test cases for PortfolioDashboardView filters."""

    def setup_method(self):
        """Set up testing environment with a superuser."""
        self.admin = SuperuserFactory()
        self.url = reverse("project:portfolio-dashboard")

    def test_filter_by_search_name(self, client):
        """Test searching projects by name on portfolio dashboard."""
        client.force_login(self.admin)

        p1 = ProjectFactory(name="Pretoria Construction")
        p2 = ProjectFactory(name="Durban Renovation")

        # Search for "Pretoria"
        response = client.get(self.url, data={"search": "Pretoria"})
        assert response.status_code == 200
        projects = list(response.context["projects"])
        assert p1 in projects
        assert p2 not in projects

        # Search for "Renovation"
        response = client.get(self.url, data={"search": "Renovation"})
        assert response.status_code == 200
        projects = list(response.context["projects"])
        assert p2 in projects
        assert p1 not in projects

    def test_filter_by_province(self, client):
        """Test filtering projects by province on portfolio dashboard."""
        client.force_login(self.admin)

        prov1 = ProvinceFactory(name="Gauteng")
        prov2 = ProvinceFactory(name="KwaZulu-Natal")

        mun1 = MunicipalityFactory(province=prov1)
        mun2 = MunicipalityFactory(province=prov2)

        p1 = ProjectFactory(name="Gauteng Project", area=mun1)
        p2 = ProjectFactory(name="KZN Project", area=mun2)

        # Filter by Gauteng
        response = client.get(self.url, data={"province": prov1.pk})
        assert response.status_code == 200
        projects = list(response.context["projects"])
        assert p1 in projects
        assert p2 not in projects

        # Filter by KZN
        response = client.get(self.url, data={"province": prov2.pk})
        assert response.status_code == 200
        projects = list(response.context["projects"])
        assert p2 in projects
        assert p1 not in projects

    def test_filter_by_municipality(self, client):
        """Test filtering projects by municipality on portfolio dashboard."""
        client.force_login(self.admin)

        prov = ProvinceFactory(name="Gauteng")
        mun1 = MunicipalityFactory(province=prov, municipality_name="Tshwane")
        mun2 = MunicipalityFactory(province=prov, municipality_name="Joburg")

        p1 = ProjectFactory(name="Tshwane Project", area=mun1)
        p2 = ProjectFactory(name="Joburg Project", area=mun2)

        # Filter by Tshwane
        response = client.get(self.url, data={"area": mun1.pk})
        assert response.status_code == 200
        projects = list(response.context["projects"])
        assert p1 in projects
        assert p2 not in projects

        # Filter by Joburg
        response = client.get(self.url, data={"area": mun2.pk})
        assert response.status_code == 200
        projects = list(response.context["projects"])
        assert p2 in projects
        assert p1 not in projects

    def test_filter_combination(self, client):
        """Test combining multiple filters on portfolio dashboard."""
        client.force_login(self.admin)

        prov1 = ProvinceFactory(name="Gauteng")
        prov2 = ProvinceFactory(name="Limpopo")

        mun1 = MunicipalityFactory(province=prov1)
        mun2 = MunicipalityFactory(province=prov2)

        p1 = ProjectFactory(name="Water Project GP", area=mun1)
        p2 = ProjectFactory(name="Road Project GP", area=mun1)
        p3 = ProjectFactory(name="Water Project LP", area=mun2)

        # Filter by GP province + "Water" name search
        response = client.get(self.url, data={"province": prov1.pk, "search": "Water"})
        assert response.status_code == 200
        projects = list(response.context["projects"])
        assert p1 in projects
        assert p2 not in projects
        assert p3 not in projects

    def test_go_to_project_and_filters_work_together(self, client):
        """Test that Go to Project dropdown options are filtered by active filters."""
        client.force_login(self.admin)

        prov1 = ProvinceFactory(name="Gauteng")
        prov2 = ProvinceFactory(name="Limpopo")

        mun1 = MunicipalityFactory(province=prov1)
        mun2 = MunicipalityFactory(province=prov2)

        p1 = ProjectFactory(name="GP Project", area=mun1)
        p2 = ProjectFactory(name="LP Project", area=mun2)

        # Filter by GP province
        response = client.get(self.url, data={"province": prov1.pk})
        assert response.status_code == 200

        # Retrieve the queryset of the 'projects' select field in the form
        projects_dropdown_qs = list(
            response.context["filter_form"].fields["projects"].queryset
        )

        # It should only show projects in Gauteng (p1) and not Limpopo (p2)
        assert p1 in projects_dropdown_qs
        assert p2 not in projects_dropdown_qs
