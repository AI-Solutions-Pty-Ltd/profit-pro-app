"""Forms for Ledger transactions."""

from __future__ import annotations

from decimal import Decimal
from typing import cast

from django import forms

from app.BillOfQuantities.models import Bill, Structure
from app.Ledger.models import Ledger, Transaction, Vat
from app.Project.models import Company


class BaseTransactionForm(forms.ModelForm):
    """Base form for shared create-transaction fields."""

    VAT_MODE_INCLUSIVE = "inclusive"
    VAT_MODE_EXCLUSIVE = "exclusive"
    VAT_MODE_CHOICES = (
        (VAT_MODE_INCLUSIVE, "VAT Inclusive"),
        (VAT_MODE_EXCLUSIVE, "VAT Exclusive"),
    )

    company = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.HiddenInput(),
        required=False,
    )

    ledger = forms.ModelChoiceField(
        queryset=Ledger.objects.none(),
        required=True,
        empty_label="Select ledger",
    )
    structure = forms.ModelChoiceField(
        queryset=Structure.objects.none(),
        required=False,
        empty_label="Select structure",
    )
    bill = forms.ModelChoiceField(
        queryset=Bill.objects.none(),
        required=False,
        empty_label="Select bill",
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Total transaction amount.",
    )
    vat_rate = forms.ModelChoiceField(
        queryset=Vat.objects.all(),
        required=False,
        empty_label="Select VAT rate",
    )
    vat_mode = forms.ChoiceField(
        choices=VAT_MODE_CHOICES,
        initial=VAT_MODE_INCLUSIVE,
        required=False,
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=True,
    )
    amount_excl_vat = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        required=False,
    )
    amount_incl_vat = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        required=False,
    )

    class Meta:
        model = Transaction
        fields = [
            "company",
            "ledger",
            "bill",
            "structure",
            "date",
            "type",
            "amount",
            "amount_excl_vat",
            "amount_incl_vat",
            "vat_rate",
            "vat_mode",
        ]

    def _get_single_value(self, key: str) -> str | None:
        """Safely get a single value from form data, handling QueryDict lists."""
        value = self.data.get(key)
        if value is None:
            return None
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def __init__(self, *args, **kwargs):
        """Initialize form with company-scoped choices."""
        self.company = kwargs.pop("company", None)
        super().__init__(*args, **kwargs)

        if not self.company:
            raise ValueError("Company is required for transaction form.")

        # Cast to Company type for mypy - we know company is not None at this point
        self.company = cast(Company, self.company)

        # Set company field queryset and initial value
        # company_form_field = cast(forms.ModelChoiceField, self.fields["company"])
        # company_form_field.queryset = Company.objects.filter(pk=self.company.pk)
        # company_form_field.initial = self.company

        # Filter ledger choices to company's ledgers
        ledger_field = cast(forms.ModelChoiceField, self.fields["ledger"])
        ledger_field.queryset = Ledger.objects.filter(company=self.company)

        # Filter structure choices to company's structures
        structure_field = cast(forms.ModelChoiceField, self.fields["structure"])
        structure_field.queryset = Structure.objects.filter(
            project__client=self.company
        )

        # Filter bill choices to company's bills
        bill_field = cast(forms.ModelChoiceField, self.fields["bill"])
        bill_field.queryset = (
            Bill.objects.filter(structure__project__client=self.company)
            .select_related("structure")
            .distinct()
        )
        bill_field.required = False

        self.fields["amount"].initial = self.instance.amount_incl_vat
        if self.instance.bill:
            self.fields["structure"].initial = self.instance.bill.structure
        elif self.data.get("bill"):
            # Handle QueryDict list values properly
            bill_value = self.data.get("bill")
            bill_pk = bill_value[0] if isinstance(bill_value, list) else bill_value
            if bill_pk:
                bill = Bill.objects.get(pk=int(bill_pk))
                self.fields["structure"].initial = bill.structure

    def clean(self) -> dict:
        """Update VAT amounts for validate form data before calling parent clean."""
        try:
            cleaned_data = super().clean()
            if cleaned_data is None:
                return {}
            cleaned_data["company"] = self.company
            print("cleaned_data", cleaned_data)

            amount = cleaned_data.get("amount")
            tx_date = cleaned_data.get("date")

            # Validate VAT rate against selected date
            if not tx_date:
                raise forms.ValidationError({"date": "Date is required."})

            if not amount:
                raise forms.ValidationError({"amount": "Amount is required."})

            # Explicit type assertion for mypy - we know company is a Company instance
            company_instance = cast(Company, self.company)
            if not company_instance.vat_registered:
                # For non-VAT companies, store calculated values in cleaned_data
                # These will be used in the save method
                cleaned_data["vat"] = False
                cleaned_data["vat_rate"] = None
                cleaned_data["amount_excl_vat"] = amount
                cleaned_data["amount_incl_vat"] = amount

                return cleaned_data
            else:
                # Get form values
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
                if cleaned_data["vat_mode"] == self.VAT_MODE_INCLUSIVE:
                    cleaned_data["amount_excl_vat"] = amount / (1 + vat_rate.rate / 100)
                    cleaned_data["amount_incl_vat"] = amount
                else:
                    cleaned_data["amount_excl_vat"] = amount
                    cleaned_data["amount_incl_vat"] = amount * (1 + vat_rate.rate / 100)

            return cleaned_data
        except Exception as e:
            # Re-raise forms.ValidationError as-is, but wrap other exceptions
            if isinstance(e, forms.ValidationError):
                raise e
            else:
                # Log unexpected errors and show a generic message
                import logging

                logger = logging.getLogger(__name__)
                logger.exception("Unexpected error in form clean method")
                raise forms.ValidationError(
                    "An unexpected error occurred. Please try again."
                ) from e

    def save(self, commit: bool = True) -> Transaction:
        """Save transaction with proper company assignment."""
        instance = super().save(commit=False)

        # Ensure company is set
        if not instance.company_id:
            instance.company = self.company

        if commit:
            instance.save()

        return instance


class NonVatTransactionCreateUpdateForm(BaseTransactionForm):
    """Transaction form for non-VAT registered companies."""


class VatTransactionCreateUpdateForm(BaseTransactionForm):
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
        choices=BaseTransactionForm.VAT_MODE_CHOICES,
        initial=BaseTransactionForm.VAT_MODE_INCLUSIVE,
        required=True,
    )

    class Meta(BaseTransactionForm.Meta):
        fields = ["ledger", "bill", "date", "vat_rate", "type", "amount", "vat_mode"]
