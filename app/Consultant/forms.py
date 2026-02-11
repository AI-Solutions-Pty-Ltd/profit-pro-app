from django import forms

from app.BillOfQuantities.models import PaymentCertificate
from app.Project.models import Company


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


class ProjectClientForm(forms.Form):
    """Form to select a client for a project."""

    client = forms.ModelChoiceField(
        queryset=Company.objects.filter(type=Company.Type.CLIENT),
        widget=forms.Select(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
            }
        ),
        required=False,
        help_text="Select a client company to associate with this project.",
    )

    def __init__(self, *args, **kwargs):
        # Pop instance before calling super() to avoid passing it to Form
        self.instance = kwargs.pop("instance", None)
        super().__init__(*args, **kwargs)
        self.fields["client"].label = "Client Company"
