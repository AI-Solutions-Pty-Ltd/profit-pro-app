from django import forms

from ..models.plant_type import PlantType
from ..models.skill_type import SkillType


class SkillTypeForm(forms.ModelForm):
    """Form for creating or updating a SkillType."""

    class Meta:
        model = SkillType
        fields = ["name", "hourly_rate"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "e.g., Skilled Worker, General Labour",
                }
            ),
            "hourly_rate": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            ),
        }


class PlantTypeForm(forms.ModelForm):
    """Form for creating or updating a PlantType."""

    class Meta:
        model = PlantType
        fields = ["name", "hourly_rate"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "e.g., Excavator, Generator, 10-ton Truck",
                }
            ),
            "hourly_rate": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            ),
        }
