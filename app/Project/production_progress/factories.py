"""Factories for production progress models."""

import factory
from factory.django import DjangoModelFactory

from app.Project.tests.factories import ProjectFactory

from .production_models import (
    DailyActivityEntry,
    DailyLabourUsage,
    DailyPlantUsage,
    ProductionPlan,
    ProductionResource,
)


class ProductionPlanFactory(DjangoModelFactory):
    """Factory for ProductionPlan model."""

    class Meta:
        model = ProductionPlan

    project = factory.SubFactory(ProjectFactory)
    activity = factory.Sequence(lambda n: f"Activity {n}")
    start_date = factory.Faker("date_between", start_date="-1y", end_date="today")
    finish_date = factory.Faker("date_between", start_date="today", end_date="+1y")
    duration = 10
    quantity = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    unit = "m3"
    labour_activity = None


class DailyActivityEntryFactory(DjangoModelFactory):
    """Factory for DailyActivityEntry model."""

    class Meta:
        model = DailyActivityEntry

    project = factory.SubFactory(ProjectFactory)
    date = factory.Faker("date_between", start_date="-1y", end_date="today")
    notes = factory.Faker("text")
    production_plan = factory.SubFactory(
        ProductionPlanFactory, project=factory.SelfAttribute("..project")
    )
    quantity = 100
    hours_on_activity = 8.0


class DailyLabourUsageFactory(DjangoModelFactory):
    """Factory for DailyLabourUsage model."""

    class Meta:
        model = DailyLabourUsage

    entry = factory.SubFactory(DailyActivityEntryFactory)
    resource = factory.SubFactory(
        "app.Project.production_progress.factories.ProductionResourceFactory",
        production_plan=factory.SelfAttribute("..entry.production_plan"),
        resource_type="LABOUR",
    )
    number = 2
    hours = 8.0


class DailyPlantUsageFactory(DjangoModelFactory):
    """Factory for DailyPlantUsage model."""

    class Meta:
        model = DailyPlantUsage

    entry = factory.SubFactory(DailyActivityEntryFactory)
    resource = factory.SubFactory(
        "app.Project.production_progress.factories.ProductionResourceFactory",
        production_plan=factory.SelfAttribute("..entry.production_plan"),
        resource_type="PLANT",
    )
    hours = 8.0
    quantity = 50.0


class ProductionResourceFactory(DjangoModelFactory):
    """Factory for ProductionResource model."""

    class Meta:
        model = ProductionResource

    production_plan = factory.SubFactory(ProductionPlanFactory)
    resource_type = "PLANT"
    name = factory.Faker("word")
    number = 1
    days = 1
    rate = 100.0
