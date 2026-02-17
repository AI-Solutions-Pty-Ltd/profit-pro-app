"""Factories for Ledger models."""

from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone
from factory import fuzzy
from factory.django import DjangoModelFactory

from app.BillOfQuantities.tests.factories import BillFactory
from app.Ledger.models import Ledger, Transaction, Vat
from app.Project.tests.factories import ClientFactory


class VatFactory(DjangoModelFactory):
    """Factory for Vat model."""

    class Meta:
        model = Vat

    name = factory.Sequence(lambda n: f"VAT Rate {n}")
    rate = fuzzy.FuzzyChoice([Decimal("0.00"), Decimal("7.00"), Decimal("15.00")])
    start_date = factory.LazyFunction(lambda: timezone.now().date())
    end_date = factory.LazyFunction(
        lambda: timezone.now().date() + timedelta(days=3650)
    )


class LedgerFactory(DjangoModelFactory):
    """Factory for Ledger model."""

    class Meta:
        model = Ledger

    company = factory.SubFactory(ClientFactory)
    financial_statement = fuzzy.FuzzyChoice(
        Ledger.FinancialStatement.choices, getter=lambda c: c[0]
    )
    code = factory.Sequence(lambda n: f"{n:04d}")
    name = factory.Sequence(lambda n: f"Ledger Account {n}")


class TransactionFactory(DjangoModelFactory):
    """Factory for Transaction model."""

    class Meta:
        model = Transaction

    company = factory.SubFactory(ClientFactory)
    ledger = factory.SubFactory(LedgerFactory)
    bill = factory.SubFactory(BillFactory)
    date = factory.LazyFunction(lambda: timezone.now().date())
    type = fuzzy.FuzzyChoice(Transaction.TransactionType.choices, getter=lambda c: c[0])
    amount_excl_vat = fuzzy.FuzzyDecimal(0.01, 10000.00, 2)
    amount_incl_vat = fuzzy.FuzzyDecimal(0.01, 11500.00, 2)
    vat = fuzzy.FuzzyChoice([True, False])
    vat_rate = factory.SubFactory(VatFactory)
