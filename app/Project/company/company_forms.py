from typing import cast

from django import forms

from app.Account.models import Account
from app.Project.models import Company


class CompanyFilterForm(forms.Form):
    company = forms.ModelChoiceField(
        queryset=Company.objects.none(),
        required=False,
        label="Jump to Company",
        widget=forms.Select(
            attrs={
                "onchange": "this.form.submit()",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        user: Account = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        if user:
            self.fields["company"].queryset = user.get_contractors.order_by("name")  # type: ignore


class CompanyForm(forms.ModelForm):
    """Form for creating and editing companies."""

    users = forms.ModelMultipleChoiceField(
        queryset=Account.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Company Users",
    )
    consultants = forms.ModelMultipleChoiceField(
        queryset=Account.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Company Consultants",
    )

    class Meta:
        model = Company
        fields = [
            "logo",
            "name",
            "registration_number",
            "tax_number",
            "vat_registered",
            "vat_number",
            "bank_name",
            "bank_account_name",
            "bank_account_number",
            "bank_branch_code",
            "bank_swift_code",
            "users",
            "consultants",
        ]
        widgets = {
            "logo": forms.FileInput(
                attrs={
                    "class": "mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100",
                    "accept": "image/*",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter company name",
                }
            ),
            "registration_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter registration number",
                }
            ),
            "tax_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter tax number",
                }
            ),
            "vat_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter VAT number",
                }
            ),
            "bank_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter bank name",
                }
            ),
            "bank_account_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter account holder name",
                }
            ),
            "bank_account_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter account number",
                }
            ),
            "bank_branch_code": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter branch code",
                }
            ),
            "bank_swift_code": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter SWIFT/BIC code",
                }
            ),
        }

    def __init__(self, *args, contractor=False, client=False, **kwargs):
        super().__init__(*args, **kwargs)
        users_field = cast(forms.ModelMultipleChoiceField, self.fields["users"])
        consultants_field = cast(
            forms.ModelMultipleChoiceField,
            self.fields["consultants"],
        )

        users_field.queryset = Account.objects.order_by("first_name", "email")
        consultants_field.queryset = Account.objects.order_by("first_name", "email")

        company_type = None
        if self.instance and self.instance.pk:
            company_type = self.instance.type

        if contractor or company_type == Company.Type.CONTRACTOR:
            # Contractors only maintain company users in this form.
            self.fields.pop("consultants", None)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data is None:
            return cleaned_data

        if (
            Company.objects.filter(
                name=cleaned_data["name"], type=Company.Type.CONTRACTOR
            )
            .exclude(id=self.instance.id)
            .exists()
        ):
            raise forms.ValidationError("Contractor with this name already exists.")

    def save(self, commit=True):
        """Save the instance, discarding VAT number if VAT registered is not selected."""
        instance = super().save(commit=False)

        # If VAT registered is not checked, clear the VAT number
        if not instance.vat_registered:
            instance.vat_number = ""

        if commit:
            instance.save()
            self.save_m2m()

        return instance
