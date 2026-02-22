from django import forms

from app.BillOfQuantities.models.contract_models import (
    CorrespondenceDialog,
    CorrespondenceDialogFile,
)
from app.core.Utilities.forms import MultipleFileField


class CorrespondenceDialogForm(forms.ModelForm):
    attachments = MultipleFileField(required=False)

    class Meta:
        model = CorrespondenceDialog
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
                    CorrespondenceDialogFile.objects.create(dialog=instance, file=file)
        return instance
