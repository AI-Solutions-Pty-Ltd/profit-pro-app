"""Tests for PaymentCertificate views."""

from decimal import Decimal

import pytest
from dateutil.utils import today
from django.urls import reverse

from app.Account.models import Account
from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.models import PaymentCertificate
from app.BillOfQuantities.tests.factories import (
    ActualTransactionFactory,
    LineItemFactory,
    PaymentCertificateFactory,
)
from app.Project.models import ProjectRole, Role
from app.Project.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestPaymentCertificateListView:
    """Test cases for PaymentCertificateListView."""

    def test_list_view_requires_authentication(self, client):
        """Test that list view requires authentication."""
        project = ProjectFactory.create()
        url = reverse(
            "bill_of_quantities:payment-certificate-list",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_list_view_displays_certificates(self, client):
        """Test list view displays payment certificates."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        cert1 = PaymentCertificateFactory.create(project=project)
        cert2 = PaymentCertificateFactory.create(project=project)
        LineItemFactory.create(project=project)

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-list",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert cert1 in response.context["payment_certificates"]
        assert cert2 in response.context["payment_certificates"]

    def test_list_view_shows_active_certificate(self, client):
        """Test list view identifies active certificate."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        LineItemFactory.create(project=project)
        draft_cert = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )
        PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.APPROVED
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-list",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)

        assert response.context["active_certificate"] == draft_cert

    def test_list_view_user_can_only_see_own_certificates(self, client):
        """Test users can only see their own project certificates."""
        user1 = AccountFactory.create()
        user2 = AccountFactory.create()
        project1 = ProjectFactory.create(users=user1)
        LineItemFactory.create(project=project1)
        project2 = ProjectFactory.create(users=user2)
        LineItemFactory.create(project=project2)

        cert1 = PaymentCertificateFactory.create(project=project1)
        cert2 = PaymentCertificateFactory.create(project=project2)

        client.force_login(user1)
        url = reverse(
            "bill_of_quantities:payment-certificate-list",
            kwargs={"project_pk": project1.pk},
        )
        response = client.get(url)

        assert cert1 in response.context["payment_certificates"]
        assert cert2 not in response.context["payment_certificates"]


@pytest.mark.django_db
class TestPaymentCertificateDetailView:
    """Test cases for PaymentCertificateDetailView."""

    def test_detail_view_requires_authentication(self, client):
        """Test that detail view requires authentication."""
        certificate = PaymentCertificateFactory.create()
        url = reverse(
            "bill_of_quantities:payment-certificate-detail",
            kwargs={"project_pk": certificate.project.pk, "pk": certificate.pk},
        )
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_detail_view_displays_certificate(self, client):
        """Test detail view displays certificate details."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        line_item = LineItemFactory.create(project=project)
        certificate = PaymentCertificateFactory.create(project=project)
        _actual_transaction = ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            total_price=Decimal("500.00"),
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-detail",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["payment_certificate"] == certificate
        assert response.context["project"] == project

    def test_detail_view_calculates_total_amount(self, client):
        """Test detail view calculates total amount correctly."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        certificate: PaymentCertificate = PaymentCertificateFactory.create(
            project=project
        )
        line_item = LineItemFactory.create(project=project)

        ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            total_price=Decimal("500.00"),
            claimed=True,
        )
        ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            total_price=Decimal("300.00"),
            claimed=True,
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-detail",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert certificate.total_claimed == Decimal("800.00")


