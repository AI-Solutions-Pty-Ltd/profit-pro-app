"""Tests for Bill, Package, and LineItem models."""

from decimal import Decimal

import pytest

from app.BillOfQuantities.models import Bill, LineItem, Package, PaymentCertificate
from app.BillOfQuantities.tests.factories import (
    ActualTransactionFactory,
    BillFactory,
    LineItemFactory,
    PackageFactory,
    PaymentCertificateFactory,
    StructureFactory,
)
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestBillModel:
    """Test cases for Bill model."""

    def test_bill_creation(self):
        """Test creating a bill with valid data."""
        bill = BillFactory.create()
        assert bill.id is not None
        assert bill.name is not None
        assert bill.structure is not None

    def test_bill_string_representation(self):
        """Test the __str__ method returns bill name."""
        bill = BillFactory(name="Earthworks")
        assert str(bill) == "Earthworks"

    def test_bill_structure_relationship(self):
        """Test relationship between Bill and Structure."""
        structure = StructureFactory.create()
        bill1 = BillFactory.create(structure=structure)
        bill2 = BillFactory.create(structure=structure)

        assert structure.bills.count() == 2
        assert bill1 in structure.bills.all()
        assert bill2 in structure.bills.all()

    def test_bill_cascade_delete_with_structure(self):
        """Test bills are deleted when structure is deleted."""
        structure = StructureFactory.create()
        bill = BillFactory.create(structure=structure)
        bill_id = bill.pk

        structure.delete()

        assert Bill.objects.filter(id=bill_id).count() == 0

    def test_bill_soft_delete(self):
        """Test soft delete functionality."""
        bill = BillFactory.create()
        bill.soft_delete()
        assert bill.is_deleted


@pytest.mark.django_db
class TestPackageModel:
    """Test cases for Package model."""

    def test_package_creation(self):
        """Test creating a package with valid data."""
        package = PackageFactory.create()
        assert package.id is not None
        assert package.name is not None
        assert package.bill is not None

    def test_package_string_representation(self):
        """Test the __str__ method returns package name."""
        package = PackageFactory.create(name="Foundation Package")
        assert str(package) == "Foundation Package"

    def test_package_bill_relationship(self):
        """Test relationship between Package and Bill."""
        bill = BillFactory.create()
        package1 = PackageFactory.create(bill=bill)
        package2 = PackageFactory.create(bill=bill)

        assert bill.packages.count() == 2
        assert package1 in bill.packages.all()
        assert package2 in bill.packages.all()

    def test_package_cascade_delete_with_bill(self):
        """Test packages are deleted when bill is deleted."""
        bill = BillFactory.create()
        package = PackageFactory.create(bill=bill)
        package_id = package.pk

        bill.delete()

        assert Package.objects.filter(id=package_id).count() == 0

    def test_package_soft_delete(self):
        """Test soft delete functionality."""
        package = PackageFactory.create()
        package.soft_delete()
        assert package.is_deleted


