"""Forms for Bill of Quantities app."""

from datetime import date
from typing import Any

from django import forms
from django.core.exceptions import ValidationError

from app.BillOfQuantities.models import (
    Bill,
    Claim,
    LineItem,
    Package,
    PaymentCertificate,
    PaymentCertificatePhoto,
    PaymentCertificateWorking,
    Structure,
)
from app.Project.models import Project


class MonthDateField(forms.DateField):
    """A DateField that accepts month input in YYYY-MM format."""

    def to_python(self, value):
        """Convert YYYY-MM string to date object."""
        if value in self.empty_values:
            return None

        if isinstance(value, date):
            return value

        # Handle month input from type="month" widget
        if isinstance(value, str) and len(value) == 7:  # Format: "YYYY-MM"
            try:
                year, month = map(int, value.split("-"))
                return date(year, month, 1)
            except ValueError as err:
                raise ValidationError("Enter a valid date.") from err

        # Let parent handle full date format
        return super().to_python(value)

    def prepare_value(self, value):
        """Convert date object to YYYY-MM format for widget."""
        if isinstance(value, date):
            return value.strftime("%Y-%m")
        return value


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

    def clean(self) -> dict[str, Any] | None:
        cleaned_data = super().clean()
        if not cleaned_data:
            return cleaned_data
        unit_measurement = cleaned_data.get("unit_measurement")
        budgeted_quantity = cleaned_data.get("budgeted_quantity", 0)
        if unit_measurement == "%" and budgeted_quantity and budgeted_quantity > 100:
            raise forms.ValidationError(
                {
                    "unit_measurement": "Percentage unit measurement must be less than or equal to 100.",
                    "budgeted_quantity": "Budgeted quantity must be less than or equal to 100 for percentage unit measurement.",
                }
            )
        return cleaned_data

    def save(self, row_index=None, commit=True):  # type: ignore
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


class PaymentCertificateFinalApprovalForm(forms.ModelForm):
    """Form for final approval or rejection of payment certificates."""

    class Meta:
        model = PaymentCertificate
        fields = ["approved_on", "assessment_date", "status", "notes"]
        widgets = {
            "approved_on": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "block w-fit border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
                }
            ),
            "assessment_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "block w-fit border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
                }
            ),
            "status": forms.RadioSelect(
                attrs={
                    "class": "focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
                    "rows": 4,
                    "placeholder": "Add any notes or comments about this decision...",
                }
            ),
        }
        labels = {
            "status": "Decision",
            "notes": "Notes (Optional)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow APPROVED or REJECTED status choices
        self.fields["status"].choices = [  # type: ignore
            (PaymentCertificate.Status.APPROVED, "Approve Certificate"),
            (PaymentCertificate.Status.REJECTED, "Reject Certificate"),
        ]

    def clean_status(self):
        status = self.cleaned_data.get("status")
        if status not in [
            PaymentCertificate.Status.APPROVED,
            PaymentCertificate.Status.REJECTED,
        ]:
            raise forms.ValidationError("Please select either Approve or Reject.")
        return status


class PaymentCertificatePhotoForm(forms.ModelForm):
    """Form for uploading photos to a payment certificate."""

    class Meta:
        model = PaymentCertificatePhoto
        fields = ["title", "image"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter photo title or description",
                }
            ),
            "image": forms.FileInput(
                attrs={
                    "class": "mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100",
                    "accept": "image/*",
                }
            ),
        }
        labels = {
            "title": "Photo Title",
            "image": "Photo File",
        }

    def __init__(self, *args, **kwargs):
        self.payment_certificate = kwargs.pop("payment_certificate", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True, uploaded_by=None):
        instance = super().save(commit=False)
        instance.payment_certificate = self.payment_certificate
        if uploaded_by:
            instance.uploaded_by = uploaded_by
        if commit:
            instance.save()
        return instance


class PaymentCertificateWorkingForm(forms.ModelForm):
    """Form for uploading working documents to a payment certificate."""

    class Meta:
        model = PaymentCertificateWorking
        fields = ["title", "file"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter document title or description",
                }
            ),
            "file": forms.FileInput(
                attrs={
                    "class": "mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100",
                }
            ),
        }
        labels = {
            "title": "Document Title",
            "file": "Document File",
        }

    def __init__(self, *args, **kwargs):
        self.payment_certificate = kwargs.pop("payment_certificate", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True, uploaded_by=None):
        instance = super().save(commit=False)
        instance.payment_certificate = self.payment_certificate
        if uploaded_by:
            instance.uploaded_by = uploaded_by
        if commit:
            instance.save()
        return instance


class ClaimForm(forms.ModelForm):
    """Form for creating and updating claims."""

    period = MonthDateField(widget=forms.DateInput(attrs={"type": "month"}))

    class Meta:
        model = Claim
        fields = ["period", "estimated_claim", "notes"]
        widgets = {
            "estimated_claim": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with project instance."""
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        # Set project on instance if it exists
        if self.project and hasattr(self, "instance"):
            self.instance.project = self.project

        # Set min and max dates based on project dates
        if self.project:
            self.fields["period"].widget.attrs.update(
                {
                    "min": self.project.start_date.strftime("%Y-%m"),
                    "max": self.project.end_date.strftime("%Y-%m"),
                }
            )

    def clean_period(self):
        """Validate period is within project dates."""
        period = self.cleaned_data["period"]

        if self.project and period:
            if period < self.project.start_date:
                raise ValidationError(
                    f"Period cannot be before project start date ({self.project.start_date})"
                )
            if period > self.project.end_date:
                raise ValidationError(
                    f"Period cannot be after project end date ({self.project.end_date})"
                )
        return period

    def clean_estimated_claim(self):
        """Validate estimated claim is positive."""
        estimated_claim = self.cleaned_data["estimated_claim"]
        if estimated_claim <= 0:
            raise ValidationError("Estimated claim must be greater than 0.")
        return estimated_claim

    def clean(self):
        """Validate claim doesn't already exist for this period."""
        cleaned_data = super().clean()
        if not cleaned_data:
            return cleaned_data
        period = cleaned_data.get("period")

        if self.project and period:
            # Check if claim already exists for this period
            existing_claim = Claim.objects.filter(
                project=self.project, period=period
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing_claim.exists():
                raise ValidationError(
                    {"period": "Claim for this project and period already exists"}
                )

        return cleaned_data
