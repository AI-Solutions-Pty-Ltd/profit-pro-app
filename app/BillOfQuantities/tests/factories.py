"""Factories for BillOfQuantities models."""

from datetime import date, timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from factory import LazyAttribute, LazyFunction, Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.models import (
    ActualTransaction,
    AdvancePayment,
    BaselineCashflow,
    Bill,
    CashflowForecast,
    Claim,
    ContractualCorrespondence,
    ContractVariation,
    CorrespondenceDialog,
    CorrespondenceDialogFile,
    Escalation,
    Forecast,
    ForecastTransaction,
    LineItem,
    MaterialsOnSite,
    Package,
    PaymentCertificate,
    Retention,
    RevisedBaseline,
    RevisedBaselineDetail,
    ScheduleForecast,
    ScheduleForecastSection,
    SectionalCompletionDate,
    SpecialItemTransaction,
    Structure,
)
from app.Project.tests.factories import ProjectFactory

fake = Faker()


class StructureFactory(DjangoModelFactory):
    """Factory for Structure model."""

    class Meta:
        model = Structure

    project = SubFactory(ProjectFactory)
    name = Sequence(lambda n: f"Structure {n}")
    description = fake.sentence()


class BillFactory(DjangoModelFactory):
    """Factory for Bill model."""

    class Meta:
        model = Bill

    structure = SubFactory(StructureFactory)
    name = Sequence(lambda n: f"Bill {n}")


class PackageFactory(DjangoModelFactory):
    """Factory for Package model."""

    class Meta:
        model = Package

    bill = SubFactory(BillFactory)
    name = Sequence(lambda n: f"Package {n}")


class LineItemFactory(DjangoModelFactory):
    """Factory for LineItem model."""

    class Meta:
        model = LineItem

    project = SubFactory(ProjectFactory)
    structure = SubFactory(StructureFactory)
    bill = SubFactory(BillFactory)
    package = SubFactory(PackageFactory)
    row_index = Sequence(lambda n: n)
    item_number = Sequence(lambda n: f"ITEM-{n:03d}")
    payment_reference = Sequence(lambda n: f"PAY-{n:03d}")
    description = fake.sentence()
    is_work = True
    unit_measurement = "m"
    unit_price = fake.pydecimal(left_digits=4, right_digits=2, positive=True)
    budgeted_quantity = fake.pydecimal(left_digits=3, right_digits=2, positive=True)
    total_price = LazyAttribute(lambda obj: obj.unit_price * obj.budgeted_quantity)
    addendum = False
    special_item = False


class PaymentCertificateFactory(DjangoModelFactory):
    """Factory for PaymentCertificate model."""

    class Meta:
        model = PaymentCertificate

    project = SubFactory(ProjectFactory)
    status = PaymentCertificate.Status.DRAFT
    # certificate_number = Sequence(lambda n: n + 1)


class ActualTransactionFactory(DjangoModelFactory):
    """Factory for ActualTransaction model."""

    class Meta:
        model = ActualTransaction

    payment_certificate = SubFactory(PaymentCertificateFactory)
    line_item = SubFactory(LineItemFactory)
    captured_by = SubFactory(AccountFactory)
    approved_by = SubFactory(AccountFactory)
    quantity = fake.pydecimal(left_digits=3, right_digits=2, positive=True)
    unit_price = LazyAttribute(lambda obj: obj.line_item.unit_price)
    total_price = LazyAttribute(lambda obj: obj.quantity * obj.unit_price)
    approved = False
    claimed = False


# ============================================================================
# Forecast Factories
# ============================================================================


class ForecastFactory(DjangoModelFactory):
    """Factory for Forecast model."""

    class Meta:
        model = Forecast

    project = SubFactory(ProjectFactory)
    period = LazyFunction(lambda: date.today().replace(day=1))
    status = Forecast.Status.DRAFT
    notes = fake.sentence()
    captured_by = SubFactory(AccountFactory)


class ForecastTransactionFactory(DjangoModelFactory):
    """Factory for ForecastTransaction model."""

    class Meta:
        model = ForecastTransaction

    forecast = SubFactory(ForecastFactory)
    line_item = SubFactory(LineItemFactory)
    quantity = fake.pydecimal(left_digits=3, right_digits=2, positive=True)
    unit_price = LazyAttribute(lambda obj: obj.line_item.unit_price)
    total_price = LazyAttribute(lambda obj: obj.quantity * obj.unit_price)
    notes = ""


# ============================================================================
# Contract Management Factories
# ============================================================================


