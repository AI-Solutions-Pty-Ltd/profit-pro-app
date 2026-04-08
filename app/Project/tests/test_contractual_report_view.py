"""Tests for the project-level Contractual Report view."""

from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.tests.factories import (
    ContractualCorrespondenceFactory,
    ContractVariationFactory,
)
from app.Project.models import ProjectDocument, ProjectRole, Role, Risk, RiskStatus
from app.Project.tests.factories import (
    MilestoneFactory,
    ProjectDocumentFactory,
    ProjectFactory,
)
from app.SiteManagement.models import EarlyWarning, EarlyWarningStatus


class TestContractualReportView(TestCase):
    def setUp(self):
        self.user = AccountFactory.create()
        self.project = ProjectFactory.create(users=[self.user])
        ProjectRole.objects.get_or_create(
            project=self.project, user=self.user, role=Role.ADMIN
        )
        self.client.force_login(self.user)

        self.url = reverse(
            "project:contractual-report",
            kwargs={"project_pk": self.project.pk},
        )

    def test_renders_and_includes_overview_counts(self):
        """Create sample records and confirm they show in context + HTML."""
        # Default reporting window is 1 month ending today.
        today = date.today()

        # Risks - ensure at least one open risk falls within the window
        Risk.objects.create(
            project=self.project,
            description="Risk description for test",
            raised_by=self.user,
            time_impact_days=5,
            cost_impact=1000,
            probability=50,
            mitigation_action="Mitigate by doing X",
            status=RiskStatus.OPEN,
            category=Risk.RiskCategory.OTHER,
        )

        # Variations
        v1 = ContractVariationFactory.create(project=self.project)
        v1.date_identified = today
        v1.status = v1.Status.SUBMITTED
        v1.save(update_fields=["date_identified", "status"])

        # Early warnings (no factory in repo, create directly)
        EarlyWarning.objects.create(
            project=self.project,
            to_user=self.user,
            subject="EW test",
            message="EW message",
            respond_by_date=today + timedelta(days=7),
            status=EarlyWarningStatus.OPEN,
        )

        # Documents in drawings/specifications categories
        d1 = ProjectDocumentFactory.create(
            project=self.project,
            category=ProjectDocument.DocumentCategory.DRAWINGS,
        )
        d2 = ProjectDocumentFactory.create(
            project=self.project,
            category=ProjectDocument.DocumentCategory.SPECIFICATIONS,
        )

        # Correspondence - outstanding response
        c1 = ContractualCorrespondenceFactory.create(project=self.project)
        c1.date_of_correspondence = today
        c1.requires_response = True
        c1.response_sent = False
        c1.response_due_date = today - timedelta(days=1)
        c1.save(
            update_fields=[
                "date_of_correspondence",
                "requires_response",
                "response_sent",
                "response_due_date",
            ]
        )

        # Milestone - delayed milestone in window
        m1 = MilestoneFactory.create(project=self.project)
        m1.planned_date = today
        m1.forecast_date = today + timedelta(days=10)
        m1.is_completed = False
        m1.save(update_fields=["planned_date", "forecast_date", "is_completed"])

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

        # Context checks
        self.assertIn("report_overview", resp.context)
        overview = resp.context["report_overview"]
        self.assertGreaterEqual(overview["open_risks"], 1)
        self.assertGreaterEqual(overview["pending_variations"], 1)
        self.assertGreaterEqual(overview["open_early_warnings"], 1)
        self.assertGreaterEqual(overview["docs_specs_drawings"], 2)
        self.assertGreaterEqual(overview["outstanding_responses"], 1)
        self.assertGreaterEqual(overview["overdue_outstanding_responses"], 1)
        self.assertGreaterEqual(overview["delayed_milestones"], 1)

        # HTML checks (smoke)
        html = resp.content.decode("utf-8")
        self.assertIn("Construction Contractual Report", html)
        self.assertIn("4. Risk Register (Extract)", html)
        self.assertIn("Impact Value", html)
        self.assertIn("Recommendations", html)

