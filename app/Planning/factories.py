"""Factories for Planning & Procurement models."""

from factory.declarations import LazyAttribute, Sequence, SubFactory
from factory.django import DjangoModelFactory, FileField
from factory.faker import Faker

from app.Planning.models import (
    DesignCategory,
    DesignCategoryFile,
    DesignDiscipline,
    DesignDisciplineFile,
    DesignGroup,
    DesignGroupFile,
    DesignStage,
    DesignSubCategory,
    DesignSubCategoryFile,
    TenderDocument,
    WorkPackage,
)
from app.Project.tests.factories import ProjectFactory


class WorkPackageFactory(DjangoModelFactory):
    """Factory for WorkPackage model."""

    class Meta:
        model = WorkPackage

    project = SubFactory(ProjectFactory)
    name = Sequence(lambda n: f"Work Package {n}")
    description = Faker("text")
    advert_start_date = Faker("date_between", start_date="-1y", end_date="today")
    advert_end_date = LazyAttribute(
        lambda o: (
            o.advert_start_date + __import__("datetime").timedelta(days=30)
            if o.advert_start_date
            else None
        )
    )
    site_inspection_percentage = 0
    site_inspection_complete = False
    tender_close_percentage = 0
    tender_close_complete = False
    tender_evaluation_percentage = 0
    tender_evaluation_complete = False
    award_signing_percentage = 0
    award_signing_complete = False
    mobilization_percentage = 0
    mobilization_complete = False


class TenderDocumentFactory(DjangoModelFactory):
    """Factory for TenderDocument model."""

    class Meta:
        model = TenderDocument

    work_package = SubFactory(WorkPackageFactory)
    name = Sequence(lambda n: f"Tender Document {n}")
    percentage_completed = 0


class DesignCategoryFactory(DjangoModelFactory):
    """Factory for DesignCategory model."""

    class Meta:
        model = DesignCategory

    work_package = SubFactory(WorkPackageFactory)
    category = SubFactory("app.Project.tests.factories.CategoryFactory")
    stage = DesignStage.DESIGN_CRITERIA
    approved = False


class DesignCategoryFileFactory(DjangoModelFactory):
    """Factory for DesignCategoryFile model."""

    class Meta:
        model = DesignCategoryFile

    design_category = SubFactory(DesignCategoryFactory)
    file = FileField(filename="test_design_category.pdf")
    description = Faker("sentence")


class DesignSubCategoryFactory(DjangoModelFactory):
    """Factory for DesignSubCategory model."""

    class Meta:
        model = DesignSubCategory

    work_package = SubFactory(WorkPackageFactory)
    sub_category = SubFactory("app.Project.tests.factories.SubCategoryFactory")
    stage = DesignStage.DESIGN_CRITERIA
    approved = False


class DesignSubCategoryFileFactory(DjangoModelFactory):
    """Factory for DesignSubCategoryFile model."""

    class Meta:
        model = DesignSubCategoryFile

    design_sub_category = SubFactory(DesignSubCategoryFactory)
    file = FileField(filename="test_design_subcategory.pdf")
    description = Faker("sentence")


class DesignGroupFactory(DjangoModelFactory):
    """Factory for DesignGroup model."""

    class Meta:
        model = DesignGroup

    work_package = SubFactory(WorkPackageFactory)
    group = SubFactory("app.Project.tests.factories.GroupFactory")
    stage = DesignStage.DESIGN_CRITERIA
    approved = False


class DesignGroupFileFactory(DjangoModelFactory):
    """Factory for DesignGroupFile model."""

    class Meta:
        model = DesignGroupFile

    design_group = SubFactory(DesignGroupFactory)
    file = FileField(filename="test_design_group.pdf")
    description = Faker("sentence")


class DesignDisciplineFactory(DjangoModelFactory):
    """Factory for DesignDiscipline model."""

    class Meta:
        model = DesignDiscipline

    work_package = SubFactory(WorkPackageFactory)
    discipline = SubFactory("app.Project.tests.factories.DisciplineFactory")
    stage = DesignStage.DESIGN_CRITERIA
    approved = False


class DesignDisciplineFileFactory(DjangoModelFactory):
    """Factory for DesignDisciplineFile model."""

    class Meta:
        model = DesignDisciplineFile

    design_discipline = SubFactory(DesignDisciplineFactory)
    file = FileField(filename="test_design_discipline.pdf")
    description = Faker("sentence")
