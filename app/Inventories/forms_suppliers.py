from datetime import datetime

from django import forms
from django.forms import modelformset_factory

from .models_suppliers import Invoice, Supplier, Transaction


class DateInput(forms.DateInput):
    input_type = "date"


class SupplierCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].required = True
        self.fields["company_registration"].required = True
        self.fields["vat"].required = True
        self.fields["vat_number"].required = True
        self.fields["primary_contact"].required = True
        self.fields["email"].required = True
        self.fields["address"].required = True
        self.fields["active"].required = True
        self.fields["gender"].required = True
        self.fields["location"].required = True

    class Meta:
        model = Supplier

        fields = "__all__"


class InvoiceTransactionCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].required = True
        self.fields["category"].required = True
        self.fields["description"].required = True
        self.fields["amount_incl"].required = True
        self.fields["date"].initial = datetime.now()

    class Meta:
        model = Transaction
        widgets = {
            "date": DateInput(),
        }
        fields = (
            "date",
            "description",
            "category",
            "amount_incl",
        )


InvoiceTransactionCreateFormSet = modelformset_factory(
    Transaction, form=InvoiceTransactionCreateForm, extra=0
)


class SupplierInvoiceUploadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["invoice"].required = True

    class Meta:
        model = Invoice
        fields = [
            "invoice",
        ]
