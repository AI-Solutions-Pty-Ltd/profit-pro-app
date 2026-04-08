"""Factories for SiteManagement models."""

import factory
from factory.declarations import Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker

from app.Project.tests.factories import OverheadEntityFactory, ProjectFactory
from app.SiteManagement.models import OverheadDailyLog


class OverheadDailyLogFactory(DjangoModelFactory):
    """Factory for OverheadDailyLog model."""

    class Meta:
        model = OverheadDailyLog

    project = SubFactory(ProjectFactory)
    overhead_entity = SubFactory(OverheadEntityFactory)
    date = Faker("date_this_year")
    quantity = Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    remarks = Faker("text")
