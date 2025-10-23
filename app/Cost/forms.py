from decimal import Decimal

from django import forms

from .models import Cost


class CostForm(forms.ModelForm):
    """Form for creating and updating costs."""

    class Meta:
        model = Cost
        fields = ["date", "description", "amount", "vat"]
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter cost description",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            ),
            "vat": forms.CheckboxInput(
                attrs={
                    "class": "rounded border-gray-300 text-indigo-600 focus:ring-indigo-500",
                }
            ),
        }
        labels = {
            "date": "Date",
            "description": "Description",
            "amount": "Amount (R)",
            "vat": "Include VAT (15%)",
        }

    def __init__(self, *args, **kwargs):
        self.bill = kwargs.pop("bill", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Calculate total with VAT if applicable
        if instance.vat:
            instance.total = instance.amount * Decimal("1.15")
        else:
            instance.total = instance.amount

        if commit:
            instance.save()

        return instance
