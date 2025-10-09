from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, UpdateView, View

from app.BillOfQuantities.forms import PaymentCertificateFinalApprovalForm
from app.BillOfQuantities.models import ActualTransaction, LineItem, PaymentCertificate
from app.Project.models import Project


class GetProjectMixin:
    def get_project(self) -> Project:
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
            deleted=False,
        )


class PaymentCertificateListView(LoginRequiredMixin, ListView, GetProjectMixin):
    model = PaymentCertificate
    template_name = "payment_certificate/payment_certificate_list.html"
    context_object_name = "payment_certificates"

    def get_queryset(self):
        project = self.get_project()
        return (
            PaymentCertificate.objects.filter(project=project)
            .select_related("project")
            .prefetch_related("actual_transactions")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project: Project = self.get_project()
        context["project"] = project

        # Active payment certificate (DRAFT or SUBMITTED)
        active_payment_certificate = project.get_active_payment_certificate
        context["active_certificate"] = active_payment_certificate

        # Completed payment certificates (APPROVED or REJECTED)
        if active_payment_certificate:
            context["completed_payment_certificates"] = self.object_list.exclude(
                pk=active_payment_certificate.pk
            ).order_by("-created_at")
        else:
            context["completed_payment_certificates"] = self.object_list.order_by(
                "-created_at"
            )

        return context


class PaymentCertificateDetailView(LoginRequiredMixin, DetailView, GetProjectMixin):
    model = PaymentCertificate
    template_name = "payment_certificate/payment_certificate_detail.html"
    context_object_name = "payment_certificate"

    def get_queryset(self):
        return (
            PaymentCertificate.objects.filter(
                project__account=self.request.user, deleted=False
            )
            .select_related("project")
            .prefetch_related(
                "actual_transactions__line_item__structure",
                "actual_transactions__line_item__bill",
                "actual_transactions__line_item__package",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()

        # Calculate total for all transactions
        total_amount = sum(t.total_price for t in self.object.actual_transactions.all())
        context["total_amount"] = total_amount

        return context


class PaymentCertificateEditView(LoginRequiredMixin, View):
    template_name = "payment_certificate/payment_certificate_edit.html"

    def get(self, request, pk=None, project_pk=None):
        project = get_object_or_404(Project, pk=project_pk, account=request.user)
        if not project.line_items:
            messages.error(request, "Project has no WBS loaded, please upload!")
            return redirect(
                "bill_of_quantities:structure-upload", project_pk=project_pk
            )
        if not pk:
            # no payment certificate selected, check if any active, or create new one
            payment_certificates = PaymentCertificate.objects.filter(
                project=project, status=PaymentCertificate.Status.DRAFT
            )
            if payment_certificates.exists():
                payment_certificate = payment_certificates.first()
            else:
                # create new pmt cert, and redirect to edit page
                next_certificate_number = (
                    PaymentCertificate.get_next_certificate_number(project)
                )
                payment_certificate = PaymentCertificate.objects.create(
                    project=project,
                    certificate_number=next_certificate_number,
                )
                messages.success(
                    request, "New Payment Certificate created successfully!"
                )
                return redirect(
                    "bill_of_quantities:payment-certificate-edit",
                    project_pk=project_pk,
                    pk=payment_certificate.pk,
                )

        else:
            payment_certificate = get_object_or_404(
                PaymentCertificate, pk=pk, project=project
            )

        if payment_certificate.status != PaymentCertificate.Status.DRAFT:
            messages.error(
                request, "Payment certifciate already approved, cannot edit anymore."
            )
            return redirect(
                "bill_of_quantities:payment-certificate-detail",
                project_pk=project_pk,
                pk=pk,
            )

        # Prefetch line items with related data
        line_items = project.line_items.select_related(
            "structure", "bill", "package"
        ).prefetch_related("actual_transactions")

        context = {
            "project": project,
            "payment_certificate": payment_certificate,
            "line_items": line_items,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk=None, project_pk=None):
        project = get_object_or_404(Project, pk=project_pk, account=request.user)
        if not project.line_items:
            messages.error(request, "Project has no WBS loaded, please upload!")
            return redirect(
                "bill_of_quantities:structure-upload", project_pk=project_pk
            )

        payment_certificate = get_object_or_404(
            PaymentCertificate, pk=pk, project=project
        )

        # Process actual quantities and create/update ActualTransaction records
        transactions_created = 0
        transactions_updated = 0

        for key, value in request.POST.items():
            line_item_pk = ""
            transaction_pk = ""
            quantity = 0
            if key.startswith("new_actual_quantity_"):
                if not value:
                    continue

                line_item_pk = key.replace("new_actual_quantity_", "")
                try:
                    quantity = Decimal(value)
                except (ValueError, TypeError, InvalidOperation):
                    continue

                # Only store non-zero quantities
                if quantity:
                    line_item: LineItem = project.line_items.get(pk=int(line_item_pk))
                    ActualTransaction.objects.create(
                        payment_certificate=payment_certificate,
                        line_item=line_item,
                        quantity=quantity - line_item.claimed_to_date,
                        unit_price=line_item.unit_price,
                        total_price=line_item.unit_price * quantity,
                        captured_by=request.user,
                    )
                    transactions_created += 1

            elif key.startswith("edit_actual_quantity_"):
                transaction_pk = key.replace("edit_actual_quantity_", "")
                try:
                    actual_transaction = ActualTransaction.objects.get(
                        pk=transaction_pk
                    )
                except ActualTransaction.DoesNotExist:
                    continue

                if not value:
                    # empty value
                    actual_transaction.delete()
                    transactions_updated += 1
                    continue

                try:
                    quantity = Decimal(value)
                except (ValueError, TypeError, InvalidOperation):
                    # invalid value
                    actual_transaction.delete()
                    transactions_updated += 1
                    continue
                line_item = actual_transaction.line_item
                if quantity == line_item.claimed_to_date:
                    # no change
                    continue

                # Only update non-zero quantities
                actual_transaction.quantity = quantity - line_item.claimed_to_date
                actual_transaction.unit_price = actual_transaction.line_item.unit_price
                actual_transaction.total_price = (
                    actual_transaction.quantity * actual_transaction.unit_price
                )
                actual_transaction.save()
                transactions_updated += 1

        # Show success message
        if transactions_created or transactions_updated:
            messages.success(
                request,
                f"Payment certificate updated: {transactions_created} new transactions, "
                f"{transactions_updated} updated.",
            )
        else:
            messages.info(request, "No changes were made.")

        return redirect(
            "bill_of_quantities:payment-certificate-edit",
            project_pk=project_pk,
            pk=pk,
        )


class PaymentCertificateSubmitView(LoginRequiredMixin, UpdateView, GetProjectMixin):
    model = PaymentCertificate
    fields = ["status"]
    template_name = "payment_certificate/payment_certificate_approve.html"
    context_object_name = "payment_certificate"

    def get_queryset(self):
        return (
            PaymentCertificate.objects.filter(
                project__account=self.request.user, deleted=False
            )
            .select_related("project")
            .prefetch_related(
                "actual_transactions__line_item__structure",
                "actual_transactions__line_item__bill",
                "actual_transactions__line_item__package",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()

        # Calculate total for all transactions
        total_amount = sum(t.total_price for t in self.object.actual_transactions.all())
        context["total_amount"] = total_amount

        return context

    def form_valid(self, form):
        payment_certificate = form.save(commit=False)

        # Mark all transactions as approved or not based on status
        if payment_certificate.status == PaymentCertificate.Status.SUBMITTED:
            payment_certificate.actual_transactions.update(approved=True)
            messages.success(
                self.request,
                f"Payment Certificate #{payment_certificate.certificate_number} has been submitted!",
            )
        else:
            payment_certificate.actual_transactions.update(approved=False)
            messages.warning(
                self.request,
                f"Payment Certificate #{payment_certificate.certificate_number} has been rejected.",
            )

        payment_certificate.save()

        return redirect(
            "bill_of_quantities:payment-certificate-detail",
            project_pk=self.kwargs["project_pk"],
            pk=payment_certificate.pk,
        )


class PaymentCertificateFinalApprovalView(
    LoginRequiredMixin, UpdateView, GetProjectMixin
):
    """Final approval/rejection view - choose between APPROVED or REJECTED."""

    model = PaymentCertificate
    form_class = PaymentCertificateFinalApprovalForm
    template_name = "payment_certificate/payment_certificate_final_approval.html"
    context_object_name = "payment_certificate"

    def get_queryset(self):
        return (
            PaymentCertificate.objects.filter(
                project__account=self.request.user, deleted=False
            )
            .select_related("project")
            .prefetch_related(
                "actual_transactions__line_item__structure",
                "actual_transactions__line_item__bill",
                "actual_transactions__line_item__package",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()

        # Calculate total for all transactions
        total_amount = sum(t.total_price for t in self.object.actual_transactions.all())
        context["total_amount"] = total_amount

        return context

    def form_valid(self, form):
        payment_certificate = form.save(commit=False)

        # Mark all transactions as claimed based on status
        if payment_certificate.status == PaymentCertificate.Status.APPROVED:
            payment_certificate.actual_transactions.update(claimed=True)
            messages.success(
                self.request,
                f"Payment Certificate #{payment_certificate.certificate_number} has been approved!",
            )
        else:
            payment_certificate.actual_transactions.update(
                claimed=False, approved=False
            )
            messages.warning(
                self.request,
                f"Payment Certificate #{payment_certificate.certificate_number} has been rejected.",
            )

        payment_certificate.save()

        return redirect(
            "bill_of_quantities:payment-certificate-detail",
            project_pk=self.kwargs["project_pk"],
            pk=payment_certificate.pk,
        )
