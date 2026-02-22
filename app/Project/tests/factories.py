"""Factories for Project models."""

import random
from datetime import timedelta

import factory
from django.contrib.auth.models import Group
from django.utils import timezone
from factory.declarations import LazyAttribute, LazyFunction, Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker
from factory.helpers import post_generation

from app.Account.models import Account
from app.Account.tests.factories import AccountFactory, UserFactory
from app.Project.models import (
    AdministrativeCompliance,
    Company,
    ContractualCompliance,
    FinalAccountCompliance,
    Milestone,
    PlannedValue,
    Project,
    ProjectCategory,
    ProjectDocument,
    ProjectRole,
    Risk,
    Role,
)


class ProjectCategoryFactory(DjangoModelFactory):
    """Factory for ProjectCategory model."""

    class Meta:
        model = ProjectCategory

    name = Sequence(lambda n: f"Category {n}")
    description = Faker("text")


class ClientFactory(DjangoModelFactory):
    """Factory for Client model."""

    class Meta:
        model = Company

    name = Sequence(lambda n: f"Client {n}")
    type = Company.Type.CLIENT

    @post_generation
    def users(self, create, extracted, **kwargs):
        """Add users to the client company."""
        if not create:
            return

        # Cast self to Company type for type checker
        # At runtime, self is actually the Company instance
        company: Company = self  # type: ignore

        # Get the actual model instance - it's passed as the first argument when called
        # In post_generation, the model instance is available via self when the method is called
        # But for type checking, we need to be careful
        if extracted:
            # If users were passed in, add them
            if isinstance(extracted, (list, tuple)):
                for user in extracted:
                    company.users.add(user)
            else:
                company.users.add(extracted)
        else:
            # Default: add a new user if none provided
            default_user = UserFactory.create()
            company.users.add(default_user)

    @post_generation
    def consultants(self, create, extracted, **kwargs):
        """Add consultants to the client company."""
        if not create:
            return

        # Cast self to Company type for type checker
        # At runtime, self is actually the Company instance
        company: Company = self  # type: ignore

        if extracted:
            # If consultants were passed in, add them
            if isinstance(extracted, (list, tuple)):
                for consultant in extracted:
                    company.consultants.add(consultant)

            else:
                company.consultants.add(extracted)

        else:
            # Default: add a new consultant if none provided
            default_consultant = UserFactory.create()
            company.consultants.add(default_consultant)

    @post_generation
    def add_consultant_to_group(self, create, extracted, **kwargs):
        """Add consultant users to consultant group."""
        if not create:
            return

        # Cast self to Company type for type checker
        # At runtime, self is actually the Company instance
        company: Company = self  # type: ignore

        # Get all consultants and add them to the consultant group
        # self refers to the model instance at runtime, not PostGeneration
        for consultant in company.consultants.all():
            # Cast to Account type to access type field
            account_consultant: Account = consultant  # type: ignore
            if hasattr(account_consultant, "type"):
                account_consultant.type = Account.Type.CONSULTANT
                account_consultant.save()

            consultant_group, _ = Group.objects.get_or_create(name="consultant")
            # Use getattr to safely access groups
            groups_manager = getattr(consultant, "groups", None)
            if groups_manager:
                groups_manager.add(consultant_group)


class ProjectFactory(DjangoModelFactory):
    """Factory for Project model."""

    class Meta:
        model = Project

    description = Faker("text")
    name = Sequence(lambda n: f"Project {n}")
    client = SubFactory(ClientFactory)
    category = SubFactory(ProjectCategoryFactory)
    start_date = Faker("date_between", start_date="-2y", end_date="today")
    end_date = LazyAttribute(
        lambda o: (
            o.start_date + timedelta(days=random.randint(3650, 7300))
            if o.start_date
            else Faker("date_between", start_date="today", end_date="+1y")
        )
    )

    @post_generation
    def users(self, create, extracted, **kwargs):
        # For ManyToManyField, we need to use the factory's instance
        # The instance is stored as self.instance in some versions
        # But the most compatible way is to use a RelatedManager
        if hasattr(self, "instance"):
            # Newer factory_boy versions
            instance: Project = self.instance  # type: ignore[attr-defined]
        else:
            # Older versions - we need to find the instance differently
            # This is a hack but works for older versions
            # Find the most recently created Project
            instance: Project = Project.objects.latest("created_at")

        # Add users to the project
        users_to_add = []
        if extracted:
            if isinstance(extracted, dict):
                users_to_add = extracted.values()
            elif isinstance(extracted, (list, tuple)):
                users_to_add = extracted
            else:
                users_to_add = [extracted]

        if not users_to_add:
            users_to_add = [AccountFactory.create()]

        # Add each user and create an admin role for them
        for user in users_to_add:
            instance.users.add(user)
            # Create admin project role for each user
            ProjectRole.objects.get_or_create(
                project=instance, user=user, role=Role.ADMIN
            )

    @post_generation
    def create_client_roles(self, create, extracted, **kwargs):
        """Create project roles for client users."""
        if not create:
            return

        # Get the project instance
        if hasattr(self, "instance"):
            instance: Project = self.instance  # type: ignore[attr-defined]
        else:
            instance: Project = Project.objects.latest("created_at")

        # Create roles for all client users
        if instance.client and instance.client.users.exists():
            for user in instance.client.users.all():
                ProjectRole.objects.get_or_create(
                    project=instance, user=user, role=Role.CLIENT
                )

        # Create roles for all consultant users
        if instance.client and instance.client.consultants.exists():
            for consultant in instance.client.consultants.all():
                ProjectRole.objects.get_or_create(
                    project=instance, user=consultant, role=Role.CONSULTANT
                )


