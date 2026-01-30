from django import forms
from django.conf import settings
from django.forms import formset_factory

from .models import Cost


class CostForm(forms.ModelForm):
    """Form for creating and updating costs."""

    class Meta:
        model = Cost
        fields = [
            "date",
            "category",
            "description",
            "quantity",
            "unit_price",
        ]
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter cost description",
                }
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            ),
            "unit_price": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            ),
        }
        labels = {
            "date": "Date",
            "category": "Category",
            "description": "Description",
            "quantity": "Quantity",
            "unit_price": "Unit Price",
        }

    def __init__(self, *args, **kwargs):
        self.bill = kwargs.pop("bill", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """Override save to calculate VAT and net amounts."""
        instance = super().save(commit=False)

        # Calculate gross amount
        instance.gross = instance.quantity * instance.unit_price

        # Check if project has VAT enabled
        if hasattr(instance, "bill") and instance.bill:
            if instance.bill.structure.project.vat:
                # Calculate VAT (15%)
                instance.vat_amount = instance.gross * settings.VAT_RATE
                instance.vat = True
            else:
                instance.vat_amount = 0
                instance.vat = False
        else:
            # Bill not set yet, let the model handle VAT calculation
            pass

        # Calculate net amount if VAT amount is set
        if hasattr(instance, "vat_amount") and instance.vat_amount is not None:
            instance.net = instance.gross + instance.vat_amount

        if commit:
            instance.save()

        return instance


class BaseCostFormSet(formset_factory(CostForm, extra=1, can_delete=True)):  # type: ignore
    def __init__(self, *args, **kwargs):
        self.bill = kwargs.pop("bill", None)
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["bill"] = self.bill
        return kwargs


CostFormSet = BaseCostFormSet
