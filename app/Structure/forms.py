"""Forms for Structure app."""

from django import forms

from app.Structure.models import Structure


class StructureForm(forms.ModelForm):
    """Form for creating and updating structures."""

    class Meta:
        model = Structure
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter structure name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter structure description (optional)",
                    "rows": 3,
                }
            ),
        }
        labels = {
            "name": "Structure Name",
            "description": "Description",
        }


class StructureExcelUploadForm(forms.Form):
    """Form for uploading structures via Excel file."""

    excel_file = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "class": "mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100",
                "accept": ".xlsx,.xls",
            }
        ),
        label="Excel File",
        help_text="Upload an Excel file with columns: 'name' and 'description' (optional)",
    )

    def __init__(self, *args, **kwargs):
        # Remove unused kwargs
        kwargs.pop("user", None)
        kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
