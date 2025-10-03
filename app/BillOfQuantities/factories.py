"""Factories for Structure models."""

import factory
from factory.django import DjangoModelFactory

from app.BillOfQuantities.models import Structure
from app.Project.factories import ProjectFactory


class StructureFactory(DjangoModelFactory):
    """Factory for Structure model."""

    class Meta:
        model = Structure

    project = factory.SubFactory(ProjectFactory)
    name = factory.Sequence(lambda n: f"Structure {n}")
    description = factory.Faker("sentence")
