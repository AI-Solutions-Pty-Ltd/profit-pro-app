from django import forms

from app.BillOfQuantities.models import (
    AdvancePayment,
    Escalation,
    MaterialsOnSite,
    Retention,
)
from app.core.Utilities.forms import styled_date_input


class AdvancedPaymentCreateUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        self.fields["date"].widget = styled_date_input
        self.fields["guarantee_expiry"].widget = styled_date_input

        # Filter payment certificates to current project
        if self.project:
            self.fields[
                "payment_certificate"
            ].queryset = self.project.payment_certificates.all().order_by(  # type: ignore
                "-created_at"
            )
            active_cert = self.project.active_payment_certificate
            if active_cert:
                if not self.instance.pk:
                    self.fields["payment_certificate"].initial = active_cert
                self.fields["payment_certificate"].disabled = True

    class Meta:
        model = AdvancePayment
        fields = [
            "transaction_type",
            "amount",
            "description",
            "date",
            "payment_certificate",
            "recovery_method",
            "recovery_percentage",
            "guarantee_reference",
            "guarantee_expiry",
        ]


class RetentionCreateUpdateCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        self.fields["date"].widget = styled_date_input

        # Filter payment certificates to current project
        if self.project:
            self.fields[
                "payment_certificate"
            ].queryset = self.project.payment_certificates.all().order_by(  # type: ignore
                "-created_at"
            )
            active_cert = self.project.active_payment_certificate
            if active_cert:
                if not self.instance.pk:
                    self.fields["payment_certificate"].initial = active_cert
                self.fields["payment_certificate"].disabled = True

    class Meta:
        model = Retention
        fields = [
            "retention_type",
            "transaction_type",
            "amount",
            "description",
            "date",
            "payment_certificate",
            "retention_percentage",
        ]


class MaterialsOnSiteCreateUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        self.fields["date"].widget = styled_date_input

        # Filter payment certificates to current project
        if self.project:
            self.fields[
                "payment_certificate"
            ].queryset = self.project.payment_certificates.all().order_by(  # type: ignore
                "-created_at"
            )
            active_cert = self.project.active_payment_certificate
            if active_cert:
                if not self.instance.pk:
                    self.fields["payment_certificate"].initial = active_cert
                self.fields["payment_certificate"].disabled = True

    class Meta:
        model = MaterialsOnSite
        fields = [
            "material_status",
            "transaction_type",
            "amount",
            "description",
            "date",
            "payment_certificate",
            "material_description",
            "quantity",
            "unit",
            "unit_price",
            "delivery_note_reference",
            "storage_location",
        ]


class EscalationCreateUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)
        self.fields["date"].widget = styled_date_input
        self.fields["base_date"].widget = styled_date_input
        self.fields["current_date"].widget = styled_date_input

        # Filter payment certificates to current project
        if self.project:
            self.fields[
                "payment_certificate"
            ].queryset = self.project.payment_certificates.all().order_by(  # type: ignore
                "-created_at"
            )
            active_cert = self.project.active_payment_certificate
            if active_cert:
                if not self.instance.pk:
                    self.fields["payment_certificate"].initial = active_cert
                self.fields["payment_certificate"].disabled = True

    class Meta:
        model = Escalation
        fields = [
            "escalation_type",
            "transaction_type",
            "amount",
            "description",
            "date",
            "payment_certificate",
            "base_date",
            "current_date",
            "base_index",
            "current_index",
            "escalation_factor",
            "formula_reference",
        ]
