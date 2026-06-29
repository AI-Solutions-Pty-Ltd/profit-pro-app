"""Forms for Category, SubCategory, and Discipline models."""

from typing import cast

from django import forms

from app.Project.projects.projects_models import (
    Category,
    Discipline,
    DrawingType,
    Group,
    SubCategory,
)


class CategoryForm(forms.ModelForm):
    """Form for creating and updating categories."""

    class Meta:
        model = Category
        fields = ["name", "description", "start_date", "end_date"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter category name (e.g., Construction, Engineering)",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Optional description of this category",
                    "rows": 3,
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
        }
        labels = {
            "name": "Name",
            "description": "Description (Optional)",
            "start_date": "Start Date",
            "end_date": "End Date",
        }


class SubCategoryForm(forms.ModelForm):
    """Form for creating and updating subcategories."""

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        if not project:
            raise ValueError("Project is required")
        category_field = cast(forms.ModelChoiceField, self.fields["category"])
        category_field.queryset = Category.objects.filter(
            project=project, deleted=False
        )
        category_field.widget = category_field.hidden_widget()

    class Meta:
        model = SubCategory
        fields = ["category", "name", "description", "start_date", "end_date"]
        widgets = {
            "category": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter subcategory name (e.g., Top Structures, Drawings)",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Optional description of this subcategory",
                    "rows": 3,
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
        }
        labels = {
            "category": "Category",
            "name": "Subcategory Name",
            "description": "Description (Optional)",
            "start_date": "Start Date",
            "end_date": "End Date",
        }


class GroupForm(forms.ModelForm):
    """Form for creating and updating groups."""

    def __init__(self, *args, **kwargs):
        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        if not project:
            raise ValueError("Project is required")
        subcategory_field = cast(forms.ModelChoiceField, self.fields["sub_category"])
        subcategory_field.queryset = SubCategory.objects.filter(
            project=project, deleted=False
        )
        subcategory_field.widget = subcategory_field.hidden_widget()

    class Meta:
        model = Group
        fields = [
            "name",
            "description",
            "sub_category",
            "start_date",
            "end_date",
        ]
        widgets = {
            "sub_category": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter group name (e.g., Top Structures, Drawings)",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Optional description of this group",
                    "rows": 3,
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
        }
        labels = {
            "sub_category": "Sub Category",
            "name": "Group Name",
            "description": "Description (Optional)",
            "start_date": "Start Date",
            "end_date": "End Date",
        }


class DisciplineForm(forms.ModelForm):
    """Form for creating and updating disciplines."""

    class Meta:
        model = Discipline
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter discipline name (e.g., Civil, Electrical, Mechanical)",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Optional description of this discipline",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "name": "Discipline Name",
            "description": "Description (Optional)",
        }


class DrawingTypeForm(forms.ModelForm):
    """Form for creating and updating project drawing types."""

    class Meta:
        model = DrawingType
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter drawing type (e.g., Tender, Construction)",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Optional description of this drawing type",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "name": "Drawing Type Name",
            "description": "Description (Optional)",
        }


class CategoryScopeDateForm(forms.ModelForm):
    """Scope-planning-only form: edit start/end dates for a category."""

    class Meta:
        model = Category
        fields = ["start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
        }
        labels = {
            "start_date": "Start Date",
            "end_date": "End Date",
        }


class SubCategoryScopeDateForm(forms.ModelForm):
    """Scope-planning-only form: edit start/end dates for a subcategory."""

    class Meta:
        model = SubCategory
        fields = ["start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
        }
        labels = {
            "start_date": "Start Date",
            "end_date": "End Date",
        }


class GroupScopeDateForm(forms.ModelForm):
    """Scope-planning-only form: edit start/end dates for a group."""

    class Meta:
        model = Group
        fields = ["start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
        }
        labels = {
            "start_date": "Start Date",
            "end_date": "End Date",
        }
