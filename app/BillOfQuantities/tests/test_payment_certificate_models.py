"""Tests for PaymentCertificate and ActualTransaction models."""

from decimal import Decimal

import pytest

from app.BillOfQuantities.models import ActualTransaction, PaymentCertificate
from app.BillOfQuantities.tests.factories import (
    ActualTransactionFactory,
    LineItemFactory,
    PaymentCertificateFactory,
)
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestPaymentCertificateModel:
    """Test cases for PaymentCertificate model."""

    def test_payment_certificate_creation(self):
        """Test creating a payment certificate with valid data."""
        certificate = PaymentCertificateFactory.create()
        assert certificate.id is not None
        assert certificate.project is not None
        assert certificate.status == PaymentCertificate.Status.DRAFT

    def test_payment_certificate_string_representation(self):
        """Test the __str__ method returns correct format."""
        project = ProjectFactory(name="Test Project")
        certificate = PaymentCertificateFactory(
            project=project,
            certificate_number=5,
            status=PaymentCertificate.Status.DRAFT,
        )
        expected = f"# 5: {project} - DRAFT"
        assert str(certificate) == expected

    def test_payment_certificate_status_choices(self):
        """Test all status choices are valid."""
        statuses = [
            PaymentCertificate.Status.DRAFT,
            PaymentCertificate.Status.SUBMITTED,
            PaymentCertificate.Status.APPROVED,
            PaymentCertificate.Status.REJECTED,
        ]
        for status in statuses:
            certificate = PaymentCertificateFactory.create(status=status)
            assert certificate.status == status

    def test_get_next_certificate_number_first_certificate(self):
        """Test getting next certificate number for first certificate."""
        project = ProjectFactory.create()
        next_number = PaymentCertificate.get_next_certificate_number(project)
        assert next_number == 1

    def test_get_next_certificate_number_with_existing(self):
        """Test getting next certificate number with existing certificates."""
        project = ProjectFactory.create()
        PaymentCertificateFactory.create(project=project, certificate_number=1)
        PaymentCertificateFactory.create(project=project, certificate_number=2)
        PaymentCertificateFactory.create(project=project, certificate_number=3)

        next_number = PaymentCertificate.get_next_certificate_number(project)
        assert next_number == 4

    def test_payment_certificate_ordering(self):
        """Test payment certificates are ordered by created_at descending."""
        project = ProjectFactory.create()
        cert1 = PaymentCertificateFactory.create(project=project, certificate_number=1)
        cert2 = PaymentCertificateFactory.create(project=project, certificate_number=2)
        cert3 = PaymentCertificateFactory.create(project=project, certificate_number=3)

        certificates = PaymentCertificate.objects.filter(project=project)
        # Most recent first
        cert_list = list(certificates)
        assert cert_list[0] == cert1
        assert cert_list[1] == cert2
        assert cert_list[2] == cert3

    def test_payment_certificate_project_relationship(self):
        """Test the relationship between PaymentCertificate and Project."""
        project = ProjectFactory.create()
        cert1 = PaymentCertificateFactory.create(project=project)
        cert2 = PaymentCertificateFactory.create(project=project)

        assert project.payment_certificates.count() == 2
        assert cert1 in project.payment_certificates.all()
        assert cert2 in project.payment_certificates.all()

    def test_payment_certificate_timestamps(self):
        """Test created_at and updated_at are set correctly."""
        certificate = PaymentCertificateFactory.create()
        assert certificate.created_at is not None
        assert certificate.updated_at is not None
        assert certificate.created_at <= certificate.updated_at


