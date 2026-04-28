"""Factories for SiteManagement models."""

from factory.declarations import SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker

from app.Project.tests.factories import OverheadEntityFactory, ProjectFactory
from app.SiteManagement.models import OverheadDailyLog, PlantType, SkillType


class OverheadDailyLogFactory(DjangoModelFactory):
    """Factory for OverheadDailyLog model."""

    class Meta:
        model = OverheadDailyLog

    project = SubFactory(ProjectFactory)
    overhead_entity = SubFactory(OverheadEntityFactory)
    date = Faker("date_this_year")
    quantity = Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    remarks = Faker("text")


class PlantTypeFactory(DjangoModelFactory):
    """Factory for PlantType model."""

    class Meta:
        model = PlantType

    project = SubFactory(ProjectFactory)
    name = Faker("word")
    hourly_rate = Faker("pydecimal", left_digits=4, right_digits=2, positive=True)


class SkillTypeFactory(DjangoModelFactory):
    """Factory for SkillType model."""

    class Meta:
        model = SkillType

    project = SubFactory(ProjectFactory)
    name = Faker("word")
    hourly_rate = Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
