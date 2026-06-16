"""Tests for the section grouping in the Financial Risk Report."""

from decimal import Decimal

import pytest
from django.test import RequestFactory

from app.Estimator.factories import BOQItemFactory
from app.Estimator.views import PricedBoqReportView
from app.Project.tests.factories import ProjectFactory


def _build_context(project, report_type="baseline_assessment", **get_params):
    view = PricedBoqReportView()
    view.kwargs = {"project_pk": project.pk, "report_type": report_type}
    view.request = RequestFactory().get("/", get_params)
    view.object_list = view.get_queryset()
    return view.get_context_data()


@pytest.mark.django_db
class TestFinancialRiskSections:
    def test_rows_grouped_by_section_with_subtotals(self):
        project = ProjectFactory()
        # Section A: two items -> contract total 2 * (100 * 250) = 50_000
        BOQItemFactory.create_batch(
            2,
            project=project,
            section="Section A",
            contract_quantity=100,
            contract_rate=Decimal("250.00"),
        )
        # Section B: one item -> contract total 10 * 100 = 1_000
        BOQItemFactory(
            project=project,
            section="Section B",
            contract_quantity=10,
            contract_rate=Decimal("100.00"),
        )

        context = _build_context(project)
        groups = {g["section"]: g for g in context["section_groups"]}

        assert set(groups) == {"Section A", "Section B"}
        assert len(groups["Section A"]["rows"]) == 2
        assert groups["Section A"]["total_a"] == Decimal("50000.00")
        assert groups["Section B"]["total_a"] == Decimal("1000.00")
        # Grand total is unchanged by grouping.
        assert context["total_a"] == Decimal("51000.00")

    def test_section_summary_sorted_by_variance_magnitude(self):
        project = ProjectFactory()
        BOQItemFactory(
            project=project,
            section="Small",
            contract_quantity=1,
            contract_rate=Decimal("100.00"),
        )
        BOQItemFactory(
            project=project,
            section="Big",
            contract_quantity=100,
            contract_rate=Decimal("500.00"),
        )

        context = _build_context(project)
        summary = context["section_summary"]

        # Largest swing first; bar is scaled to the biggest mover (100%).
        assert summary[0]["section"] == "Big"
        assert summary[-1]["section"] == "Small"
        assert summary[0]["bar_pct"] == 100
        assert summary[-1]["bar_pct"] < 100

    def test_section_header_items_excluded(self):
        project = ProjectFactory()
        BOQItemFactory(project=project, section="Section A", is_section_header=True)
        BOQItemFactory(
            project=project,
            section="Section A",
            contract_quantity=5,
            contract_rate=Decimal("10.00"),
        )

        context = _build_context(project)
        groups = {g["section"]: g for g in context["section_groups"]}

        assert len(groups["Section A"]["rows"]) == 1
