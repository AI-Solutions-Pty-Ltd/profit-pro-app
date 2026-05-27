"""Test cases for lead consultant views."""

import json

from django.test import TestCase
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.Project.models import Company, ProjectRole, Role
from app.Project.tests.factories import ClientFactory, ProjectFactory


class TestRevealLeadConsultantFieldView(TestCase):
    """Test cases for RevealLeadConsultantFieldView."""

    def setUp(self):
        """Set up test data."""
        from app.Account.subscription_config import Subscription

        self.user = AccountFactory()
        self.other_user = AccountFactory(subscription=Subscription.FREE_TIER)

        self.lead_consultant = ClientFactory(
            name="Test Lead Consultant",
            type=Company.Type.LEAD_CONSULTANT,
        )

        self.project = ProjectFactory(
            name="Lead Consultant Privacy Project",
        )
        self.project.lead_consultant = self.lead_consultant
        self.project.save()

        # Grant Role.ADMIN to the main test user
        ProjectRole.objects.create(
            project=self.project, user=self.user, role=Role.ADMIN
        )

    def test_reveal_endpoint_success_for_authorized_user(self):
        self.client.force_login(self.user)

        url = reverse(
            "client:lead-consultant-management:lead-consultant-reveal-field",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.lead_consultant.pk,
            },
        )

        response = self.client.post(
            url,
            data=json.dumps({"field_name": "registration_number"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

    def test_reveal_endpoint_forbidden_for_unauthorized_user(self):
        """Test that an unauthorized user receives 403 Forbidden."""
        self.client.force_login(self.other_user)

        url = reverse(
            "client:lead-consultant-management:lead-consultant-reveal-field",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.lead_consultant.pk,
            },
        )

        response = self.client.post(
            url,
            data=json.dumps({"field_name": "registration_number"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_reveal_endpoint_bad_request_for_invalid_field(self):
        """Test that requesting an invalid or non-sensitive field returns 400."""
        self.client.force_login(self.user)

        url = reverse(
            "client:lead-consultant-management:lead-consultant-reveal-field",
            kwargs={
                "project_pk": self.project.pk,
                "company_pk": self.lead_consultant.pk,
            },
        )

        response = self.client.post(
            url,
            data=json.dumps({"field_name": "name"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
