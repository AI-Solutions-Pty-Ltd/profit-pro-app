"""Forms for Order Amendments."""

from django import forms

from app.Project.models import OrderAmendment


class OrderAmendmentForm(forms.ModelForm):
    """Form for creating and editing Order Amendments."""

    class Meta:
        """Meta options for OrderAmendmentForm."""

        model = OrderAmendment
        fields = [
            "amendment_number",
            "name",
            "category",
            "variation_amount",
            "date_approved",
            "description",
            "justification",
        ]
        widgets = {
            "amendment_number": forms.TextInput(
                attrs={
                    "class": "shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md",
                    "placeholder": "e.g., 1, 2, A",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md",
                    "placeholder": "e.g., Extension of Time",
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md",
                }
            ),
            "variation_amount": forms.NumberInput(
                attrs={
                    "class": "shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md",
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            ),
            "date_approved": forms.DateInput(
                attrs={
                    "class": "shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md",
                    "type": "date",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md",
                    "rows": 3,
                    "placeholder": "Detailed description of the amendment...",
                }
            ),
            "justification": forms.Textarea(
                attrs={
                    "class": "shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md",
                    "rows": 3,
                    "placeholder": "Justification for the amendment...",
                }
            ),
        }

    def __init__(self, *args, project=None, user=None, **kwargs):
        """Initialize form with project and user context."""
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user

    def save(self, commit=True):
        """Save the amendment with project and approved_by set."""
        instance = super().save(commit=False)

        if self.project:
            instance.project = self.project

        # Set status to approved if date_approved is provided
        if instance.date_approved:
            instance.status = OrderAmendment.Status.APPROVED
            if self.user:
                instance.approved_by = self.user
        else:
            instance.status = OrderAmendment.Status.PENDING

        if commit:
            instance.save()

        return instance
