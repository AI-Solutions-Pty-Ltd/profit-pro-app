from django import forms

from app.Account.models import Municipality, Province


class MunicipalityFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={"placeholder": "Search by Province, Municipality, Code, or District"}
        ),
    )
    province = forms.ChoiceField(
        required=False,
        label="Province",
        choices=[("", "All Provinces")],
    )
    district = forms.ChoiceField(
        required=False,
        label="District",
        choices=[("", "All Districts")],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            province_field = self.fields["province"]
            if hasattr(province_field, "choices"):
                province_field.choices = [("", "All Provinces")] + list(  # type: ignore
                    Province.objects.order_by("name")
                    .values_list("id", "name")
                )

            district_field = self.fields["district"]
            if hasattr(district_field, "choices"):
                district_field.choices = [("", "All Districts")] + list(  # type: ignore
                    Municipality.objects.order_by("district")
                    .values_list("district", "district")
                    .distinct()
                )
        except Exception:
            # Handle cases where database might not be ready (e.g., migrations)
            pass
