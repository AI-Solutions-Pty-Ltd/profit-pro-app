"""Tests for new BillOfQuantities models."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.models import (
    AdvancePayment,
    ContractualCorrespondence,
    ContractVariation,
    Escalation,
    MaterialsOnSite,
    Retention,
    SpecialItemTransaction,
)
from app.BillOfQuantities.tests.factories import (
    AdvancePaymentFactory,
    BaselineCashflowFactory,
    CashflowForecastFactory,
    ContractualCorrespondenceFactory,
    ContractVariationFactory,
    EscalationFactory,
    MaterialsOnSiteFactory,
    PaymentCertificateFactory,
    RetentionFactory,
    RevisedBaselineDetailFactory,
    RevisedBaselineFactory,
    ScheduleForecastFactory,
    ScheduleForecastSectionFactory,
    SectionalCompletionDateFactory,
    SpecialItemTransactionFactory,
)
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestContractVariationModel:
    """Test cases for ContractVariation model."""

    def test_contract_variation_creation(self):
        """Test creating a contract variation."""
        variation = ContractVariationFactory.create()
        assert variation.id is not None
        assert variation.variation_number is not None
        assert variation.project is not None

    def test_contract_variation_str(self):
        """Test string representation."""
        variation = ContractVariationFactory.create(
            variation_number="VAR-001", title="Test Variation"
        )
        assert str(variation) == "VAR-001: Test Variation"

    def test_contract_variation_categories(self):
        """Test all variation categories are valid."""
        for category in ContractVariation.Category:
            variation = ContractVariationFactory.create(category=category)
            assert variation.category == category

    def test_contract_variation_types(self):
        """Test all variation types are valid."""
        for var_type in ContractVariation.VariationType:
            variation = ContractVariationFactory.create(variation_type=var_type)
            assert variation.variation_type == var_type


@pytest.mark.django_db
class TestContractualCorrespondenceModel:
    """Test cases for ContractualCorrespondence model."""

    def test_correspondence_creation(self):
        """Test creating a correspondence."""
        correspondence = ContractualCorrespondenceFactory.create()
        assert correspondence.id is not None
        assert correspondence.reference_number is not None

    def test_correspondence_str(self):
        """Test string representation."""
        correspondence = ContractualCorrespondenceFactory.create(
            reference_number="CORR-001", subject="Test Subject"
        )
        assert str(correspondence) == "CORR-001: Test Subject"

    def test_correspondence_types(self):
        """Test all correspondence types are valid."""
        for corr_type in ContractualCorrespondence.CorrespondenceType:
            correspondence = ContractualCorrespondenceFactory.create(
                correspondence_type=corr_type
            )
            assert correspondence.correspondence_type == corr_type

    def test_correspondence_with_user_fields(self):
        """Test correspondence with user fields."""
        sender = AccountFactory.create()
        recipient = AccountFactory.create()

        correspondence = ContractualCorrespondenceFactory.create(
            sender_user=sender,
            recipient_user=recipient,
            sender="String Sender",
            recipient="String Recipient",
        )

        assert correspondence.sender_user == sender
        assert correspondence.recipient_user == recipient
        assert correspondence.sender == "String Sender"
        assert correspondence.recipient == "String Recipient"

    def test_correspondence_directions(self):
        """Test all correspondence directions are valid."""
        for direction in ContractualCorrespondence.Direction:
            correspondence = ContractualCorrespondenceFactory.create(
                direction=direction
            )
            assert correspondence.direction == direction


@pytest.mark.django_db
class TestAdvancePaymentModel:
    """Test cases for AdvancePayment model."""

    def test_advance_payment_creation(self):
        """Test creating an advance payment."""
        advance = AdvancePaymentFactory.create()
        assert advance.pk is not None
        assert advance.amount is not None

    def test_advance_payment_signed_amount_debit(self):
        """Test signed amount for debit transaction."""
        advance = AdvancePaymentFactory.create(
            transaction_type=AdvancePayment.TransactionType.DEBIT,
            amount=Decimal("10000.00"),
        )
        assert advance.signed_amount == Decimal("10000.00")

    def test_advance_payment_signed_amount_credit(self):
        """Test signed amount for credit transaction."""
        advance = AdvancePaymentFactory.create(
            transaction_type=AdvancePayment.TransactionType.CREDIT,
            amount=Decimal("5000.00"),
        )
        assert advance.signed_amount == Decimal("-5000.00")

    def test_advance_payment_balance_calculation(self):
        """Test balance calculation for a project."""
        project = ProjectFactory.create()
        cert = PaymentCertificateFactory.create(project=project)

        # Add advance (debit)
        AdvancePaymentFactory.create(
            project=project,
            payment_certificate=cert,
            transaction_type=AdvancePayment.TransactionType.DEBIT,
            amount=Decimal("10000.00"),
        )
        # Recovery (credit)
        AdvancePaymentFactory.create(
            project=project,
            payment_certificate=cert,
            transaction_type=AdvancePayment.TransactionType.CREDIT,
            amount=Decimal("2000.00"),
        )

        balance = AdvancePayment.get_balance_for_project(project)
        assert balance == Decimal("8000.00")


@pytest.mark.django_db
class TestRetentionModel:
    """Test cases for Retention model."""

    def test_retention_creation(self):
        """Test creating a retention."""
        retention = RetentionFactory.create()
        assert retention.id is not None
        assert retention.retention_type is not None

    def test_retention_types(self):
        """Test all retention types are valid."""
        for ret_type in Retention.RetentionType:
            retention = RetentionFactory.create(retention_type=ret_type)
            assert retention.retention_type == ret_type


@pytest.mark.django_db
class TestMaterialsOnSiteModel:
    """Test cases for MaterialsOnSite model."""

    def test_materials_creation(self):
        """Test creating materials on site."""
        materials = MaterialsOnSiteFactory.create()
        assert materials.id is not None
        assert materials.material_description is not None

    def test_materials_status_choices(self):
        """Test all material status choices are valid."""
        for status in MaterialsOnSite.MaterialStatus:
            materials = MaterialsOnSiteFactory.create(material_status=status)
            assert materials.material_status == status


@pytest.mark.django_db
class TestEscalationModel:
    """Test cases for Escalation model."""

    def test_escalation_creation(self):
        """Test creating an escalation."""
        escalation = EscalationFactory.create()
        assert escalation.id is not None
        assert escalation.escalation_type is not None

    def test_escalation_types(self):
        """Test all escalation types are valid."""
        for esc_type in Escalation.EscalationType:
            escalation = EscalationFactory.create(escalation_type=esc_type)
            assert escalation.escalation_type == esc_type


@pytest.mark.django_db
class TestSpecialItemTransactionModel:
    """Test cases for SpecialItemTransaction model."""

    def test_special_item_creation(self):
        """Test creating a special item transaction."""
        special = SpecialItemTransactionFactory.create()
        assert special.id is not None
        assert special.special_item_type is not None

    def test_special_item_types(self):
        """Test all special item types are valid."""
        for item_type in SpecialItemTransaction.SpecialItemType:
            special = SpecialItemTransactionFactory.create(special_item_type=item_type)
            assert special.special_item_type == item_type


@pytest.mark.django_db
class TestBaselineCashflowModel:
    """Test cases for BaselineCashflow model."""

    def test_baseline_creation(self):
        """Test creating a baseline cashflow."""
        baseline = BaselineCashflowFactory.create()
        assert baseline.id is not None
        assert baseline.planned_value is not None

    def test_baseline_period_normalization(self):
        """Test that period is normalized to first day of month."""
        baseline = BaselineCashflowFactory.create(period=date(2024, 6, 15))
        assert baseline.period.day == 1

    def test_baseline_str(self):
        """Test string representation."""
        baseline = BaselineCashflowFactory.create(version=1, period=date(2024, 6, 1))
        assert "v1" in str(baseline)
        assert "2024-06-01" in str(baseline)


@pytest.mark.django_db
class TestRevisedBaselineModel:
    """Test cases for RevisedBaseline model."""

    def test_revised_baseline_creation(self):
        """Test creating a revised baseline."""
        revised = RevisedBaselineFactory.create()
        assert revised.id is not None
        assert revised.revision_number is not None

    def test_time_extension_days_calculation(self):
        """Test time extension days calculation."""
        revised = RevisedBaselineFactory.create(
            original_completion_date=date(2024, 12, 31),
            revised_completion_date=date(2025, 1, 30),
        )
        assert revised.time_extension_days == 30

    def test_value_change_calculation(self):
        """Test value change calculation."""
        revised = RevisedBaselineFactory.create(
            original_contract_value=Decimal("1000000.00"),
            revised_contract_value=Decimal("1150000.00"),
        )
        assert revised.value_change == Decimal("150000.00")


@pytest.mark.django_db
class TestRevisedBaselineDetailModel:
    """Test cases for RevisedBaselineDetail model."""

    def test_detail_creation(self):
        """Test creating a baseline detail."""
        detail = RevisedBaselineDetailFactory.create()
        assert detail.id is not None
        assert detail.planned_value is not None

    def test_detail_period_normalization(self):
        """Test that period is normalized to first day of month."""
        detail = RevisedBaselineDetailFactory.create(period=date(2024, 6, 15))
        assert detail.period.day == 1


@pytest.mark.django_db
class TestCashflowForecastModel:
    """Test cases for CashflowForecast model."""

    def test_forecast_creation(self):
        """Test creating a cashflow forecast."""
        forecast = CashflowForecastFactory.create()
        assert forecast.id is not None
        assert forecast.forecast_value is not None

    def test_forecast_variance_calculation(self):
        """Test variance is calculated on save."""
        forecast = CashflowForecastFactory.create(
            forecast_value=Decimal("120000.00"),
            baseline_value=Decimal("100000.00"),
        )
        assert forecast.variance == Decimal("20000.00")


@pytest.mark.django_db
class TestSectionalCompletionDateModel:
    """Test cases for SectionalCompletionDate model."""

    def test_sectional_creation(self):
        """Test creating a sectional completion date."""
        sectional = SectionalCompletionDateFactory.create()
        assert sectional.id is not None
        assert sectional.section_name is not None

    def test_days_variance_calculation(self):
        """Test days variance calculation."""
        sectional = SectionalCompletionDateFactory.create(
            planned_completion_date=date(2024, 12, 31),
            forecast_completion_date=date(2025, 1, 15),
        )
        assert sectional.days_variance == 15
        assert sectional.is_delayed is True

    def test_days_to_completion(self):
        """Test days to completion calculation."""
        future_date = date.today() + timedelta(days=30)
        sectional = SectionalCompletionDateFactory.create(
            planned_completion_date=future_date
        )
        assert sectional.days_to_completion == 30

    def test_estimated_penalty(self):
        """Test estimated penalty calculation."""
        sectional = SectionalCompletionDateFactory.create(
            planned_completion_date=date(2024, 1, 1),
            forecast_completion_date=date(2024, 1, 11),
            has_penalty=True,
            penalty_rate=Decimal("1000.00"),
            penalty_cap=Decimal("50000.00"),
        )
        assert sectional.estimated_penalty == Decimal("10000.00")


@pytest.mark.django_db
class TestScheduleForecastModel:
    """Test cases for ScheduleForecast model."""

    def test_forecast_creation(self):
        """Test creating a schedule forecast."""
        forecast = ScheduleForecastFactory.create()
        assert forecast.id is not None
        assert forecast.planned_project_completion is not None

    def test_days_variance(self):
        """Test days variance calculation."""
        forecast = ScheduleForecastFactory.create(
            planned_project_completion=date(2024, 12, 31),
            forecast_project_completion=date(2025, 1, 20),
        )
        assert forecast.days_variance == 20
        assert forecast.is_delayed is True

    def test_schedule_variance_percentage(self):
        """Test schedule variance percentage calculation."""
        forecast = ScheduleForecastFactory.create(
            overall_percentage_complete=Decimal("45.00"),
            planned_percentage_complete=Decimal("50.00"),
        )
        assert forecast.schedule_variance_percentage == Decimal("-5.00")


@pytest.mark.django_db
class TestScheduleForecastSectionModel:
    """Test cases for ScheduleForecastSection model."""

    def test_section_forecast_creation(self):
        """Test creating a schedule forecast section."""
        section = ScheduleForecastSectionFactory.create()
        assert section.id is not None
        assert section.forecast_completion_date is not None

    def test_section_days_variance(self):
        """Test section days variance calculation."""
        sectional = SectionalCompletionDateFactory.create(
            planned_completion_date=date(2024, 6, 30)
        )
        section = ScheduleForecastSectionFactory.create(
            sectional_completion=sectional,
            forecast_completion_date=date(2024, 7, 10),
        )
        assert section.days_variance == 10
