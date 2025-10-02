"""Factories for Project models."""

import factory
from factory.django import DjangoModelFactory

from app.Account.factories import AccountFactory
from app.Project.models import Project


class ProjectFactory(DjangoModelFactory):
    """Factory for Project model."""

    class Meta:
        model = Project

    account = factory.SubFactory(AccountFactory)
    name = factory.Sequence(lambda n: f"Project {n}")
