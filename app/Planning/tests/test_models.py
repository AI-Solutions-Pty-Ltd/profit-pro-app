"""Tests for Planning & Procurement models."""

import pytest
from django.db import IntegrityError

from app.Planning.factories import (
    DesignCategoryFactory,
    DesignDisciplineFactory,
    DesignGroupFactory,
    DesignSubCategoryFactory,
    TenderDocumentFactory,
    WorkPackageFactory,
)


class TestWorkPackageModel:
    """Test cases for WorkPackage model."""

    def test_work_package_creation(self):
        """Test creating a work package with valid data."""
        work_package = WorkPackageFactory()
        assert work_package.id is not None
        assert work_package.name is not None
        assert work_package.project is not None
        assert work_package.overall_percentage == 0.0

    def test_work_package_str_representation(self):
        """Test string representation of work package."""
        work_package = WorkPackageFactory(name="Test Work Package")
        assert str(work_package) == "Test Work Package"

    def test_create_default_tender_documents(self):
        """Test that default tender documents are created."""
        work_package = WorkPackageFactory()
        work_package.create_default_tender_documents()

        default_docs = [
            "L1 Bill of Quantities",
            "Specification",
            "Drawings",
            "Conditions of Contract",
            "Scope of Work",
        ]

        assert work_package.tender_documents.count() == 5
        for doc_name in default_docs:
            assert work_package.tender_documents.filter(name=doc_name).exists()

    def test_overall_percentage_calculation(self):
        """Test overall percentage calculation."""
        work_package = WorkPackageFactory(
            site_inspection_percentage=50,
            tender_close_percentage=75,
            tender_evaluation_percentage=25,
            award_signing_percentage=100,
            mobilization_percentage=0,
        )
        expected = (50 + 75 + 25 + 100 + 0) / 5
        assert work_package.overall_percentage == expected


class TestTenderDocumentModel:
    """Test cases for TenderDocument model."""

    def test_tender_document_creation(self):
        """Test creating a tender document."""
        document = TenderDocumentFactory()
        assert document.id is not None
        assert document.work_package is not None
        assert document.name is not None

    def test_tender_document_str_representation(self):
        """Test string representation of tender document."""
        wp = WorkPackageFactory(name="Test WP")
        doc = TenderDocumentFactory(work_package=wp, name="Test Doc")
        expected = "Test WP - Test Doc"
        assert str(doc) == expected

    def test_tender_document_unique_constraint(self):
        """Test that tender document names are unique within work package."""
        wp = WorkPackageFactory()
        TenderDocumentFactory(work_package=wp, name="Test Doc")

        # Creating another with same name should raise IntegrityError
        with pytest.raises(IntegrityError):
            TenderDocumentFactory(work_package=wp, name="Test Doc")

    def test_is_complete_property(self):
        """Test is_complete property."""
        doc = TenderDocumentFactory(file=None)
        assert not doc.is_complete

        doc.file = "test.pdf"
        doc.save()
        assert doc.is_complete

    def test_auto_percentage_on_file_upload(self):
        """Test that percentage is set to 100 when file is uploaded."""
        doc = TenderDocumentFactory(file=None, percentage_completed=0)
        doc.file = "test.pdf"
        doc.save()
        assert doc.percentage_completed == 100


class TestDesignCategoryModel:
    """Test cases for DesignCategory model."""

    def test_design_category_creation(self):
        """Test creating a design category."""
        design_cat = DesignCategoryFactory()
        assert design_cat.id is not None
        assert design_cat.work_package is not None
        assert design_cat.category is not None

    def test_design_category_str_representation(self):
        """Test string representation of design category."""
        design_cat = DesignCategoryFactory()
        assert str(design_cat) == f"{design_cat.category.name} - Design Criteria"


class TestDesignSubCategoryModel:
    """Test cases for DesignSubCategory model."""

    def test_design_subcategory_creation(self):
        """Test creating a design subcategory."""
        design_subcat = DesignSubCategoryFactory()
        assert design_subcat.id is not None
        assert design_subcat.work_package is not None
        assert design_subcat.sub_category is not None

    def test_design_subcategory_str_representation(self):
        """Test string representation of design subcategory."""
        design_subcat = DesignSubCategoryFactory()
        expected = f"{design_subcat.sub_category.name} - Design Criteria"
        assert str(design_subcat) == expected


class TestDesignGroupModel:
    """Test cases for DesignGroup model."""

    def test_design_group_creation(self):
        """Test creating a design group."""
        design_group = DesignGroupFactory()
        assert design_group.id is not None
        assert design_group.work_package is not None
        assert design_group.group is not None

    def test_design_group_str_representation(self):
        """Test string representation of design group."""
        design_group = DesignGroupFactory()
        expected = f"{design_group.group.name} - Design Criteria"
        assert str(design_group) == expected


class TestDesignDisciplineModel:
    """Test cases for DesignDiscipline model."""

    def test_design_discipline_creation(self):
        """Test creating a design discipline."""
        design_discipline = DesignDisciplineFactory()
        assert design_discipline.id is not None
        assert design_discipline.work_package is not None
        assert design_discipline.discipline is not None

    def test_design_discipline_str_representation(self):
        """Test string representation of design discipline."""
        design_discipline = DesignDisciplineFactory()
        expected = f"{design_discipline.discipline.name} - Design Criteria"
        assert str(design_discipline) == expected
