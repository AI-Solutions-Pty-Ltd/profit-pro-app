"""Forms for Structure app."""

from django import forms

from app.BillOfQuantities.models import Bill, LineItem, Package, Structure
from app.Project.models import Project


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


class LineItemExcelUploadForm(forms.ModelForm):
    """Form for uploading line items via Excel file."""

    project = forms.ModelChoiceField(queryset=Project.objects.all())
    structure = forms.CharField()
    bill = forms.CharField()
    package = forms.CharField(required=False)

    class Meta:
        model = LineItem
        fields = [
            # "project",
            # "structure",
            # "bill",
            # "package",
            "row_index",
            "item_number",
            "payment_reference",
            "description",
            "unit_measurement",
            "budgeted_quantity",
            "unit_price",
            "total_price",
        ]

    def clean_structure(self):
        if not self.cleaned_data["structure"]:
            raise forms.ValidationError("Structure is required.")
        return self.cleaned_data["structure"]

    def clean_bill(self):
        if not self.cleaned_data["bill"]:
            raise forms.ValidationError("Bill is required.")
        return self.cleaned_data["bill"]

    def clean(self):
        cleaned_data = super().clean()
        unit_measurement = cleaned_data.get("unit_measurement")
        budgeted_quantity = cleaned_data.get("budgeted_quantity")
        if unit_measurement == "%" and budgeted_quantity > 100:
            raise forms.ValidationError(
                {
                    "unit_measurement": "Percentage unit measurement must be less than or equal to 100.",
                    "budgeted_quantity": "Budgeted quantity must be less than or equal to 100 for percentage unit measurement.",
                }
            )
        return cleaned_data

    def save(self, row_index=None, commit=True):
        line_item = super().save(commit=False)
        project = self.cleaned_data["project"]
        structure, _ = Structure.objects.get_or_create(
            project=self.cleaned_data["project"], name=self.cleaned_data["structure"]
        )
        bill, _ = Bill.objects.get_or_create(
            structure=structure, name=self.cleaned_data["bill"]
        )
        if self.cleaned_data["package"]:
            package, _ = Package.objects.get_or_create(
                bill=bill, name=self.cleaned_data["package"]
            )
        else:
            package = None

        line_item.project = project
        line_item.structure = structure
        line_item.bill = bill
        line_item.package = package
        line_item.is_work = True if self.cleaned_data["total_price"] else False
        if commit:
            line_item.save()
        return line_item