class ContractVariationFactory(DjangoModelFactory):
    """Factory for ContractVariation model."""

    class Meta:
        model = ContractVariation

    project = SubFactory(ProjectFactory)
    variation_number = Sequence(lambda n: f"VAR-{n:03d}")
    title = fake.sentence(nb_words=5)
    description = fake.paragraph()
    category = ContractVariation.Category.SCOPE_CHANGE
    variation_type = ContractVariation.VariationType.AMOUNT
    status = ContractVariation.Status.DRAFT
    variation_amount = fake.pydecimal(left_digits=6, right_digits=2, positive=True)
    date_identified = LazyFunction(date.today)
    submitted_by = SubFactory(AccountFactory)


class ContractualCorrespondenceFactory(DjangoModelFactory):
    """Factory for ContractualCorrespondence model."""

    class Meta:
        model = ContractualCorrespondence

    project = SubFactory(ProjectFactory)
    reference_number = Sequence(lambda n: f"CORR-{n:04d}")
    subject = fake.sentence(nb_words=8)
    correspondence_type = ContractualCorrespondence.CorrespondenceType.LETTER
    direction = ContractualCorrespondence.Direction.OUTGOING
    date_of_correspondence = LazyFunction(date.today)
    sender = fake.company()
    recipient = fake.company()
    summary = fake.paragraph()
    logged_by = SubFactory(AccountFactory)
    sender_user = None
    recipient_user = None


class CorrespondenceDialogFactory(DjangoModelFactory):
    """Factory for CorrespondenceDialog model."""

    class Meta:
        model = CorrespondenceDialog

    correspondence = SubFactory(ContractualCorrespondenceFactory)
    sender_user = SubFactory(AccountFactory)
    receiver_user = SubFactory(AccountFactory)
    message = fake.paragraph(nb_sentences=3)
    sender = ""
    receiver = ""


class CorrespondenceDialogFileFactory(DjangoModelFactory):
    """Factory for CorrespondenceDialogFile model."""

    class Meta:
        model = CorrespondenceDialogFile

    dialog = SubFactory(CorrespondenceDialogFactory)
    file = LazyAttribute(
        lambda _: SimpleUploadedFile(
            f"test_file_{fake.uuid4()[:8]}.pdf",
            b"fake file content",
            content_type="application/pdf",
        )
    )


# ============================================================================
# Ledger Factories
# ============================================================================


class AdvancePaymentFactory(DjangoModelFactory):
    """Factory for AdvancePayment model."""

    class Meta:
        model = AdvancePayment

    project = SubFactory(ProjectFactory)
    payment_certificate = SubFactory(PaymentCertificateFactory)
    transaction_type = AdvancePayment.TransactionType.DEBIT
    amount = fake.pydecimal(left_digits=6, right_digits=2, positive=True)
    description = fake.sentence()
    date = LazyFunction(date.today)
    captured_by = SubFactory(AccountFactory)
    recovery_method = AdvancePayment.RecoveryMethod.PERCENTAGE
    recovery_percentage = Decimal("10.00")


class RetentionFactory(DjangoModelFactory):
    """Factory for Retention model."""

    class Meta:
        model = Retention

    project = SubFactory(ProjectFactory)
    payment_certificate = SubFactory(PaymentCertificateFactory)
    transaction_type = Retention.TransactionType.DEBIT
    amount = fake.pydecimal(left_digits=5, right_digits=2, positive=True)
    description = fake.sentence()
    date = LazyFunction(date.today)
    captured_by = SubFactory(AccountFactory)
    retention_type = Retention.RetentionType.WITHHELD
    retention_percentage = Decimal("10.00")


class MaterialsOnSiteFactory(DjangoModelFactory):
    """Factory for MaterialsOnSite model."""

    class Meta:
        model = MaterialsOnSite

    project = SubFactory(ProjectFactory)
    payment_certificate = SubFactory(PaymentCertificateFactory)
    transaction_type = MaterialsOnSite.TransactionType.DEBIT
    amount = fake.pydecimal(left_digits=5, right_digits=2, positive=True)
    description = fake.sentence()
    date = LazyFunction(date.today)
    captured_by = SubFactory(AccountFactory)
    material_status = MaterialsOnSite.MaterialStatus.CLAIMED
    material_description = fake.sentence(nb_words=4)
    quantity = fake.pydecimal(left_digits=3, right_digits=2, positive=True)
    unit = "m3"


class EscalationFactory(DjangoModelFactory):
    """Factory for Escalation model."""

    class Meta:
        model = Escalation

    project = SubFactory(ProjectFactory)
    payment_certificate = SubFactory(PaymentCertificateFactory)
    transaction_type = Escalation.TransactionType.DEBIT
    amount = fake.pydecimal(left_digits=5, right_digits=2, positive=True)
    description = fake.sentence()
    date = LazyFunction(date.today)
    captured_by = SubFactory(AccountFactory)
    escalation_type = Escalation.EscalationType.COMBINED