@pytest.mark.django_db
class TestActualTransactionModel:
    """Test cases for ActualTransaction model."""

    def test_actual_transaction_creation(self):
        """Test creating an actual transaction with valid data."""
        transaction = ActualTransactionFactory.create()
        assert transaction.id is not None
        assert transaction.payment_certificate is not None
        assert transaction.line_item is not None
        assert transaction.quantity > 0

    def test_actual_transaction_total_price_calculation(self):
        """Test total price is calculated correctly."""
        transaction = ActualTransactionFactory.create(
            quantity=Decimal("10.00"), unit_price=Decimal("25.50")
        )
        expected_total = Decimal("10.00") * Decimal("25.50")
        assert transaction.total_price == expected_total

    def test_actual_transaction_approved_default(self):
        """Test approved defaults to False."""
        transaction = ActualTransactionFactory.create()
        assert transaction.approved is False

    def test_actual_transaction_claimed_default(self):
        """Test claimed defaults to False."""
        transaction = ActualTransactionFactory.create()
        assert transaction.claimed is False

    def test_actual_transaction_ordering(self):
        """Test transactions are ordered by line_item row_index."""
        certificate = PaymentCertificateFactory.create()
        line_item1 = LineItemFactory.create(row_index=3)
        line_item2 = LineItemFactory.create(row_index=1)
        line_item3 = LineItemFactory.create(row_index=2)

        trans1 = ActualTransactionFactory.create(
            payment_certificate=certificate, line_item=line_item1
        )
        trans2 = ActualTransactionFactory.create(
            payment_certificate=certificate, line_item=line_item2
        )
        trans3 = ActualTransactionFactory.create(
            payment_certificate=certificate, line_item=line_item3
        )

        transactions = ActualTransaction.objects.filter(payment_certificate=certificate)
        assert list(transactions) == [trans2, trans3, trans1]

    def test_actual_transaction_payment_certificate_relationship(self):
        """Test relationship between ActualTransaction and PaymentCertificate."""
        certificate = PaymentCertificateFactory.create()
        trans1 = ActualTransactionFactory.create(payment_certificate=certificate)
        trans2 = ActualTransactionFactory.create(payment_certificate=certificate)

        assert certificate.actual_transactions.count() == 2
        assert trans1 in certificate.actual_transactions.all()
        assert trans2 in certificate.actual_transactions.all()

    def test_actual_transaction_line_item_relationship(self):
        """Test relationship between ActualTransaction and LineItem."""
        line_item = LineItemFactory.create()
        trans1 = ActualTransactionFactory.create(line_item=line_item)
        trans2 = ActualTransactionFactory.create(line_item=line_item)

        assert line_item.actual_transactions.count() == 2
        assert trans1 in line_item.actual_transactions.all()
        assert trans2 in line_item.actual_transactions.all()

    def test_actual_transaction_soft_delete(self):
        """Test soft delete functionality."""
        transaction = ActualTransactionFactory.create()

        transaction.soft_delete()

        assert ActualTransaction.objects.all().count() == 0
        assert transaction.is_deleted


@pytest.mark.django_db
class TestLineItemProperties:
    """Test cases for LineItem properties."""

    def test_claimed_to_date_with_no_transactions(self):
        """Test claimed_to_date returns 0 when no transactions."""
        line_item = LineItemFactory.create()
        assert line_item.claimed_to_date == Decimal(0)

    def test_claimed_to_date_with_claimed_transactions(self):
        """Test claimed_to_date sums only claimed transactions."""
        line_item = LineItemFactory.create(budgeted_quantity=Decimal("100.00"))
        certificate = PaymentCertificateFactory.create(project=line_item.project)

        # Create claimed transactions
        ActualTransactionFactory.create(
            line_item=line_item,
            payment_certificate=certificate,
            quantity=Decimal("15.00"),
            claimed=True,
        )
        ActualTransactionFactory.create(
            line_item=line_item,
            payment_certificate=certificate,
            quantity=Decimal("5.00"),
            claimed=True,
        )

        # Create unclaimed transaction (should not be counted)
        ActualTransactionFactory.create(
            line_item=line_item,
            payment_certificate=certificate,
            quantity=Decimal("20.00"),
            claimed=False,
        )

        assert line_item.claimed_to_date == Decimal("0")
        certificate.status = PaymentCertificate.Status.APPROVED
        certificate.save()

        assert line_item.claimed_to_date == Decimal("20.00")

    def test_remaining_quantity_calculation(self):
        """Test remaining_quantity is calculated correctly."""
        line_item = LineItemFactory.create(budgeted_quantity=Decimal("100.00"))
        certificate = PaymentCertificateFactory.create(
            project=line_item.project, status=PaymentCertificate.Status.APPROVED
        )

        ActualTransactionFactory.create(
            line_item=line_item,
            payment_certificate=certificate,
            quantity=Decimal("30.00"),
            claimed=True,
        )

        assert line_item.remaining_quantity == Decimal("70.00")

    def test_current_transaction_with_active_certificate(self):
        """Test current_transaction returns transaction for active certificate."""
        project = ProjectFactory.create()
        line_item = LineItemFactory.create(project=project)
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )
        transaction = ActualTransactionFactory.create(
            line_item=line_item, payment_certificate=certificate
        )

        assert line_item.current_transaction == transaction

    def test_current_transaction_with_no_active_certificate(self):
        """Test current_transaction returns None when no active certificate."""
        line_item = LineItemFactory.create()
        assert line_item.current_transaction is None


