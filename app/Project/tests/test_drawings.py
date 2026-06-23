"""Tests for Drawing model and DrawingForm."""

import pytest

from app.Project.tests.factories import (
    CategoryFactory,
    DisciplineFactory,
    DrawingFactory,
    DrawingTypeFactory,
    GroupFactory,
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

    def test_drawing_wbs_links(self):
        """Test linking drawing to WBS levels."""
        category = CategoryFactory()
        sub_category = SubCategoryFactory(category=category)
        group = GroupFactory(sub_category=sub_category)

        drawing_cat = DrawingFactory(category=category)
        drawing_sub = DrawingFactory(sub_category=sub_category)
        drawing_grp = DrawingFactory(group=group)

        assert drawing_cat.category == category
        assert drawing_sub.sub_category == sub_category
        assert drawing_grp.group == group

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


@pytest.mark.django_db
class TestDrawingForm:
    """Test cases for DrawingForm integration with project WBS levels."""

    def test_drawing_form_wbs_choices_and_save(self):
        """Test DrawingForm populates hierarchical choices and saves correctly with parent resolution."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from app.Project.documents.document_forms import DrawingForm

        project = ProjectFactory()
        category = CategoryFactory(project=project, name="Category L1")
        sub_category = SubCategoryFactory(
            category=category, project=project, name="Subcategory L2"
        )
        group = GroupFactory(
            sub_category=sub_category, project=project, name="Group L3"
        )
        discipline = DisciplineFactory(project=project, name="Mechanical")

        # Initialize form
        form = DrawingForm(project=project)
        choices = dict(form.fields["wbs_level"].choices)

        # Verify hierarchical choices exist and are structured correctly
        assert f"category_{category.pk}" in choices
        assert choices[f"category_{category.pk}"] == "L1: Category L1"
        assert f"subcategory_{sub_category.pk}" in choices
        assert choices[f"subcategory_{sub_category.pk}"] == "  L2: Subcategory L2"
        assert f"group_{group.pk}" in choices
        assert choices[f"group_{group.pk}"] == "    L3: Group L3"

        # Verify category field is present
        assert "category" in form.fields
        category_choices = [c[0] for c in form.fields["category"].choices]
        assert category.pk in category_choices

        # Verify discipline choices are filtered
        discipline_queryset = form.fields["discipline"].queryset
        assert discipline in discipline_queryset

        # Test validation and saving with group selected (resolves parent category and subcategory)
        test_file = SimpleUploadedFile(
            "test.pdf", b"file_content", content_type="application/pdf"
        )
        form_data = {
            "drawing_number": "M-101",
            "name": "HVAC Layout",
            "revision_number": "01",
            "discipline": discipline.pk,
            "wbs_level": f"group_{group.pk}",
            "notes": "Testing form save",
        }
        form = DrawingForm(data=form_data, files={"file": test_file}, project=project)
        assert form.is_valid(), form.errors
        drawing = form.save()

        assert drawing.group == group
        assert drawing.sub_category == sub_category
        assert drawing.category == category
        assert drawing.discipline == discipline

    def test_drawing_form_explicit_category_save(self):
        """Test that selecting category explicitly works when wbs_level is empty."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from app.Project.documents.document_forms import DrawingForm

        project = ProjectFactory()
        category = CategoryFactory(project=project, name="Category L1")
        discipline = DisciplineFactory(project=project, name="Electrical")

        test_file = SimpleUploadedFile(
            "test.pdf", b"file_content", content_type="application/pdf"
        )
        form_data = {
            "drawing_number": "E-101",
            "name": "Power Layout",
            "revision_number": "01",
            "discipline": discipline.pk,
            "category": category.pk,
            "wbs_level": "",
            "notes": "Testing explicit category save",
        }
        form = DrawingForm(data=form_data, files={"file": test_file}, project=project)
        assert form.is_valid(), form.errors
        drawing = form.save()

        assert drawing.category == category
        assert drawing.sub_category is None
        assert drawing.group is None
        assert drawing.discipline == discipline

    def test_drawing_form_edit_initial_value(self):
        """Test that the form correctly pre-selects the WBS level when editing."""
        from app.Project.documents.document_forms import DrawingForm

        project = ProjectFactory()
        category = CategoryFactory(project=project)
        sub_category = SubCategoryFactory(category=category, project=project)
        group = GroupFactory(sub_category=sub_category, project=project)

        drawing = DrawingFactory(project=project, group=group)
        form = DrawingForm(instance=drawing, project=project)
        assert form.initial["wbs_level"] == f"group_{group.pk}"

        drawing2 = DrawingFactory(
            project=project, sub_category=sub_category, group=None
        )
        form2 = DrawingForm(instance=drawing2, project=project)
        assert form2.initial["wbs_level"] == f"subcategory_{sub_category.pk}"


@pytest.mark.django_db
class TestDrawingTypeModel:
    """Test cases for DrawingType model."""

    def test_drawing_type_creation(self):
        """Test creating a drawing type."""
        dt = DrawingTypeFactory(name="Tender")
        assert dt.id is not None
        assert dt.name == "Tender"
        assert str(dt) == "Tender"

    def test_drawing_type_is_project_scoped(self):
        """Test drawing types are scoped to a project."""
        project = ProjectFactory()
        dt = DrawingTypeFactory(project=project, name="Construction")
        assert dt.project == project

    def test_drawing_type_unique_per_project(self):
        """Test drawing type names must be unique within a project."""
        from django.db import IntegrityError, transaction

        from app.Project.projects.projects_models import DrawingType

        project = ProjectFactory()
        # "Unique Type" is not in the defaults, so it will only exist once
        DrawingType.objects.create(project=project, name="Unique Type")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                DrawingType.objects.create(project=project, name="Unique Type")

    def test_drawing_type_str(self):
        """Test __str__ returns name."""
        dt = DrawingTypeFactory(name="Shop")
        assert str(dt) == "Shop"


@pytest.mark.django_db
class TestDrawingFormWithDrawingType:
    """Test DrawingForm uses a select for drawing_type."""

    def test_drawing_form_drawing_type_is_model_choice_field(self):
        """Test that drawing_type field is a ModelChoiceField (select)."""
        from django.forms import ModelChoiceField

        from app.Project.documents.document_forms import DrawingForm

        project = ProjectFactory()
        form = DrawingForm(project=project)
        assert isinstance(form.fields["drawing_type"], ModelChoiceField)

    def test_drawing_form_drawing_type_filtered_by_project(self):
        """Test that drawing_type choices are filtered by project."""
        from app.Project.documents.document_forms import DrawingForm

        project = ProjectFactory()
        other_project = ProjectFactory()
        dt_mine = DrawingTypeFactory(project=project, name="Tender")
        dt_other = DrawingTypeFactory(project=other_project, name="Tender")
        form = DrawingForm(project=project)
        qs = form.fields["drawing_type"].queryset
        assert dt_mine in qs
        assert dt_other not in qs

    def test_new_project_gets_default_drawing_types(self):
        """Test that default drawing types are created when a project is created."""
        from app.Project.projects.projects_models import DrawingType

        project = ProjectFactory()
        type_names = list(
            DrawingType.objects.filter(project=project, deleted=False)
            .values_list("name", flat=True)
            .order_by("name")
        )
        assert "Construction" in type_names
        assert "Information" in type_names
        assert "Shop" in type_names
        assert "Tender" in type_names

    def test_new_project_gets_default_disciplines(self):
        """Test that default disciplines are created when a project is created."""
        from app.Project.projects.projects_models import Discipline

        project = ProjectFactory()
        discipline_names = list(
            Discipline.objects.filter(project=project, deleted=False)
            .values_list("name", flat=True)
            .order_by("name")
        )
        defaults = [
            "Project management",
            "Quantity Surveying",
            "Structural",
            "Electrical",
            "Mechanical",
            "Civil",
            "Piping",
            "Control & Instrumentation",
            "Geotech",
            "Town Planning",
            "Health and Safety",
            "Land Surveying",
            "Architectural",
        ]
        for name in defaults:
            assert name in discipline_names

    def test_discipline_uniqueness_per_project(self):
        """Test discipline names must be unique within a project."""
        from django.db import IntegrityError, transaction

        from app.Project.projects.projects_models import Discipline

        project = ProjectFactory()
        # "Unique Disc" is not in default disciplines list
        Discipline.objects.create(project=project, name="Unique Disc")
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Discipline.objects.create(project=project, name="Unique Disc")