class SpecialItemTransactionFactory(DjangoModelFactory):
    """Factory for SpecialItemTransaction model."""

    class Meta:
        model = SpecialItemTransaction

    project = SubFactory(ProjectFactory)
    payment_certificate = SubFactory(PaymentCertificateFactory)
    transaction_type = SpecialItemTransaction.TransactionType.DEBIT
    amount = fake.pydecimal(left_digits=5, right_digits=2, positive=True)
    description = fake.sentence()
    date = LazyFunction(date.today)
    captured_by = SubFactory(AccountFactory)
    special_item_type = SpecialItemTransaction.SpecialItemType.PROVISIONAL
    item_reference = Sequence(lambda n: f"SI-{n:03d}")


# ============================================================================
# Cashflow Factories
# ============================================================================


class BaselineCashflowFactory(DjangoModelFactory):
    """Factory for BaselineCashflow model."""

    class Meta:
        model = BaselineCashflow

    project = SubFactory(ProjectFactory)
    version = 1
    period = LazyFunction(lambda: date.today().replace(day=1))
    planned_value = fake.pydecimal(left_digits=6, right_digits=2, positive=True)
    status = BaselineCashflow.Status.DRAFT


class RevisedBaselineFactory(DjangoModelFactory):
    """Factory for RevisedBaseline model."""

    class Meta:
        model = RevisedBaseline

    project = SubFactory(ProjectFactory)
    revision_number = Sequence(lambda n: n + 1)
    revision_date = LazyFunction(date.today)
    revision_reason = RevisedBaseline.RevisionReason.VARIATION
    reason_description = fake.paragraph()
    status = RevisedBaseline.Status.DRAFT
    original_completion_date = LazyFunction(lambda: date.today() + timedelta(days=180))
    revised_completion_date = LazyFunction(lambda: date.today() + timedelta(days=210))


class RevisedBaselineDetailFactory(DjangoModelFactory):
    """Factory for RevisedBaselineDetail model."""

    class Meta:
        model = RevisedBaselineDetail

    revised_baseline = SubFactory(RevisedBaselineFactory)
    period = LazyFunction(lambda: date.today().replace(day=1))
    planned_value = fake.pydecimal(left_digits=6, right_digits=2, positive=True)


class CashflowForecastFactory(DjangoModelFactory):
    """Factory for CashflowForecast model."""

    class Meta:
        model = CashflowForecast

    project = SubFactory(ProjectFactory)
    forecast_date = LazyFunction(date.today)
    forecast_period = LazyFunction(lambda: date.today().replace(day=1))
    forecast_value = fake.pydecimal(left_digits=6, right_digits=2, positive=True)
    status = CashflowForecast.Status.DRAFT
    captured_by = SubFactory(AccountFactory)


# ============================================================================
# Schedule Factories
# ============================================================================


class SectionalCompletionDateFactory(DjangoModelFactory):
    """Factory for SectionalCompletionDate model."""

    class Meta:
        model = SectionalCompletionDate

    project = SubFactory(ProjectFactory)
    section_name = Sequence(lambda n: f"Section {n}")
    section_description = fake.sentence()
    planned_start_date = LazyFunction(date.today)
    planned_completion_date = LazyFunction(lambda: date.today() + timedelta(days=90))
    status = SectionalCompletionDate.Status.NOT_STARTED


class ScheduleForecastFactory(DjangoModelFactory):
    """Factory for ScheduleForecast model."""

    class Meta:
        model = ScheduleForecast

    project = SubFactory(ProjectFactory)
    forecast_date = LazyFunction(date.today)
    reporting_period = LazyFunction(lambda: date.today().replace(day=1))
    planned_project_completion = LazyFunction(
        lambda: date.today() + timedelta(days=180)
    )
    forecast_project_completion = LazyFunction(
        lambda: date.today() + timedelta(days=200)
    )
    status = ScheduleForecast.Status.DRAFT
    captured_by = SubFactory(AccountFactory)


class ScheduleForecastSectionFactory(DjangoModelFactory):
    """Factory for ScheduleForecastSection model."""

    class Meta:
        model = ScheduleForecastSection

    schedule_forecast = SubFactory(ScheduleForecastFactory)
    sectional_completion = SubFactory(SectionalCompletionDateFactory)
    forecast_completion_date = LazyFunction(lambda: date.today() + timedelta(days=90))


class ClaimFactory(DjangoModelFactory):
    """Factory for Claim model."""

    class Meta:
        model = Claim

    project = SubFactory(ProjectFactory)
    period = LazyFunction(lambda: date.today().replace(day=1, year=2024, month=1))
    estimated_claim = LazyFunction(lambda: Decimal("100000.00"))
    notes = fake.text(max_nb_chars=200)
