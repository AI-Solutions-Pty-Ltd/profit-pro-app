from django import forms
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
            "gross",
            "vat",
            "vat_amount",
            "net",
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
            "gross": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            ),
            "vat_amount": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm bg-gray-100",
                    "readonly": "readonly",
                    "placeholder": "0.00",
                    "step": "0.01",
                }
            ),
            "net": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm bg-gray-100",
                    "readonly": "readonly",
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
            "gross": "Gross (R)",
            "vat": "Include VAT (15%)",
            "vat_amount": "VAT Amount (R)",
            "net": "Net (R)",
        }

    def __init__(self, *args, **kwargs):
        self.bill = kwargs.pop("bill", None)
        super().__init__(*args, **kwargs)


class BaseCostFormSet(formset_factory(CostForm, extra=1, can_delete=True)):
    def __init__(self, *args, **kwargs):
        self.bill = kwargs.pop('bill', None)
        super().__init__(*args, **kwargs)
        
    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['bill'] = self.bill
        return kwargs

CostFormSet = BaseCostFormSet
