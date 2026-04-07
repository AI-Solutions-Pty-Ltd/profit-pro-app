import factory
from factory.declarations import Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker

from app.Project.models import (
    JournalEntry,
    LabourCostTracker,
    LabourEntity,
    MaterialCostTracker,
    MaterialEntity,
    OverheadCostTracker,
    OverheadEntity,
    SubcontractorCostTracker,
    SubcontractorEntity,
)
from app.Project.tests.factories import ProjectFactory


class LabourEntityFactory(DjangoModelFactory):
    class Meta:
        model = LabourEntity

    project = SubFactory(ProjectFactory)
    person_name = Faker("name")
    id_number = Sequence(lambda n: f"ID-{n:04d}")
    rate = 150.00


class SubcontractorEntityFactory(DjangoModelFactory):
    class Meta:
        model = SubcontractorEntity

    project = SubFactory(ProjectFactory)
    name = Faker("company")
    rate = 500.00


class MaterialEntityFactory(DjangoModelFactory):
    class Meta:
        model = MaterialEntity

    project = SubFactory(ProjectFactory)
    name = Sequence(lambda n: f"Material {n}")
    rate = 50.00
    supplier = Faker("company")


class OverheadEntityFactory(DjangoModelFactory):
    class Meta:
        model = OverheadEntity

    project = SubFactory(ProjectFactory)
    name = Sequence(lambda n: f"Overhead {n}")
    rate = 100.00


class JournalEntryFactory(DjangoModelFactory):
    class Meta:
        model = JournalEntry

    project = SubFactory(ProjectFactory)
    date = factory.Faker("date_this_month")
    category = JournalEntry.Category.OTHER
    description = Faker("sentence")
    amount = 1000.00
    transaction_type = JournalEntry.EntryType.DEBIT


class SubcontractorCostTrackerFactory(DjangoModelFactory):
    class Meta:
        model = SubcontractorCostTracker

    project = SubFactory(ProjectFactory)
    subcontractor_entity = SubFactory(SubcontractorEntityFactory)
    date = factory.Faker("date_this_month")
    amount_of_days = 5
    rate = 500.00


class LabourCostTrackerFactory(DjangoModelFactory):
    class Meta:
        model = LabourCostTracker

    project = SubFactory(ProjectFactory)
    labour_entity = SubFactory(LabourEntityFactory)
    date = factory.Faker("date_this_month")
    amount_of_days = 5
    salary = 150.00


class MaterialCostTrackerFactory(DjangoModelFactory):
    class Meta:
        model = MaterialCostTracker

    project = SubFactory(ProjectFactory)
    material_entity = SubFactory(MaterialEntityFactory)
    date = factory.Faker("date_this_month")
    quantity = 10
    rate = 50.00


class OverheadCostTrackerFactory(DjangoModelFactory):
    class Meta:
        model = OverheadCostTracker

    project = SubFactory(ProjectFactory)
    overhead_entity = SubFactory(OverheadEntityFactory)
    date = factory.Faker("date_this_month")
    amount_of_days = 5
    rate = 100.00
