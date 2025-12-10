"""Factories for Project models."""

import factory
from django.contrib.auth.models import Group
from django.utils import timezone
from factory import Faker
from factory.django import DjangoModelFactory

from app.Account.models import Account
from app.Account.tests.factories import UserFactory
from app.Project.models import (
    Client,
    Milestone,
    PlannedValue,
    Project,
    ProjectCategory,
    ProjectDocument,
    Risk,
)


class ProjectCategoryFactory(DjangoModelFactory):
    """Factory for ProjectCategory model."""

    class Meta:
        model = ProjectCategory

    name = factory.Sequence(lambda n: f"Category {n}")
    description = Faker("text")


class ClientFactory(DjangoModelFactory):
    """Factory for Client model."""

    class Meta:
        model = Client

    name = factory.Sequence(lambda n: f"Client {n}")
    description = Faker("text")
    user = factory.SubFactory(UserFactory)
    consultant = factory.SubFactory(UserFactory)

    @factory.post_generation
    def add_consultant_to_group(self, create, extracted, **kwargs):
        """Add consultant user to consultant group."""
        self.consultant.type = Account.Type.CONSULTANT
        self.consultant.save()
        if not create or not self.consultant:
            return

        consultant_group, _ = Group.objects.get_or_create(name="consultant")
        self.consultant.groups.add(consultant_group)


class ProjectFactory(DjangoModelFactory):
    """Factory for Project model."""

    class Meta:
        model = Project

    description = Faker("text")
    name = factory.Sequence(lambda n: f"Project {n}")
    account = factory.SubFactory(UserFactory)
    client = factory.SubFactory(ClientFactory)
    category = factory.SubFactory(ProjectCategoryFactory)


class PlannedValueFactory(DjangoModelFactory):
    """Factory for PlannedValue model."""

    class Meta:
        model = PlannedValue

    project = factory.SubFactory(ProjectFactory)
    period = factory.LazyFunction(lambda: timezone.now().date().replace(day=1))
    value = factory.Faker("pydecimal", left_digits=7, right_digits=2, positive=True)
    forecast_value = factory.Faker(
        "pydecimal", left_digits=7, right_digits=2, positive=True
    )


class MilestoneFactory(DjangoModelFactory):
    """Factory for Milestone model."""

    class Meta:
        model = Milestone

    project = factory.SubFactory(ProjectFactory)
    name = factory.Sequence(lambda n: f"Milestone {n}")
    planned_date = factory.LazyFunction(lambda: timezone.now().date())
    forecast_date = None
    reason_for_change = ""
    sequence = factory.Sequence(lambda n: n)
    is_completed = False
    actual_date = None


class ProjectDocumentFactory(DjangoModelFactory):
    """Factory for ProjectDocument model."""

    class Meta:
        model = ProjectDocument

    project = factory.SubFactory(ProjectFactory)
    category = ProjectDocument.Category.CONTRACT_DOCUMENTS
    title = factory.Sequence(lambda n: f"Document {n}")
    file = factory.django.FileField(filename="test_document.pdf")
    uploaded_by = factory.SubFactory(UserFactory)
    notes = ""


class RiskFactory(DjangoModelFactory):
    """Factory for Risk model."""

    class Meta:
        model = Risk

    project = factory.SubFactory(ProjectFactory)
    risk_name = factory.Sequence(lambda n: f"Risk {n}")
    description = Faker("paragraph")
    time_impact_start = factory.LazyFunction(lambda: timezone.now().date())
    time_impact_end = factory.LazyFunction(
        lambda: timezone.now().date() + __import__("datetime").timedelta(days=30)
    )
    cost_impact = Faker("pydecimal", left_digits=6, right_digits=2, positive=True)
    probability = Faker(
        "pydecimal", left_digits=2, right_digits=2, min_value=0, max_value=100
    )
    is_active = True
    created_by = factory.SubFactory(UserFactory)
