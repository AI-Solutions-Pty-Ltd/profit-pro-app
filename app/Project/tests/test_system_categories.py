"""Tests for global category management moved to System Library."""

import pytest
from django.urls import NoReverseMatch, reverse

from app.Account.tests.factories import AccountFactory


@pytest.mark.django_db
class TestSystemCategoriesAccess:
    """Test access control for System Library category views."""

    def setup_method(self):
        self.staff_user = AccountFactory(is_staff=True)
        self.regular_user = AccountFactory(is_staff=False)
        self.system_urls = [
            ("estimator:sys_sectors", "estimator:sys_sector_create"),
            ("estimator:sys_areas", "estimator:sys_area_create"),
            ("estimator:sys_disciplines", "estimator:sys_discipline_create"),
            ("estimator:sys_project_stages", "estimator:sys_project_stage_create"),
        ]

    def test_new_urls_resolving_and_staff_access(self, client):
        """Verify new URLs exist and are accessible only to staff."""
        client.force_login(self.staff_user)
        for list_url_name, _ in self.system_urls:
            url = reverse(list_url_name)
            response = client.get(url)
            # Should render successfully
            assert response.status_code == 200

    def test_new_urls_deny_regular_user(self, client):
        """Verify non-staff users are denied access to the new URLs."""
        client.force_login(self.regular_user)
        for list_url_name, _ in self.system_urls:
            url = reverse(list_url_name)
            response = client.get(url)
            # Django's UserPassesTestMixin redirects non-staff or returns 403
            assert response.status_code in [302, 403]

    def test_old_urls_no_longer_resolve(self):
        """Verify old URL namespace elements no longer resolve."""
        old_names = [
            "project:category-list",
            "project:subcategory-list",
            "project:discipline-list",
            "project:project-stage-list",
        ]
        for name in old_names:
            with pytest.raises(NoReverseMatch):
                reverse(name)
