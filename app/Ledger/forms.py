"""Forms for Ledger transactions."""

from __future__ import annotations

from decimal import Decimal
from typing import cast

from django import forms

from app.BillOfQuantities.models import Bill, Structure
from app.Ledger.models import Ledger, Transaction, Vat
from app.Project.models import Company, Project


class ProjectFilterForm(forms.Form):
    projects = None
    structure = None
    bill = None
    bill_search = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        company = self.initial.get("company")
        if not company:
            raise ValueError("Company is required for project filter form.")
        self.fields["project"] = forms.ModelChoiceField(
            queryset=Project.objects.filter(contractor=company),
            required=False,
            empty_label="Select project",
        )
        project = self.data.get("project")
        self.fields["project"].initial = project
        if project:
            structure = self.data.get("structure")
            self.fields["structure"] = forms.ModelChoiceField(
                queryset=Structure.objects.filter(project=project),
                required=False,
                empty_label="Select structure",
            )
            self.fields["structure"].initial = structure
            if structure:
                bill = self.data.get("bill")
                bill_search = self.data.get("bill_search")
                self.fields["bill_search"] = forms.CharField(
                    required=False,
                    widget=forms.TextInput(attrs={"placeholder": "Search bills..."}),
                )
                self.fields["bill_search"].initial = bill_search
                bills = Bill.objects.filter(structure=structure)
                if bill_search:
                    bills = bills.filter(name__icontains=bill_search)
                self.fields["bill"] = forms.ModelChoiceField(
                    queryset=bills,
                    required=False,
                    empty_label="Select bill",
                )
                self.fields["bill"].initial = bill

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data:
            return cleaned_data
        cleaned_data["company"] = self.initial.get("company")
        return cleaned_data


class SafeDateField(forms.DateField):
    """DateField that handles QueryDict list values safely."""

    def to_python(self, value):
        """Convert value to datetime, handling list values."""
        if value is None:
            return None

        # Handle QueryDict list values
        if isinstance(value, list):
            value = value[0] if value else None

        # Call parent method with cleaned value
        return super().to_python(value)


class SafeCharField(forms.CharField):
    """DateField that handles QueryDict list values safely."""

    def to_python(self, value):
        """Convert value to datetime, handling list values."""
        if value is None:
            return None

        # Handle QueryDict list values
        if isinstance(value, list):
            value = value[0] if value else None

        # Call parent method with cleaned value
        return super().to_python(value)


class SafeChoiceField(forms.ChoiceField):
    def to_python(self, value):
        """Convert value to datetime, handling list values."""
        if value is None:
            return None

        # Handle QueryDict list values
        if isinstance(value, list):
            value = value[0] if value else None

        # Call parent method with cleaned value
        return super().to_python(value)


