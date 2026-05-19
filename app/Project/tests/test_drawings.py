"""Tests for Drawing model."""

import pytest

from app.Project.tests.factories import (
    CategoryFactory,
    DisciplineFactory,
    DrawingFactory,
    ProjectFactory,
    SubCategoryFactory,
)


@pytest.mark.django_db
class TestDrawingModel:
    """Test cases for Drawing model."""

    def test_drawing_creation(self):
        """Test creating a drawing with valid data."""
        project = ProjectFactory()
        discipline = DisciplineFactory(project=project)
        drawing = DrawingFactory(
            project=project,
            drawing_number="ARC-001",
            name="Ground Floor Plan",
            revision_number="A",
            discipline=discipline,
        )

        assert drawing.id is not None
        assert drawing.drawing_number == "ARC-001"
        assert drawing.name == "Ground Floor Plan"
        assert str(drawing) == "ARC-001: Ground Floor Plan (Rev A)"
        assert drawing.level == 0

    def test_drawing_hierarchy(self):
        """Test drawing nested hierarchy."""
        parent = DrawingFactory(drawing_number="P-001", name="Parent Drawing")
        child = DrawingFactory(
            drawing_number="C-001", name="Child Drawing", parent=parent
        )
        grandchild = DrawingFactory(
            drawing_number="GC-001", name="Grandchild Drawing", parent=child
        )

        assert child.parent == parent
        assert grandchild.parent == child
        assert parent.children.count() == 1
        assert child.children.count() == 1

        assert parent.level == 0
        assert child.level == 1
        assert grandchild.level == 2

    def test_drawing_wbs_links(self):
        """Test linking drawing to WBS levels."""
        category = CategoryFactory()
        sub_category = SubCategoryFactory(category=category)

        drawing = DrawingFactory(category=category, sub_category=sub_category)

        assert drawing.category == category
        assert drawing.sub_category == sub_category

    def test_drawing_file_upload_path(self):
        """Test the upload path for drawing files."""
        project = ProjectFactory(pk=123)
        discipline = DisciplineFactory(name="Architecture")
        drawing = DrawingFactory(
            project=project, discipline=discipline, drawing_number="D-001"
        )

        path = drawing.upload_to("test.pdf")
        assert "project_drawings/123/" in path
        assert "Architecture" in path
