"""Factories for Ledger models."""

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from factory import fuzzy
from factory.declarations import LazyFunction, Sequence, SubFactory
from factory.django import DjangoModelFactory

from app.BillOfQuantities.tests.factories import BillFactory
from app.Ledger.models import FinancialStatement, Ledger, Transaction, Vat
from app.Project.tests.factories import ClientFactory


class VatFactory(DjangoModelFactory):
    """Factory for Vat model."""

    class Meta:
        model = Vat

    name = Sequence(lambda n: f"VAT Rate {n}")
    rate = fuzzy.FuzzyChoice([Decimal("0.00"), Decimal("7.00"), Decimal("15.00")])
    start_date = LazyFunction(lambda: timezone.now().date())
    end_date = LazyFunction(lambda: timezone.now().date() + timedelta(days=3650))


class FinancialStatementFactory(DjangoModelFactory):
    """Factory for FinancialStatement model."""

    class Meta:
        model = FinancialStatement

    name = Sequence(lambda n: f"Financial Statement {n}")


class LedgerFactory(DjangoModelFactory):
    """Factory for Ledger model."""

    class Meta:
        model = Ledger

    company = SubFactory(ClientFactory)
    financial_statement = SubFactory(FinancialStatementFactory)
    code = Sequence(lambda n: f"{n:04d}")
    name = Sequence(lambda n: f"Ledger Account {n}")


class TransactionFactory(DjangoModelFactory):
    """Factory for Transaction model."""

    class Meta:
        model = Transaction

    company = SubFactory(ClientFactory)
    debit_ledger = SubFactory(LedgerFactory)
    credit_ledger = SubFactory(LedgerFactory)
    bill = SubFactory(BillFactory)
    date = LazyFunction(lambda: timezone.now().date())
    amount_excl_vat = fuzzy.FuzzyDecimal(0.01, 10000.00, 2)
    amount_incl_vat = fuzzy.FuzzyDecimal(0.01, 11500.00, 2)
    vat = fuzzy.FuzzyChoice([True, False])
    vat_rate = SubFactory(VatFactory)