@pytest.mark.django_db
class TestPaymentCertificateEditView:
    """Test cases for PaymentCertificateEditView."""

    def test_edit_view_requires_authentication(self, client):
        """Test that edit view requires authentication."""
        certificate = PaymentCertificateFactory.create()
        url = reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": certificate.project.pk, "pk": certificate.pk},
        )
        response = client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_edit_view_creates_new_certificate_if_none_exists(self, client):
        """Test edit view creates new certificate when none exists."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        LineItemFactory.create(project=project)  # Need at least one line item

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-new",
            kwargs={"project_pk": project.pk},
        )
        response = client.get(url)

        assert response.status_code == 302  # Redirect to edit page
        assert project.payment_certificates.count() == 1

    def test_edit_view_prevents_editing_non_draft_certificates(self, client):
        """Test edit view prevents editing submitted/approved certificates."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        LineItemFactory.create(project=project)
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.SUBMITTED
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        response = client.get(url)

        assert response.status_code == 302  # Redirect
        # Check error message was added
        messages = list(response.wsgi_request._messages)
        assert any("cannot edit" in str(m).lower() for m in messages)

    def test_edit_view_post_creates_new_transactions(self, client):
        """Test POST request creates new actual transactions."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        line_item = LineItemFactory.create(
            project=project,
            unit_price=Decimal("100.00"),
            budgeted_quantity=Decimal("50.00"),
        )
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        response = client.post(url, {f"new_actual_quantity_{line_item.pk}": "10.00"})

        assert response.status_code == 302  # Redirect after save
        assert certificate.actual_transactions.count() == 1
        transaction = certificate.actual_transactions.first()
        assert transaction.quantity == Decimal("10.00")

    def test_edit_view_post_updates_existing_transactions(self, client):
        """Test POST request updates existing transactions."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        # start with 100 budget
        line_item = LineItemFactory.create(
            project=project,
            unit_price=Decimal("100.00"),
            budgeted_quantity=Decimal("100.00"),
        )
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )

        # certify 5 (95 remaining)
        actual_transaction = ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            quantity=Decimal("5.00"),
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )

        # change to 10 (90 remaining)
        response = client.post(
            url, {f"edit_actual_quantity_{actual_transaction.pk}": "10.00"}
        )

        assert response.status_code == 302
        actual_transaction.refresh_from_db()
        assert actual_transaction.quantity == Decimal("10.00")
        certificate.status = PaymentCertificate.Status.APPROVED
        certificate.save()

        new_certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )

        url = reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": project.pk, "pk": new_certificate.pk},
        )

        # alter total to 15 (85 remaining)
        response2 = client.post(url, {f"new_actual_quantity_{line_item.pk}": "15.00"})

        assert response2.status_code == 302
        assert new_certificate.actual_transactions.count() == 1
        transaction2 = new_certificate.actual_transactions.last()
        assert transaction2.quantity == Decimal("15.00")


