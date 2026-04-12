from django import forms

from ..models.unit_models import UnitOfMeasure


class UnitOfMeasureForm(forms.ModelForm):
    """Form for creating and updating Units of Measure."""

    class Meta:
        model = UnitOfMeasure
        fields = [
            "name",
            "short_name",
            "category",
            "conversion_factor",
            "reference_unit",
        ]
        widgets = {
            "category": forms.Select(
                attrs={
                    "class": "form-select block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                }
            ),
            "reference_unit": forms.Select(
                attrs={
                    "class": "form-select block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure only units of the same category can be selected as reference
        if self.instance and self.instance.pk:
            self.fields["reference_unit"].queryset = UnitOfMeasure.objects.exclude(  # type: ignore
                pk=self.instance.pk
            )
