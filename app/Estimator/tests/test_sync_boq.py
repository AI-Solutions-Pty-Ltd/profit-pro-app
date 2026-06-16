"""Tests for syncing Output BoQ items from BillOfQuantities line items."""

from decimal import Decimal

import pytest

from app.BillOfQuantities.tests.factories import (
    BillFactory,
    LineItemFactory,
    StructureFactory,
)
from app.Estimator.models import BOQItem, sync_boq_from_lineitems
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestSyncBoqFromLineItems:
    """Section-header classification when syncing to the Output BoQ."""

    def _project_with_bill(self):
        project = ProjectFactory()
        structure = StructureFactory(project=project)
        bill = BillFactory(structure=structure)
        return project, bill

    def test_unrated_work_item_is_not_a_section_header(self):
        """A measurable item with a quantity but no rate must still show on the
        Output BoQ as an editable row (not collapsed into a section header)."""
        project, bill = self._project_with_bill()
        # is_work is False because there is no total_price (rate blank), but the
        # row carries a quantity and unit — it just needs pricing.
        li = LineItemFactory(
            project=project,
            bill=bill,
            is_work=False,
            unit_measurement="m3",
            unit_price=Decimal("0"),
            budgeted_quantity=Decimal("10"),
            total_price=Decimal("0"),
        )

        sync_boq_from_lineitems(project)

        boq = BOQItem.objects.get(project=project, source_line_item=li)
        assert boq.is_section_header is False
        assert boq.contract_quantity == Decimal("10")

    def test_true_heading_is_a_section_header(self):
        """A genuine heading row (no quantity, no unit) stays a section header."""
        project, bill = self._project_with_bill()
        li = LineItemFactory(
            project=project,
            bill=bill,
            is_work=False,
            unit_measurement="",
            unit_price=Decimal("0"),
            budgeted_quantity=Decimal("0"),
            total_price=Decimal("0"),
        )

        sync_boq_from_lineitems(project)

        boq = BOQItem.objects.get(project=project, source_line_item=li)
        assert boq.is_section_header is True

    def test_priced_work_item_is_not_a_section_header(self):
        """A normal rated work item remains a regular BoQ row."""
        project, bill = self._project_with_bill()
        li = LineItemFactory(
            project=project,
            bill=bill,
            is_work=True,
            unit_measurement="m3",
            unit_price=Decimal("150.00"),
            budgeted_quantity=Decimal("10"),
            total_price=Decimal("1500.00"),
        )

        sync_boq_from_lineitems(project)

        boq = BOQItem.objects.get(project=project, source_line_item=li)
        assert boq.is_section_header is False
