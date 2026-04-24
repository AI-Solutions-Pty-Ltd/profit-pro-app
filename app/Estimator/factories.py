"""Factories for Estimator models."""

import factory
from factory.django import DjangoModelFactory

from app.Estimator.models import (
    BOQItem,
    ProjectPlantCost,
    ProjectPlantSpecification,
    ProjectPlantSpecificationComponent,
)
from app.Project.tests.factories import ProjectFactory


class ProjectPlantCostFactory(DjangoModelFactory):
    """Factory for ProjectPlantCost model."""

    class Meta:
        model = ProjectPlantCost

    project = factory.SubFactory(ProjectFactory)
    name = factory.Sequence(lambda n: f"Plant Type {n}")
    hourly_rate = 150.00


class ProjectPlantSpecificationFactory(DjangoModelFactory):
    """Factory for ProjectPlantSpecification model."""

    class Meta:
        model = ProjectPlantSpecification

    project = factory.SubFactory(ProjectFactory)
    name = factory.Sequence(lambda n: f"Plant Spec {n}")


class ProjectPlantSpecificationComponentFactory(DjangoModelFactory):
    """Factory for ProjectPlantSpecificationComponent model."""

    class Meta:
        model = ProjectPlantSpecificationComponent

    specification = factory.SubFactory(ProjectPlantSpecificationFactory)
    plant_type = factory.SubFactory(
        ProjectPlantCostFactory,
        project=factory.SelfAttribute("..specification.project"),
    )
    hours = 8.0


class BOQItemFactory(DjangoModelFactory):
    """Factory for BOQItem model."""

    class Meta:
        model = BOQItem

    project = factory.SubFactory(ProjectFactory)
    section = "Section A"
    bill_no = "Bill 1"
    item_no = factory.Sequence(lambda n: f"Item {n}")
    description = factory.Faker("text")
    contract_quantity = 100
    contract_rate = 250.00