@pytest.mark.django_db
class TestPaymentCertificateProperties:
    """Test cases for PaymentCertificate properties."""

    def test_items_submitted_with_approved_transactions(self):
        """Test items_submitted calculates total for approved transactions."""
        certificate = PaymentCertificateFactory.create()
        line_item = LineItemFactory.create(unit_price=Decimal("100.00"))

        ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            quantity=Decimal("5.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("500.00"),
            approved=True,
        )
        ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            quantity=Decimal("3.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("300.00"),
            approved=True,
        )

        assert certificate.items_submitted == Decimal("800.00")

    def test_items_claimed_with_approved_transactions(self):
        """Test items_claimed calculates total for approved transactions."""
        certificate = PaymentCertificateFactory.create()
        line_item = LineItemFactory.create(unit_price=Decimal("50.00"))

        ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            quantity=Decimal("10.00"),
            unit_price=Decimal("50.00"),
            total_price=Decimal("500.00"),
            claimed=True,
        )

        assert certificate.items_claimed == Decimal("500.00")

    def test_progressive_previous_first_certificate(self):
        """Test progressive_previous returns 0 for first certificate."""
        project = ProjectFactory.create()
        cert1 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=1,
            status=PaymentCertificate.Status.DRAFT,
        )

        assert cert1.progressive_previous == Decimal("0")

    def test_progressive_previous_with_approved_certificates(self):
        """Test progressive_previous calculates total from previous approved certificates."""
        project = ProjectFactory.create()
        line_item = LineItemFactory.create(
            project=project, unit_price=Decimal("100.00")
        )

        # Certificate 1 - Approved
        cert1 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=1,
            status=PaymentCertificate.Status.APPROVED,
        )
        ActualTransactionFactory.create(
            payment_certificate=cert1,
            line_item=line_item,
            quantity=Decimal("5.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("500.00"),
            approved=True,
        )

        # Certificate 2 - Approved
        cert2 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=2,
            status=PaymentCertificate.Status.APPROVED,
        )
        ActualTransactionFactory.create(
            payment_certificate=cert2,
            line_item=line_item,
            quantity=Decimal("3.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("300.00"),
            approved=True,
        )

        # Certificate 3 - Draft (current)
        cert3 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=3,
            status=PaymentCertificate.Status.DRAFT,
        )

        # Progressive previous should be cert1 + cert2 = 500 + 300 = 800
        assert cert3.progressive_previous == Decimal("800.00")

    def test_progressive_previous_ignores_non_approved(self):
        """Test progressive_previous only includes approved certificates."""
        project = ProjectFactory.create()
        line_item = LineItemFactory.create(
            project=project, unit_price=Decimal("100.00")
        )

        # Certificate 1 - Approved
        cert1 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=1,
            status=PaymentCertificate.Status.APPROVED,
        )
        ActualTransactionFactory.create(
            payment_certificate=cert1,
            line_item=line_item,
            quantity=Decimal("5.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("500.00"),
            approved=True,
        )

        # Certificate 2 - Rejected (should be ignored)
        cert2 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=2,
            status=PaymentCertificate.Status.REJECTED,
        )
        ActualTransactionFactory.create(
            payment_certificate=cert2,
            line_item=line_item,
            quantity=Decimal("3.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("300.00"),
            approved=False,
        )

        # Certificate 3 - Draft (current)
        cert3 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=3,
            status=PaymentCertificate.Status.DRAFT,
        )

        # Progressive previous should only include cert1 = 500
        assert cert3.progressive_previous == Decimal("500.00")

    def test_progressive_to_date(self):
        """Test progressive_to_date includes current certificate."""
        project = ProjectFactory.create()
        line_item = LineItemFactory.create(
            project=project, unit_price=Decimal("100.00")
        )

        # Certificate 1 - Approved
        cert1 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=1,
            status=PaymentCertificate.Status.APPROVED,
        )
        ActualTransactionFactory.create(
            payment_certificate=cert1,
            line_item=line_item,
            quantity=Decimal("5.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("500.00"),
            approved=True,
        )

        # Certificate 2 - Draft (current)
        cert2 = PaymentCertificateFactory.create(
            project=project,
            certificate_number=2,
            status=PaymentCertificate.Status.DRAFT,
        )
        ActualTransactionFactory.create(
            payment_certificate=cert2,
            line_item=line_item,
            quantity=Decimal("3.00"),
            unit_price=Decimal("100.00"),
            total_price=Decimal("300.00"),
            approved=False,
        )

        # Progressive to date = previous (500) + current (300) = 800
        assert cert2.progressive_to_date == Decimal("800.00")
