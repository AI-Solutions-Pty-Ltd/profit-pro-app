"""Forms for Category, SubCategory, and Discipline models."""

from typing import cast

from django import forms

from app.Project.projects.projects_models import (
    Category,
    Discipline,
    Group,
    SubCategory,
)


class CategoryForm(forms.ModelForm):
    """Form for creating and updating categories."""

    class Meta:
        model = Category
        fields = ["name", "description"]
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
        }
        labels = {
            "name": "Category Name",
            "description": "Description (Optional)",
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
        fields = ["category", "name", "description"]
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
        }
        labels = {
            "category": "Category",
            "name": "Subcategory Name",
            "description": "Description (Optional)",
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
        }
        labels = {
            "sub_category": "Sub Category",
            "name": "Group Name",
            "description": "Description (Optional)",
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
