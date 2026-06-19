"""Tests for ledger form pre-selection and disabling behavior."""

import pytest

from app.BillOfQuantities.forms import (
    AdvancedPaymentCreateUpdateForm,
    EscalationCreateUpdateForm,
    MaterialsOnSiteCreateUpdateForm,
    RetentionCreateUpdateCreateForm,
)
from app.BillOfQuantities.models import PaymentCertificate
from app.BillOfQuantities.tests.factories import (
    AdvancePaymentFactory,
    PaymentCertificateFactory,
)
from app.BillOfQuantities.views.ledger_views import (
    SpecialItemTransactionCreateView,
)
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestLedgerFormsActiveCertificateBehavior:
    """Test suite to verify that forms correctly pre-select and disable payment_certificate."""

    def test_create_forms_preselect_and_disable_active_certificate(self):
        """Verify that when creating, the active certificate is pre-selected and disabled."""
        project = ProjectFactory.create()
        # Create an active certificate
        active_cert = PaymentCertificateFactory.create(
            project=project,
            status=PaymentCertificate.Status.DRAFT,
        )

        form_classes = [
            AdvancedPaymentCreateUpdateForm,
            RetentionCreateUpdateCreateForm,
            MaterialsOnSiteCreateUpdateForm,
            EscalationCreateUpdateForm,
            SpecialItemTransactionCreateView.CreateForm,
        ]

        for form_cls in form_classes:
            form = form_cls(project=project)
            assert form.fields["payment_certificate"].initial == active_cert
            assert form.fields["payment_certificate"].disabled is True

    def test_update_forms_retain_existing_certificate_and_disable(self):
        """Verify that when editing, the existing certificate is kept and the field is disabled."""
        project = ProjectFactory.create()
        # Create a certificate
        cert = PaymentCertificateFactory.create(
            project=project,
            status=PaymentCertificate.Status.DRAFT,
        )

        # Create a transaction linked to the certificate
        advance = AdvancePaymentFactory.create(
            project=project,
            payment_certificate=cert,
        )

        # Instantiate update form
        form = AdvancedPaymentCreateUpdateForm(project=project, instance=advance)
        assert form.fields["payment_certificate"].disabled is True
        # Since it's bound to an instance, initial is populated from the instance
        assert form.initial.get("payment_certificate") == cert.pk

    def test_create_form_no_active_certificate(self):
        """Verify that if there is no active certificate, the field is not disabled or pre-selected."""
        project = ProjectFactory.create()
        # No active certificate is created

        form = AdvancedPaymentCreateUpdateForm(project=project)
        assert form.fields["payment_certificate"].initial is None
        assert form.fields["payment_certificate"].disabled is not True
