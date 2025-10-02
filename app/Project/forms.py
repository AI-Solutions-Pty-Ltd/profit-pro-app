"""Forms for Project app."""

from django import forms

from app.Project.models import Project


class ProjectForm(forms.ModelForm):
    """Form for creating and updating projects."""

    class Meta:
        model = Project
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter project name",
                }
            ),
        }
        labels = {
            "name": "Project Name",
        }
