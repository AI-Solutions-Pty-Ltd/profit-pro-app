"""Forms for Project app."""

from django import forms

from app.Project.models import (
    ProjectCategory,
    ProjectDiscipline,
    ProjectSubCategory,
)


class ProjectCategoryForm(forms.ModelForm):
    """Form for creating and updating project categories."""

    class Meta:
        model = ProjectCategory
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter category name (e.g., Education, Health)",
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


class ProjectSubCategoryForm(forms.ModelForm):
    """Form for creating and updating project subcategories."""

    class Meta:
        model = ProjectSubCategory
        fields = ["name", "description"]
        widgets = {
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
            "name": "Subcategory Name",
            "description": "Description (Optional)",
        }


class ProjectDisciplineForm(forms.ModelForm):
    """Form for creating and updating project disciplines."""

    class Meta:
        model = ProjectDiscipline
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
