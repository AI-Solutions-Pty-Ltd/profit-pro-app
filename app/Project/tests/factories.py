"""Factories for Project models."""

import factory
from django.contrib.auth.models import Group
from factory import Faker
from factory.django import DjangoModelFactory

from app.Account.models import Account
from app.Account.tests.factories import UserFactory
from app.Project.models import Client, Project


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