@pytest.mark.django_db
class TestPaymentCertificateSubmitView:
    """Test cases for PaymentCertificateSubmitView."""

    def test_submit_view_updates_status_to_submitted(self, client):
        """Test submit view changes status to SUBMITTED."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )
        _line_item = LineItemFactory.create(project=project)

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-submit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        response = client.post(url, {"status": PaymentCertificate.Status.SUBMITTED})

        assert response.status_code == 302
        certificate = PaymentCertificate.objects.get(pk=certificate.pk)
        assert certificate.status == PaymentCertificate.Status.SUBMITTED

    def test_submit_view_marks_transactions_as_approved(self, client):
        """Test submit view marks all transactions as approved."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )
        line_item = LineItemFactory.create(project=project)
        trans1 = ActualTransactionFactory.create(
            payment_certificate=certificate, line_item=line_item, approved=False
        )
        trans2 = ActualTransactionFactory.create(
            payment_certificate=certificate, line_item=line_item, approved=False
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-submit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        response = client.post(url, {"status": "SUBMITTED"})

        assert response.status_code == 302
        trans1.refresh_from_db()
        trans2.refresh_from_db()
        assert trans1.approved is True
        assert trans2.approved is True


@pytest.mark.django_db
class TestPaymentCertificateFinalApprovalView:
    """Test cases for PaymentCertificateFinalApprovalView."""

    def test_final_approval_view_approves_certificate(self, client, consultant_user):
        """Test final approval view approves certificate."""
        project = ProjectFactory.create(users=consultant_user)
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.SUBMITTED
        )
        LineItemFactory.create(project=project)

        client.force_login(consultant_user)
        url = reverse(
            "bill_of_quantities:payment-certificate-submit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        response = client.post(url, {"status": "APPROVED", "is_final": False})

        assert response.status_code == 302
        certificate.refresh_from_db()
        assert certificate.status == PaymentCertificate.Status.APPROVED

    def test_final_approval_view_rejects_certificate(self, client, consultant_user):
        """Test final approval view can reject certificate."""
        project = ProjectFactory.create(users=consultant_user)
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.SUBMITTED
        )
        LineItemFactory.create(project=project)

        client.force_login(consultant_user)
        url = reverse(
            "bill_of_quantities:payment-certificate-submit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        response = client.post(
            url, {"status": PaymentCertificate.Status.REJECTED, "is_final": False}
        )

        assert response.status_code == 302
        certificate = PaymentCertificate.objects.get(pk=certificate.pk)
        assert certificate.status == PaymentCertificate.Status.REJECTED

    def test_final_approval_rejection_unmarks_transactions(
        self, client, consultant_user
    ):
        """Test rejection unmarks transactions as claimed and approved."""
        start = today()
        start = start.replace(year=start.year - 1)
        end = today()
        project = ProjectFactory.create(
            users=consultant_user, start_date=start, end_date=end
        )
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.SUBMITTED
        )
        line_item = LineItemFactory.create(project=project)
        trans1 = ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            claimed=True,
            approved=True,
        )

        client.force_login(consultant_user)
        url = reverse(
            "bill_of_quantities:payment-certificate-submit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        response = client.post(url, {"status": "REJECTED"})

        assert response.status_code == 302
        trans1.refresh_from_db()
        assert trans1.claimed is False
        assert trans1.approved is False


@pytest.mark.django_db
class TestPaymentCertificateEditViewPost:
    """Test cases for PaymentCertificateEditView POST operations."""

    @pytest.mark.skip("Test disabled - soft delete logic needs investigation")
    def test_post_deletes_transaction_with_empty_value(self, client):
        """Test POST with empty value deletes existing transaction."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        line_item = LineItemFactory.create(project=project)
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )
        transaction = ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            quantity=Decimal("10.00"),
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        response = client.post(url, {f"edit_actual_quantity_{transaction.pk}": ""})

        assert response.status_code == 302
        # Check if transaction is soft deleted
        transaction.refresh_from_db()
        assert transaction.is_deleted

    def test_post_ignores_invalid_decimal_values(self, client):
        """Test POST ignores invalid decimal values."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        line_item = LineItemFactory.create(project=project)
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        response = client.post(url, {f"new_actual_quantity_{line_item.pk}": "invalid"})

        assert response.status_code == 302
        assert certificate.actual_transactions.count() == 0

    def test_post_calculates_total_price_correctly(self, client):
        """Test POST calculates total_price from quantity and unit_price."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        line_item = LineItemFactory.create(
            project=project,
            unit_price=Decimal("50.00"),
            budgeted_quantity=Decimal("100.00"),
        )
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        response = client.post(url, {f"new_actual_quantity_{line_item.pk}": "20.00"})

        assert response.status_code == 302
        transaction = certificate.actual_transactions.first()
        assert transaction.total_price == Decimal("20.00") * Decimal("50.00")


@pytest.mark.django_db
class TestPaymentCertificateWorkflow:
    """Test complete payment certificate workflow."""

    def test_complete_workflow_draft_to_approved(self, client, project):
        """Test complete workflow from draft to approved."""
        line_item = LineItemFactory.create(
            project=project,
            unit_price=Decimal("100.00"),
            budgeted_quantity=Decimal("50.00"),
        )
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.DRAFT
        )
        admin_user: Account = project.users.first()

        client.force_login(admin_user)

        # Step 1: Add transactions
        edit_url = reverse(
            "bill_of_quantities:payment-certificate-edit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        client.post(edit_url, {f"new_actual_quantity_{line_item.pk}": "10.00"})

        # Step 2: Submit certificate
        submit_url = reverse(
            "bill_of_quantities:payment-certificate-submit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        client.post(submit_url, {"status": PaymentCertificate.Status.SUBMITTED})

        certificate = PaymentCertificate.objects.get(pk=certificate.pk)
        assert certificate.status == PaymentCertificate.Status.SUBMITTED
        first_transaction = certificate.actual_transactions.first()
        assert first_transaction is not None
        assert first_transaction.approved is True

        # Step 3: Final approval
        approve_url = reverse(
            "bill_of_quantities:payment-certificate-submit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        consultant_user = project.client.consultants.first()
        ProjectRole.objects.create(
            user=consultant_user, project=project, role=Role.PAYMENT_CERTIFICATES
        )
        client.force_login(consultant_user)
        _response = client.post(
            approve_url, {"status": PaymentCertificate.Status.APPROVED}
        )

        certificate = PaymentCertificate.objects.get(pk=certificate.pk)
        assert certificate.status == PaymentCertificate.Status.APPROVED
        first_transaction = certificate.actual_transactions.first()
        assert first_transaction is not None
        assert first_transaction.claimed is True

    def test_workflow_rejection_at_final_approval(self, client, project):
        """Test rejecting certificate at final approval stage."""
        line_item = LineItemFactory.create(project=project)
        certificate = PaymentCertificateFactory.create(
            project=project, status=PaymentCertificate.Status.SUBMITTED
        )
        transaction = ActualTransactionFactory.create(
            payment_certificate=certificate,
            line_item=line_item,
            approved=True,
            claimed=False,
        )

        consultant_user = project.client.consultants.first()
        ProjectRole.objects.create(
            user=consultant_user, project=project, role=Role.PAYMENT_CERTIFICATES
        )

        client.force_login(consultant_user)
        approve_url = reverse(
            "bill_of_quantities:payment-certificate-submit",
            kwargs={"project_pk": project.pk, "pk": certificate.pk},
        )
        client.post(approve_url, {"status": PaymentCertificate.Status.REJECTED})

        certificate.refresh_from_db()
        transaction.refresh_from_db()
        assert certificate.status == PaymentCertificate.Status.REJECTED
        assert transaction.approved is False
        assert transaction.claimed is False
