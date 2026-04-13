"""Factories for production progress models."""

import factory
from factory.django import DjangoModelFactory

from app.BillOfQuantities.tests.factories import (
    BillFactory,
    PackageFactory,
    StructureFactory,
)
from app.Project.tests.factories import ProjectFactory

from .production_models import ProductionPlan


class ProductionPlanFactory(DjangoModelFactory):
    """Factory for ProductionPlan model."""

    class Meta:
        model = ProductionPlan

    project = factory.SubFactory(ProjectFactory)
    structure = factory.SubFactory(
        StructureFactory, project=factory.SelfAttribute("..project")
    )
    bill = factory.SubFactory(
        BillFactory, structure=factory.SelfAttribute("..structure")
    )
    package = factory.SubFactory(PackageFactory, bill=factory.SelfAttribute("..bill"))
    activity = factory.Sequence(lambda n: f"Activity {n}")
    start_date = factory.Faker("date_between", start_date="-1y", end_date="today")
    finish_date = factory.Faker("date_between", start_date="today", end_date="+1y")
    duration = 10
    quantity = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    unit = "m3"