class TransactionForm(forms.ModelForm):
    """Base form for shared create-transaction fields."""

    VAT_MODE_INCLUSIVE = "inclusive"
    VAT_MODE_EXCLUSIVE = "exclusive"
    VAT_MODE_CHOICES = (
        (VAT_MODE_INCLUSIVE, "VAT Inclusive"),
        (VAT_MODE_EXCLUSIVE, "VAT Exclusive"),
    )

    ledger = forms.ModelChoiceField(
        queryset=Ledger.objects.none(),
        required=True,
        empty_label="Select ledger",
    )
    date = SafeDateField(
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Total transaction amount.",
        required=True,
    )
    vat_rate = forms.ModelChoiceField(
        queryset=Vat.objects.all(),
        empty_label="Select VAT rate",
        required=False,
    )
    vat_mode = forms.ChoiceField(
        choices=VAT_MODE_CHOICES,
        initial=VAT_MODE_INCLUSIVE,
        required=False,
    )
    type = SafeChoiceField(
        choices=Transaction.TransactionType.choices,
        initial=Transaction.TransactionType.DEBIT,
        required=False,
    )

    company = forms.ModelChoiceField(
        queryset=Company.objects.all(), widget=forms.HiddenInput(), required=False
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(), widget=forms.HiddenInput(), required=False
    )
    structure = forms.ModelChoiceField(
        queryset=Structure.objects.all(), widget=forms.HiddenInput(), required=False
    )
    bill = forms.ModelChoiceField(
        queryset=Bill.objects.all(), widget=forms.HiddenInput(), required=False
    )

    class Meta:
        model = Transaction
        fields = [
            "company",
            "project",
            "structure",
            "bill",
            "ledger",
            "date",
            "type",
            "amount",
            "vat_rate",
            "vat_mode",
        ]

    def __init__(self, company, *args, **kwargs):
        """Initialize form with company-scoped choices."""
        super().__init__(*args, **kwargs)
        self.company = company
        self.project = self.data.get("project")

        if not self.company:
            raise ValueError("Company is required for transaction form.")

        # Filter ledger choices to company's ledgers
        ledger_field = cast(forms.ModelChoiceField, self.fields["ledger"])
        ledger_field.queryset = Ledger.objects.filter(company=self.company)

        # initial values
        # set amount field
        self.fields["amount"].initial = self.instance.amount_incl_vat

    def clean(self) -> dict:
        """Validation."""
        cleaned_data = super().clean()
        if cleaned_data is None:
            return {}

        if not self.company:
            raise ValueError("Company is required for transaction form.")

        project = cleaned_data.get("project")
        if project:
            structure = cleaned_data.get("structure")
            if not structure:
                raise forms.ValidationError({"structure": "Structure is required."})

            if structure not in project.structures.all():
                raise forms.ValidationError(
                    {"structure": "Structure is not valid for this project."}
                )
            bill = cleaned_data.get("bill")
            if not bill:
                raise forms.ValidationError({"bill": "Bill is required."})

            if bill not in structure.bills.all():
                raise forms.ValidationError(
                    {"bill": "Bill is not valid for this project."}
                )

        tx_date = cleaned_data.get("date")

        # Explicit type assertion for mypy - we know company is a Company instance
        company_instance = cast(Company, self.company)
        if company_instance.vat_registered:
            vat_rate = cleaned_data.get("vat_rate")
            vat_mode = cleaned_data.get("vat_mode")

            if not vat_rate:
                raise forms.ValidationError({"vat_rate": "VAT rate is required."})

            if not vat_mode:
                raise forms.ValidationError({"vat_mode": "VAT mode is required."})

            if vat_rate.start_date and tx_date < vat_rate.start_date:
                raise forms.ValidationError(
                    {
                        "vat_rate": f"VAT rate '{vat_rate.name}' is not valid before {vat_rate.start_date}. "
                        f"Select a VAT rate valid for {tx_date}."
                    }
                )
            if vat_rate.end_date and tx_date > vat_rate.end_date:
                raise forms.ValidationError(
                    {
                        "vat_rate": f"VAT rate '{vat_rate.name}' is not valid after {vat_rate.end_date}. "
                        f"Select a VAT rate valid for {tx_date}."
                    }
                )

        return cleaned_data

    def save(self, commit: bool = True) -> Transaction:
        """Save transaction with proper company assignment."""
        instance = super().save(commit=False)
        amount = self.cleaned_data.get("amount")
        if not instance.company.vat_registered:
            instance.vat = False
            instance.vat_rate = None
            instance.amount_excl_vat = amount
            instance.amount_incl_vat = amount
        else:
            instance.vat = True
            vat_rate: Vat = cast(Vat, self.cleaned_data.get("vat_rate"))
            vat_mode = self.cleaned_data.get("vat_mode")
            if vat_mode == self.VAT_MODE_INCLUSIVE:
                instance.amount_excl_vat = amount / (1 + vat_rate.rate / 100)
                instance.amount_incl_vat = amount
            else:
                instance.amount_excl_vat = amount
                instance.amount_incl_vat = amount * (1 + vat_rate.rate / 100)

        # finally save
        if commit:
            instance.save()

        return instance


class NonVatTransactionCreateUpdateForm(TransactionForm):
    """Transaction form for non-VAT registered companies."""


class VatTransactionCreateUpdateForm(TransactionForm):
    """Transaction form for VAT-registered companies."""

    vat_rate = forms.ModelChoiceField(
        queryset=Vat.objects.all(),
        required=True,
        empty_label="Select VAT rate",
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Enter either VAT-inclusive or VAT-exclusive amount.",
    )
    vat_mode = forms.ChoiceField(
        choices=TransactionForm.VAT_MODE_CHOICES,
        initial=TransactionForm.VAT_MODE_INCLUSIVE,
        required=True,
    )

    class Meta(TransactionForm.Meta):
        fields = ["ledger", "bill", "date", "vat_rate", "type", "amount", "vat_mode"]