class ProjectRoleFactory(DjangoModelFactory):
    """Factory for ProjectRole model."""

    class Meta:
        model = ProjectRole

    project = SubFactory(ProjectFactory)
    user = SubFactory(UserFactory)
    role = Role.ADMIN


class PlannedValueFactory(DjangoModelFactory):
    """Factory for PlannedValue model."""

    class Meta:
        model = PlannedValue

    project = SubFactory(ProjectFactory)
    period = LazyFunction(lambda: timezone.now().date().replace(day=1))
    value = Faker("pydecimal", left_digits=7, right_digits=2, positive=True)
    forecast_value = Faker("pydecimal", left_digits=7, right_digits=2, positive=True)


class MilestoneFactory(DjangoModelFactory):
    """Factory for Milestone model."""

    class Meta:
        model = Milestone

    project = SubFactory(ProjectFactory)
    name = Sequence(lambda n: f"Milestone {n}")
    planned_date = LazyFunction(lambda: timezone.now().date())
    forecast_date = None
    reason_for_change = ""
    sequence = Sequence(lambda n: n)
    is_completed = False
    actual_date = None


class ProjectDocumentFactory(DjangoModelFactory):
    """Factory for ProjectDocument model."""

    class Meta:
        model = ProjectDocument

    project = SubFactory(ProjectFactory)
    category = ProjectDocument.Category.CONTRACT_DOCUMENTS
    title = Sequence(lambda n: f"Document {n}")
    file = factory.django.FileField(filename="test_document.pdf")  # type: ignore
    uploaded_by = SubFactory(UserFactory)
    notes = ""


class RiskFactory(DjangoModelFactory):
    """Factory for Risk model."""

    class Meta:
        model = Risk

    project = SubFactory(ProjectFactory)
    risk_name = Sequence(lambda n: f"Risk {n}")
    description = Faker("paragraph")
    time_impact_start = LazyFunction(lambda: timezone.now().date())
    time_impact_end = LazyFunction(
        lambda: timezone.now().date() + __import__("datetime").timedelta(days=30)
    )
    cost_impact = Faker("pydecimal", left_digits=6, right_digits=2, positive=True)
    probability = Faker(
        "pydecimal", left_digits=2, right_digits=2, min_value=0, max_value=100
    )
    is_active = True
    created_by = SubFactory(UserFactory)


class ContractualComplianceFactory(DjangoModelFactory):
    """Factory for ContractualCompliance model."""

    class Meta:
        model = ContractualCompliance

    project = SubFactory(ProjectFactory)
    responsible_party = SubFactory(UserFactory)
    obligation_description = Sequence(lambda n: f"Contractual Obligation {n}")
    contract_reference = Sequence(lambda n: f"Clause {n}.1")
    due_date = LazyFunction(
        lambda: timezone.now().date() + __import__("datetime").timedelta(days=30)
    )
    frequency = ContractualCompliance.Frequency.MONTHLY
    expiry_date = None
    status = ContractualCompliance.Status.PENDING
    notes = ""
    created_by = SubFactory(UserFactory)


class AdministrativeComplianceFactory(DjangoModelFactory):
    """Factory for AdministrativeCompliance model."""

    class Meta:
        model = AdministrativeCompliance

    project = SubFactory(ProjectFactory)
    item_type = AdministrativeCompliance.ItemType.CERTIFICATE
    reference_number = Sequence(lambda n: f"REF-{n:04d}")
    description = Sequence(lambda n: f"Administrative Item {n}")
    responsible_party = SubFactory(UserFactory)
    submission_due_date = LazyFunction(
        lambda: timezone.now().date() + __import__("datetime").timedelta(days=14)
    )
    submission_date = None
    approval_due_date = LazyFunction(
        lambda: timezone.now().date() + __import__("datetime").timedelta(days=21)
    )
    approval_date = None
    status = AdministrativeCompliance.Status.DRAFT
    notes = ""
    created_by = SubFactory(UserFactory)


class FinalAccountComplianceFactory(DjangoModelFactory):
    """Factory for FinalAccountCompliance model."""

    class Meta:
        model = FinalAccountCompliance

    project = SubFactory(ProjectFactory)
    document_type = FinalAccountCompliance.DocumentType.TEST_CERTIFICATE
    description = Sequence(lambda n: f"Final Account Document {n}")
    responsible_party = SubFactory(UserFactory)
    test_date = None
    submission_date = None
    approval_date = None
    status = FinalAccountCompliance.Status.REQUIRED
    file = None
    notes = ""
    created_by = SubFactory(UserFactory)
