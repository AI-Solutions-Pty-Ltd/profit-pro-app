from django import forms

from app.BillOfQuantities.models import PaymentCertificate


class PaymentCertificateApprovedDateForm(forms.ModelForm):
    """Form for editing only the approved_on date."""

    class Meta:
        model = PaymentCertificate
        fields = ["approved_on", "assessment_date"]
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
        }
        labels = {
            "approved_on": "Approval Date",
            "assessment_date": "Assessment Date",
        }