@pytest.mark.django_db
class TestLineItemModel:
    """Test cases for LineItem model."""

    def test_line_item_creation(self):
        """Test creating a line item with valid data."""
        line_item = LineItemFactory.create()
        assert line_item.id is not None
        assert line_item.project is not None
        assert line_item.structure is not None
        assert line_item.bill is not None

    def test_line_item_string_representation(self):
        """Test the __str__ method returns item number."""
        line_item = LineItemFactory.create(item_number="ITEM-123")
        assert str(line_item) == "ITEM-123"

    def test_line_item_with_package(self):
        """Test creating line item with package."""
        package = PackageFactory.create()
        line_item = LineItemFactory.create(package=package)
        assert line_item.package == package

    def test_line_item_without_package(self):
        """Test creating line item without package."""
        line_item = LineItemFactory.create(package=None)
        assert line_item.package is None

    def test_line_item_is_work_flag(self):
        """Test is_work flag for work items."""
        work_item = LineItemFactory.create(is_work=True)
        heading_item = LineItemFactory.create(is_work=False)

        assert work_item.is_work is True
        assert heading_item.is_work is False

    def test_line_item_ordering_by_row_index(self):
        """Test line items are ordered by row_index."""
        project = ProjectFactory.create()
        item3 = LineItemFactory.create(project=project, row_index=3)
        item1 = LineItemFactory.create(project=project, row_index=1)
        item2 = LineItemFactory.create(project=project, row_index=2)

        items = LineItem.objects.filter(project=project)
        assert list(items) == [item1, item2, item3]

    def test_line_item_claimed_to_date_excludes_current_certificate(self):
        """Test claimed_to_date excludes current draft certificate transactions."""
        project = ProjectFactory.create()
        line_item = LineItemFactory.create(
            project=project, budgeted_quantity=Decimal("100.00")
        )

        # Create approved certificate with claimed transaction
        approved_cert = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.APPROVED
        )
        ActualTransactionFactory.create(
            payment_certificate=approved_cert,
            line_item=line_item,
            quantity=Decimal("20.00"),
            claimed=True,
        )

        # Create draft certificate with transaction (should be excluded)
        draft_cert = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )
        ActualTransactionFactory.create(
            payment_certificate=draft_cert,
            line_item=line_item,
            quantity=Decimal("10.00"),
            claimed=False,
        )

        assert line_item.claimed_to_date == Decimal("20.00")

    def test_line_item_remaining_quantity_calculation(self):
        """Test remaining_quantity calculates correctly."""
        project = ProjectFactory.create()
        line_item = LineItemFactory.create(
            project=project, budgeted_quantity=Decimal("100.00")
        )
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.APPROVED
        )

        ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            quantity=Decimal("35.00"),
            claimed=True,
        )

        assert line_item.remaining_quantity == Decimal("65.00")

    def test_line_item_current_transaction_returns_draft_transaction(self):
        """Test current_transaction returns transaction from active draft certificate."""
        project = ProjectFactory.create()
        line_item = LineItemFactory.create(project=project)
        draft_cert = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )
        transaction = ActualTransactionFactory.create(
            payment_certificate=draft_cert, line_item=line_item
        )

        assert line_item.current_transaction == transaction

    def test_line_item_current_transaction_none_when_no_draft(self):
        """Test current_transaction returns None when no draft certificate."""
        project = ProjectFactory.create()
        line_item = LineItemFactory.create(project=project)
        approved_cert = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.APPROVED
        )
        ActualTransactionFactory.create(
            payment_certificate=approved_cert, line_item=line_item
        )

        assert line_item.current_transaction is None

    def test_line_item_addendum_flag(self):
        """Test addendum flag for addendum items."""
        addendum_item = LineItemFactory.create(addendum=True)
        regular_item = LineItemFactory.create(addendum=False)

        assert addendum_item.addendum is True
        assert regular_item.addendum is False

    def test_line_item_project_relationship(self):
        """Test relationship between LineItem and Project."""
        project = ProjectFactory.create()
        item1 = LineItemFactory.create(project=project)
        item2 = LineItemFactory.create(project=project)

        assert project.line_items.count() == 2
        assert item1 in project.line_items.all()
        assert item2 in project.line_items.all()

    def test_line_item_soft_delete(self):
        """Test soft delete functionality."""
        line_item = LineItemFactory.create()
        line_item.soft_delete()
        assert line_item.is_deleted

    def test_line_item_with_blank_optional_fields(self):
        """Test creating line item with blank optional fields."""
        line_item = LineItemFactory.create(
            item_number="",
            payment_reference="",
            description="",
            unit_measurement="",
            package=None,
        )
        assert line_item.item_number == ""
        assert line_item.payment_reference == ""
        assert line_item.description == ""
        assert line_item.unit_measurement == ""
        assert line_item.package is None

    def test_construct_payment_certificate_with_no_transactions(self):
        """Test construct_payment_certificate with no transactions."""
        project = ProjectFactory.create()
        LineItemFactory.create(project=project)
        LineItemFactory.create(project=project)
        certificate = PaymentCertificateFactory.create(
            project=project, certificate_number=1
        )

        result = LineItem.construct_payment_certificate(certificate)

        assert len(result) == 2
        for item in result:
            assert item.previous_claimed is None
            assert item.current_claim is None
            assert item.total_claimed is None

    def test_construct_payment_certificate_with_current_transactions_only(self):
        """Test construct_payment_certificate with only current certificate transactions."""
        project = ProjectFactory.create()
        line_item1 = LineItemFactory.create(
            project=project, unit_price=Decimal("100.00")
        )
        line_item2 = LineItemFactory.create(
            project=project, unit_price=Decimal("200.00")
        )

        certificate = PaymentCertificateFactory.create(
            project=project, certificate_number=1
        )

        # Add transactions to current certificate
        ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item1,
            quantity=Decimal("10.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("1000.00"),
        )
        ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item2,
            quantity=Decimal("5.00"),
            unit_price=Decimal("200.00"),
            total_price=Decimal("1000.00"),
        )

        result = LineItem.construct_payment_certificate(certificate)

        line_item1_result = result.get(id=line_item1.id)
        line_item2_result = result.get(id=line_item2.id)

        # No previous certificates
        assert line_item1_result.previous_claimed is None
        assert line_item2_result.previous_claimed is None

        # Current claims should match
        assert line_item1_result.current_claim == Decimal("1000.00")
        assert line_item2_result.current_claim == Decimal("1000.00")

        # Total claimed should equal current (no previous)
        assert line_item1_result.total_claimed == Decimal("1000.00")
        assert line_item2_result.total_claimed == Decimal("1000.00")

    def test_construct_payment_certificate_with_previous_certificates(self):
        """Test construct_payment_certificate with previous approved certificates."""
        project = ProjectFactory.create()
        line_item = LineItemFactory.create(
            project=project, unit_price=Decimal("100.00")
        )

        # Certificate 1 (previous, approved)
        cert1 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=1,
            status=PaymentCertificate.Status.APPROVED,
        )
        ActualTransactionFactory.create(
            payment_certificate=cert1,
            line_item=line_item,
            total_price=Decimal("500.00"),
        )

        # Certificate 2 (previous, approved)
        cert2 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=2,
            status=PaymentCertificate.Status.APPROVED,
        )
        ActualTransactionFactory.create(
            payment_certificate=cert2,
            line_item=line_item,
            total_price=Decimal("300.00"),
        )

        # Certificate 3 (current)
        cert3 = PaymentCertificateFactory.create(project=project, certificate_number=3)
        ActualTransactionFactory.create(
            payment_certificate=cert3,
            line_item=line_item,
            total_price=Decimal("200.00"),
        )

        result = LineItem.construct_payment_certificate(cert3)
        line_item_result = result.get(id=line_item.id)

        # Previous claimed should be sum of cert1 and cert2
        assert line_item_result.previous_claimed == Decimal("800.00")

        # Current claim should be cert3 only
        assert line_item_result.current_claim == Decimal("200.00")

        # Total claimed should be all three
        assert line_item_result.total_claimed == Decimal("1000.00")

    def test_construct_payment_certificate_excludes_future_certificates(self):
        """Test that future certificates are not included in calculations."""
        project = ProjectFactory.create()
        line_item = LineItemFactory.create(project=project)

        # Certificate 1 (previous)
        cert1 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=1,
            status=PaymentCertificate.Status.APPROVED,
        )
        ActualTransactionFactory.create(
            payment_certificate=cert1,
            line_item=line_item,
            total_price=Decimal("500.00"),
        )

        # Certificate 2 (current)
        cert2 = PaymentCertificateFactory.create(project=project, certificate_number=2)
        ActualTransactionFactory.create(
            payment_certificate=cert2,
            line_item=line_item,
            total_price=Decimal("300.00"),
        )

        # Certificate 3 (future - should be excluded)
        cert3 = PaymentCertificateFactory.create(project=project, certificate_number=3)
        ActualTransactionFactory.create(
            payment_certificate=cert3,
            line_item=line_item,
            total_price=Decimal("200.00"),
        )

        result = LineItem.construct_payment_certificate(cert2)
        line_item_result = result.get(id=line_item.id)

        # Previous should only include cert1
        assert line_item_result.previous_claimed == Decimal("500.00")

        # Current should only be cert2
        assert line_item_result.current_claim == Decimal("300.00")

        # Total should not include cert3
        assert line_item_result.total_claimed == Decimal("800.00")

    def test_construct_payment_certificate_multiple_line_items(self):
        """Test construct_payment_certificate with multiple line items."""
        project = ProjectFactory.create()
        line_item1 = LineItemFactory.create(project=project)
        line_item2 = LineItemFactory.create(project=project)
        line_item3 = LineItemFactory.create(project=project)

        # Previous certificate
        cert1 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=1,
            status=PaymentCertificate.Status.APPROVED,
        )
        ActualTransactionFactory.create(
            payment_certificate=cert1,
            line_item=line_item1,
            total_price=Decimal("100.00"),
        )
        ActualTransactionFactory.create(
            payment_certificate=cert1,
            line_item=line_item2,
            total_price=Decimal("200.00"),
        )

        # Current certificate
        cert2 = PaymentCertificateFactory.create(project=project, certificate_number=2)
        ActualTransactionFactory.create(
            payment_certificate=cert2,
            line_item=line_item1,
            total_price=Decimal("50.00"),
        )
        ActualTransactionFactory.create(
            payment_certificate=cert2,
            line_item=line_item3,
            total_price=Decimal("150.00"),
        )

        result = LineItem.construct_payment_certificate(cert2)

        item1 = result.get(id=line_item1.id)
        item2 = result.get(id=line_item2.id)
        item3 = result.get(id=line_item3.id)

        # Line item 1: has previous and current
        assert item1.previous_claimed == Decimal("100.00")
        assert item1.current_claim == Decimal("50.00")
        assert item1.total_claimed == Decimal("150.00")

        # Line item 2: has previous only
        assert item2.previous_claimed == Decimal("200.00")
        assert item2.current_claim is None
        assert item2.total_claimed == Decimal("200.00")

        # Line item 3: has current only
        assert item3.previous_claimed is None
        assert item3.current_claim == Decimal("150.00")
        assert item3.total_claimed == Decimal("150.00")

    def test_construct_payment_certificate_multiple_transactions_per_line_item(self):
        """Test construct_payment_certificate with multiple transactions for same line item."""
        project = ProjectFactory.create()
        line_item = LineItemFactory.create(project=project)

        certificate = PaymentCertificateFactory.create(
            project=project, certificate_number=1
        )

        # Multiple transactions for same line item in same certificate
        ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            total_price=Decimal("100.00"),
        )
        ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            total_price=Decimal("150.00"),
        )
        ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            total_price=Decimal("250.00"),
        )

        result = LineItem.construct_payment_certificate(certificate)
        line_item_result = result.get(id=line_item.id)

        # Should sum all transactions
        assert line_item_result.current_claim == Decimal("500.00")
        assert line_item_result.total_claimed == Decimal("500.00")

    def test_construct_payment_certificate_returns_queryset(self):
        """Test that construct_payment_certificate returns a queryset."""
        project = ProjectFactory.create()
        LineItemFactory.create(project=project)
        certificate = PaymentCertificateFactory.create(project=project)

        result = LineItem.construct_payment_certificate(certificate)

        # Should be a queryset
        assert hasattr(result, "filter")
        assert hasattr(result, "count")
        assert hasattr(result, "order_by")
