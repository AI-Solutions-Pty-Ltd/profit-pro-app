"""Tests for Structure models."""

import pytest
from django.db import IntegrityError

from app.BillOfQuantities.models import Structure
from app.BillOfQuantities.tests.factories import StructureFactory
from app.Project.tests.factories import ProjectFactory


class TestStructureModel:
    """Test cases for Structure model."""

    def test_structure_creation(self):
        """Test creating a structure with valid data."""
        structure = StructureFactory.create(name="Test Building")
        assert structure.id is not None
        assert structure.name == "Test Building"
        assert structure.project is not None

    def test_structure_string_representation(self):
        """Test the __str__ method returns correct format."""
        project = ProjectFactory(name="Test Project")
        structure = StructureFactory(name="Main Building", project=project)
        expected = "Main Building (Test Project)"
        assert str(structure) == expected

    def test_structures_with_empty_description(self):
        """Test creating a structure with empty description."""
        structure = StructureFactory(description="")
        assert structure.description == ""

    def test_structures_with_long_name(self):
        """Test creating a structure with maximum length name."""
        long_name = "A" * 255
        structure = StructureFactory.create(name=long_name)
        assert structure.name == long_name
        assert len(structure.name) == 255

    def test_structures_project_relationship(self):
        """Test the relationship between Structure and Project."""
        project = ProjectFactory.create()
        structure = StructureFactory.create(project=project)

        assert structure.project == project
        assert project.structures.count() == 1
        assert project.structures.first() == structure

    def test_structures_ordering(self):
        """Test structures are ordered by name."""
        project = ProjectFactory.create()
        structure_c = StructureFactory.create(name="Zebra Building", project=project)
        structure_a = StructureFactory.create(name="Alpha Building", project=project)
        structure_b = StructureFactory.create(name="Beta Building", project=project)

        structures = Structure.objects.filter(project=project)
        assert list(structures) == [structure_a, structure_b, structure_c]

    def test_structures_soft_delete(self):
        """Test soft delete functionality."""
        structure = StructureFactory.create()
        _structure2 = StructureFactory.create()

        structure.soft_delete()

        assert Structure.objects.all().count() == 1

    def test_structures_restore(self):
        """Test restore functionality after soft delete."""
        structure = StructureFactory.create()
        structure_id = structure.pk

        structure.soft_delete()
        structure.restore()

        assert Structure.objects.filter(id=structure_id).count() == 1

    def test_structures_timestamps(self):
        """Test created_at and updated_at are set correctly."""
        structure = StructureFactory.create()
        assert structure.created_at is not None
        assert structure.updated_at is not None
        assert structure.created_at <= structure.updated_at

    def test_structures_project_cascade_delete(self):
        """Test that structures are deleted when project is deleted."""
        project = ProjectFactory.create()
        structure = StructureFactory.create(project=project)
        structure_id = structure.pk

        project.delete()

        assert Structure.objects.filter(id=structure_id).count() == 0

    def test_structures_required_fields(self):
        """Test required fields for structure creation."""
        project = ProjectFactory.create()

        # Should create successfully with required fields
        structure = Structure.objects.create(project=project, name="Test Structure")
        assert structure.id is not None

    def test_structures_missing_project_raises_error(self):
        """Test that missing project raises IntegrityError."""
        with pytest.raises(IntegrityError):
            Structure.objects.create(name="No Project Structure")

    def test_structures_missing_name_raises_error(self):
        """Test that missing name raises IntegrityError."""
        project = ProjectFactory()
        with pytest.raises(IntegrityError):
            Structure.objects.create(project=project, name=None)

    def test_structures_verbose_names(self):
        """Test verbose name settings in Meta class."""
        assert Structure._meta.verbose_name == "Structure"
        assert Structure._meta.verbose_name_plural == "Structures"

    def test_structures_url_methods(self):
        """Test URL generation methods."""
        project = ProjectFactory.create()
        structure = StructureFactory.create(project=project)

        expected_detail = f"/bill-of-quantities/project/{structure.pk}/"
        expected_update = f"/bill-of-quantities/project/{structure.pk}/update/"
        expected_delete = f"/bill-of-quantities/project/{structure.pk}/delete/"

        assert structure.get_absolute_url() == expected_detail
        assert structure.get_update_url() == expected_update
        assert structure.get_delete_url() == expected_delete

    def test_multiple_structures_per_project(self):
        """Test creating multiple structures for the same project."""
        project = ProjectFactory.create()

        structure1 = StructureFactory.create(project=project, name="Building A")
        structure2 = StructureFactory.create(project=project, name="Building B")
        structure3 = StructureFactory.create(project=project, name="Building C")

        assert project.structures.count() == 3
        assert all(s.project == project for s in [structure1, structure2, structure3])

    def test_structures_description_length(self):
        """Test that description can handle long text."""
        long_description = "This is a very long description. " * 50
        structure = StructureFactory.create(description=long_description)

        assert len(structure.description) == len(long_description)
        assert structure.description == long_description
