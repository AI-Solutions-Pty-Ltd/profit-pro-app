"""Forms for Category, SubCategory, and Discipline models."""

from django import forms

from app.Project.projects.projects_models import Category, Discipline, SubCategory


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

    class Meta:
        model = SubCategory
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
