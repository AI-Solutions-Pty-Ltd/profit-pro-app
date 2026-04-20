from django import forms

from app.Account.models import Municipality


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
        choices=[("", "All Provinces")]
        + list(
            Municipality.objects.order_by("province")
            .values_list("province", "province")
            .distinct()
        ),
    )
    district = forms.ChoiceField(
        required=False,
        label="District",
        choices=[("", "All Districts")]
        + list(
            Municipality.objects.order_by("district")
            .values_list("district", "district")
            .distinct()
        ),
    )
