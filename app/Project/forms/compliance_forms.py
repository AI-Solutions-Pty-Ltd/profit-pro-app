"""Forms for compliance dialogs."""

from django import forms

from app.core.Utilities.forms import MultipleFileField
from app.Project.models.compliance_models import (
    AdministrativeComplianceDialog,
    AdministrativeComplianceDialogFile,
    ContractualComplianceDialog,
    ContractualComplianceDialogFile,
    FinalAccountComplianceDialog,
    FinalAccountComplianceDialogFile,
)


class ContractualComplianceDialogForm(forms.ModelForm):
    """Form for contractual compliance dialog."""

    attachments = MultipleFileField(required=False)

    class Meta:
        model = ContractualComplianceDialog
        fields = ["message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].widget = forms.Textarea(
            attrs={
                "rows": 4,
                "class": "shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md",
                "placeholder": "Enter your message here...",
            }
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Handle multiple file attachments
            attachments = self.cleaned_data.get("attachments", [])
            for file in attachments:
                if file:  # Ensure file is not empty
                    ContractualComplianceDialogFile.objects.create(
                        dialog=instance, file=file
                    )
        return instance


class AdministrativeComplianceDialogForm(forms.ModelForm):
    """Form for administrative compliance dialog."""

    attachments = MultipleFileField(required=False)

    class Meta:
        model = AdministrativeComplianceDialog
        fields = ["message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].widget = forms.Textarea(
            attrs={
                "rows": 4,
                "class": "shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md",
                "placeholder": "Enter your message here...",
            }
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Handle multiple file attachments
            attachments = self.cleaned_data.get("attachments", [])
            for file in attachments:
                if file:  # Ensure file is not empty
                    AdministrativeComplianceDialogFile.objects.create(
                        dialog=instance, file=file
                    )
        return instance


class FinalAccountComplianceDialogForm(forms.ModelForm):
    """Form for final account compliance dialog."""

    attachments = MultipleFileField(required=False)

    class Meta:
        model = FinalAccountComplianceDialog
        fields = ["message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["message"].widget = forms.Textarea(
            attrs={
                "rows": 4,
                "class": "shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md",
                "placeholder": "Enter your message here...",
            }
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Handle multiple file attachments
            attachments = self.cleaned_data.get("attachments", [])
            for file in attachments:
                if file:  # Ensure file is not empty
                    FinalAccountComplianceDialogFile.objects.create(
                        dialog=instance, file=file
                    )
        return instance
