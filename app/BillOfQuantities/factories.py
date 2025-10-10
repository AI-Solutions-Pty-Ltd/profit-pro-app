"""Factories for Structure models."""

import factory
from factory.django import DjangoModelFactory

from app.Account.factories import AccountFactory
from app.BillOfQuantities.models import (
    ActualTransaction,
    Bill,
    LineItem,
    Package,
    PaymentCertificate,
    Structure,
)
from app.Project.factories import ProjectFactory


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
    certificate_number = factory.Sequence(lambda n: n + 1)
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
