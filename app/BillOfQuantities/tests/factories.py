"""Factories for BillOfQuantities models."""

from datetime import date, timedelta
from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.models import (
    ActualTransaction,
    AdvancePayment,
    BaselineCashflow,
    Bill,
    CashflowForecast,
    ContractualCorrespondence,
    ContractVariation,
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


class StructureFactory(DjangoModelFactory):
    """Factory for Structure model."""

    class Meta:
        model = Structure

    project = factory.SubFactory(ProjectFactory)
    name = factory.Sequence(lambda n: f"Structure {n}")
    description = factory.Faker("sentence")


class BillFactory(DjangoModelFactory):
    """Factory for Bill model."""

    class Meta:
        model = Bill

    structure = factory.SubFactory(StructureFactory)
    name = factory.Sequence(lambda n: f"Bill {n}")


class PackageFactory(DjangoModelFactory):
    """Factory for Package model."""

    class Meta:
        model = Package

    bill = factory.SubFactory(BillFactory)
    name = factory.Sequence(lambda n: f"Package {n}")


class LineItemFactory(DjangoModelFactory):
    """Factory for LineItem model."""

    class Meta:
        model = LineItem

    project = factory.SubFactory(ProjectFactory)
    structure = factory.SubFactory(StructureFactory)
    bill = factory.SubFactory(BillFactory)
    package = factory.SubFactory(PackageFactory)
    row_index = factory.Sequence(lambda n: n)
    item_number = factory.Sequence(lambda n: f"ITEM-{n:03d}")
    payment_reference = factory.Sequence(lambda n: f"PAY-{n:03d}")
    description = factory.Faker("sentence")
    is_work = True
    unit_measurement = "m"
    unit_price = factory.Faker(
        "pydecimal", left_digits=4, right_digits=2, positive=True
    )
    budgeted_quantity = factory.Faker(
        "pydecimal", left_digits=3, right_digits=2, positive=True
    )
    total_price = factory.LazyAttribute(
        lambda obj: obj.unit_price * obj.budgeted_quantity
    )


class PaymentCertificateFactory(DjangoModelFactory):
    """Factory for PaymentCertificate model."""

    class Meta:
        model = PaymentCertificate

    project = factory.SubFactory(ProjectFactory)
    status = PaymentCertificate.Status.DRAFT


class ActualTransactionFactory(DjangoModelFactory):
    """Factory for ActualTransaction model."""

    class Meta:
        model = ActualTransaction

    payment_certificate = factory.SubFactory(PaymentCertificateFactory)
    line_item = factory.SubFactory(LineItemFactory)
    captured_by = factory.SubFactory(AccountFactory)
    approved_by = factory.SubFactory(AccountFactory)
    quantity = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    unit_price = factory.LazyAttribute(lambda obj: obj.line_item.unit_price)
    total_price = factory.LazyAttribute(lambda obj: obj.quantity * obj.unit_price)
    approved = False
    claimed = False


# ============================================================================
# Forecast Factories
# ============================================================================


class ForecastFactory(DjangoModelFactory):
    """Factory for Forecast model."""

    class Meta:
        model = Forecast

    project = factory.SubFactory(ProjectFactory)
    period = factory.LazyFunction(lambda: date.today().replace(day=1))
    status = Forecast.Status.DRAFT
    notes = factory.Faker("sentence")
    captured_by = factory.SubFactory(AccountFactory)


class ForecastTransactionFactory(DjangoModelFactory):
    """Factory for ForecastTransaction model."""

    class Meta:
        model = ForecastTransaction

    forecast = factory.SubFactory(ForecastFactory)
    line_item = factory.SubFactory(LineItemFactory)
    quantity = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    unit_price = factory.LazyAttribute(lambda obj: obj.line_item.unit_price)
    total_price = factory.LazyAttribute(lambda obj: obj.quantity * obj.unit_price)
    notes = ""


# ============================================================================
# Contract Management Factories
# ============================================================================


class ContractVariationFactory(DjangoModelFactory):
    """Factory for ContractVariation model."""

    class Meta:
        model = ContractVariation

    project = factory.SubFactory(ProjectFactory)
    variation_number = factory.Sequence(lambda n: f"VAR-{n:03d}")
    title = factory.Faker("sentence", nb_words=5)
    description = factory.Faker("paragraph")
    category = ContractVariation.Category.SCOPE_CHANGE
    variation_type = ContractVariation.VariationType.AMOUNT
    status = ContractVariation.Status.DRAFT
    variation_amount = factory.Faker(
        "pydecimal", left_digits=6, right_digits=2, positive=True
    )
    date_identified = factory.LazyFunction(date.today)
    submitted_by = factory.SubFactory(AccountFactory)


class ContractualCorrespondenceFactory(DjangoModelFactory):
    """Factory for ContractualCorrespondence model."""

    class Meta:
        model = ContractualCorrespondence

    project = factory.SubFactory(ProjectFactory)
    reference_number = factory.Sequence(lambda n: f"CORR-{n:04d}")
    subject = factory.Faker("sentence", nb_words=8)
    correspondence_type = ContractualCorrespondence.CorrespondenceType.LETTER
    direction = ContractualCorrespondence.Direction.OUTGOING
    date_of_correspondence = factory.LazyFunction(date.today)
    sender = factory.Faker("company")
    recipient = factory.Faker("company")
    summary = factory.Faker("paragraph")
    logged_by = factory.SubFactory(AccountFactory)


# ============================================================================
# Ledger Factories
# ============================================================================


class AdvancePaymentFactory(DjangoModelFactory):
    """Factory for AdvancePayment model."""

    class Meta:
        model = AdvancePayment

    project = factory.SubFactory(ProjectFactory)
    payment_certificate = factory.SubFactory(PaymentCertificateFactory)
    transaction_type = AdvancePayment.TransactionType.DEBIT
    amount = factory.Faker("pydecimal", left_digits=6, right_digits=2, positive=True)
    description = factory.Faker("sentence")
    date = factory.LazyFunction(date.today)
    captured_by = factory.SubFactory(AccountFactory)
    recovery_method = AdvancePayment.RecoveryMethod.PERCENTAGE
    recovery_percentage = Decimal("10.00")


class RetentionFactory(DjangoModelFactory):
    """Factory for Retention model."""

    class Meta:
        model = Retention

    project = factory.SubFactory(ProjectFactory)
    payment_certificate = factory.SubFactory(PaymentCertificateFactory)
    transaction_type = Retention.TransactionType.DEBIT
    amount = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    description = factory.Faker("sentence")
    date = factory.LazyFunction(date.today)
    captured_by = factory.SubFactory(AccountFactory)
    retention_type = Retention.RetentionType.WITHHELD
    retention_percentage = Decimal("10.00")


class MaterialsOnSiteFactory(DjangoModelFactory):
    """Factory for MaterialsOnSite model."""

    class Meta:
        model = MaterialsOnSite

    project = factory.SubFactory(ProjectFactory)
    payment_certificate = factory.SubFactory(PaymentCertificateFactory)
    transaction_type = MaterialsOnSite.TransactionType.DEBIT
    amount = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    description = factory.Faker("sentence")
    date = factory.LazyFunction(date.today)
    captured_by = factory.SubFactory(AccountFactory)
    material_status = MaterialsOnSite.MaterialStatus.CLAIMED
    material_description = factory.Faker("sentence", nb_words=4)
    quantity = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    unit = "m3"


class EscalationFactory(DjangoModelFactory):
    """Factory for Escalation model."""

    class Meta:
        model = Escalation

    project = factory.SubFactory(ProjectFactory)
    payment_certificate = factory.SubFactory(PaymentCertificateFactory)
    transaction_type = Escalation.TransactionType.DEBIT
    amount = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    description = factory.Faker("sentence")
    date = factory.LazyFunction(date.today)
    captured_by = factory.SubFactory(AccountFactory)
    escalation_type = Escalation.EscalationType.COMBINED


class SpecialItemTransactionFactory(DjangoModelFactory):
    """Factory for SpecialItemTransaction model."""

    class Meta:
        model = SpecialItemTransaction

    project = factory.SubFactory(ProjectFactory)
    payment_certificate = factory.SubFactory(PaymentCertificateFactory)
    transaction_type = SpecialItemTransaction.TransactionType.DEBIT
    amount = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
    description = factory.Faker("sentence")
    date = factory.LazyFunction(date.today)
    captured_by = factory.SubFactory(AccountFactory)
    special_item_type = SpecialItemTransaction.SpecialItemType.PROVISIONAL
    item_reference = factory.Sequence(lambda n: f"SI-{n:03d}")


# ============================================================================
# Cashflow Factories
# ============================================================================


class BaselineCashflowFactory(DjangoModelFactory):
    """Factory for BaselineCashflow model."""

    class Meta:
        model = BaselineCashflow

    project = factory.SubFactory(ProjectFactory)
    version = 1
    period = factory.LazyFunction(lambda: date.today().replace(day=1))
    planned_value = factory.Faker(
        "pydecimal", left_digits=6, right_digits=2, positive=True
    )
    status = BaselineCashflow.Status.DRAFT


class RevisedBaselineFactory(DjangoModelFactory):
    """Factory for RevisedBaseline model."""

    class Meta:
        model = RevisedBaseline

    project = factory.SubFactory(ProjectFactory)
    revision_number = factory.Sequence(lambda n: n + 1)
    revision_date = factory.LazyFunction(date.today)
    revision_reason = RevisedBaseline.RevisionReason.VARIATION
    reason_description = factory.Faker("paragraph")
    status = RevisedBaseline.Status.DRAFT
    original_completion_date = factory.LazyFunction(
        lambda: date.today() + timedelta(days=180)
    )
    revised_completion_date = factory.LazyFunction(
        lambda: date.today() + timedelta(days=210)
    )


class RevisedBaselineDetailFactory(DjangoModelFactory):
    """Factory for RevisedBaselineDetail model."""

    class Meta:
        model = RevisedBaselineDetail

    revised_baseline = factory.SubFactory(RevisedBaselineFactory)
    period = factory.LazyFunction(lambda: date.today().replace(day=1))
    planned_value = factory.Faker(
        "pydecimal", left_digits=6, right_digits=2, positive=True
    )


class CashflowForecastFactory(DjangoModelFactory):
    """Factory for CashflowForecast model."""

    class Meta:
        model = CashflowForecast

    project = factory.SubFactory(ProjectFactory)
    forecast_date = factory.LazyFunction(date.today)
    forecast_period = factory.LazyFunction(lambda: date.today().replace(day=1))
    forecast_value = factory.Faker(
        "pydecimal", left_digits=6, right_digits=2, positive=True
    )
    status = CashflowForecast.Status.DRAFT
    captured_by = factory.SubFactory(AccountFactory)


# ============================================================================
# Schedule Factories
# ============================================================================


class SectionalCompletionDateFactory(DjangoModelFactory):
    """Factory for SectionalCompletionDate model."""

    class Meta:
        model = SectionalCompletionDate

    project = factory.SubFactory(ProjectFactory)
    section_name = factory.Sequence(lambda n: f"Section {n}")
    section_description = factory.Faker("sentence")
    planned_start_date = factory.LazyFunction(date.today)
    planned_completion_date = factory.LazyFunction(
        lambda: date.today() + timedelta(days=90)
    )
    status = SectionalCompletionDate.Status.NOT_STARTED


class ScheduleForecastFactory(DjangoModelFactory):
    """Factory for ScheduleForecast model."""

    class Meta:
        model = ScheduleForecast

    project = factory.SubFactory(ProjectFactory)
    forecast_date = factory.LazyFunction(date.today)
    reporting_period = factory.LazyFunction(lambda: date.today().replace(day=1))
    planned_project_completion = factory.LazyFunction(
        lambda: date.today() + timedelta(days=180)
    )
    forecast_project_completion = factory.LazyFunction(
        lambda: date.today() + timedelta(days=200)
    )
    status = ScheduleForecast.Status.DRAFT
    captured_by = factory.SubFactory(AccountFactory)


class ScheduleForecastSectionFactory(DjangoModelFactory):
    """Factory for ScheduleForecastSection model."""

    class Meta:
        model = ScheduleForecastSection

    schedule_forecast = factory.SubFactory(ScheduleForecastFactory)
    sectional_completion = factory.SubFactory(SectionalCompletionDateFactory)
    forecast_completion_date = factory.LazyFunction(
        lambda: date.today() + timedelta(days=95)
    )
