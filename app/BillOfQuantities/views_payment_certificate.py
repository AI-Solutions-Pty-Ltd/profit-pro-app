from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, UpdateView, View

from app.BillOfQuantities.models import ActualTransaction, LineItem, PaymentCertificate
from app.BillOfQuantities.tasks import generate_payment_certificate_pdf
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Project


class PaymentCertificateMixin(UserHasGroupGenericMixin):
    permissions = ["contractor"]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        if not hasattr(self, "project"):
            self.project = get_object_or_404(
                Project,
                pk=self.kwargs[self.project_slug],
                account=self.request.user,
                deleted=False,
            )
        return self.project

    def get_queryset(self):
        if not hasattr(self, "queryset"):
            self.queryset = (
                PaymentCertificate.objects.filter(
                    project=self.get_project(), project__account=self.request.user
                )
                .select_related("project")
                .prefetch_related("actual_transactions")
                .prefetch_related("actual_transactions__line_item")
                .prefetch_related("line_items")
                .prefetch_related("line_items__structure")
                .prefetch_related("line_items__bill")
                .prefetch_related("line_items__package")
                .order_by("certificate_number")
            )
        return self.queryset


class PaymentCertificateListView(PaymentCertificateMixin, ListView):
    model = PaymentCertificate
    template_name = "payment_certificate/payment_certificate_list.html"
    context_object_name = "payment_certificates"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()

        # Active payment certificate (DRAFT or SUBMITTED)
        active_payment_certificate: PaymentCertificate | None = (
            self.get_project().get_active_payment_certificate
        )
        context["active_certificate"] = active_payment_certificate

        # Completed payment certificates (APPROVED or REJECTED)
        if active_payment_certificate:
            completed_certificates = self.get_queryset().exclude(
                pk=active_payment_certificate.pk
            )
        else:
            completed_certificates = self.get_queryset()

        context["completed_payment_certificates"] = completed_certificates
        total_claimed = sum(t.total_claimed for t in completed_certificates)
        active_claimed = 0
        if active_payment_certificate:
            active_claimed = Decimal(
                active_payment_certificate.actual_transactions.aggregate(
                    total=Sum("total_price")
                )["total"]
                or 0
            )
        remaining_amount = (
            self.project.get_total_contract_value - total_claimed - active_claimed
        )
        context["total_claimed"] = total_claimed
        context["active_claimed"] = active_claimed
        context["remaining_amount"] = remaining_amount
        return context


class PaymentCertificateDetailView(PaymentCertificateMixin, DetailView):
    model = PaymentCertificate
    template_name = "payment_certificate/payment_certificate_detail.html"
    context_object_name = "payment_certificate"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()

        # Calculate total for all transactions
        total_amount = sum(t.total_price for t in self.object.actual_transactions.all())
        context["total_amount"] = total_amount

        return context


class PaymentCertificateEditView(PaymentCertificateMixin, View):
    template_name = "payment_certificate/payment_certificate_edit.html"

    def get(self, request, pk=None, project_pk=None):
        project = self.get_project()
        # Get unique structures, bills, packages for dropdowns
        if not project.line_items:
            messages.error(request, "Project has no WBS loaded, please upload!")
            return redirect(
                "bill_of_quantities:structure-upload", project_pk=project_pk
            )

        from app.BillOfQuantities.models import Bill, Package, Structure

        structures = Structure.objects.filter(project=project).distinct()
        bills = Bill.objects.filter(structure__project=project).distinct()
        packages = Package.objects.filter(bill__structure__project=project).distinct()

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

        # Apply filters
        structure_id = request.GET.get("structure")
        bill_id = request.GET.get("bill")
        package_id = request.GET.get("package")
        description = request.GET.get("description")

        if structure_id:
            line_items = line_items.filter(structure_id=structure_id)
            bills = bills.filter(structure_id=structure_id)
        if bill_id:
            line_items = line_items.filter(bill_id=bill_id)
            packages = packages.filter(bill_id=bill_id)
        if package_id:
            line_items = line_items.filter(package_id=package_id)
        if description:
            line_items = line_items.filter(description__icontains=description)

        context = {
            "project": project,
            "payment_certificate": payment_certificate,
            "line_items": line_items,
            "structures": structures,
            "bills": bills,
            "packages": packages,
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


class PaymentCertificateSubmitView(PaymentCertificateMixin, UpdateView):
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


class PaymentCertificateDownloadPDFView(PaymentCertificateMixin, View):
    """Download payment certificate as PDF."""

    def get(self, request, pk=None, project_pk=None):
        project = self.get_project()
        payment_certificate = get_object_or_404(
            PaymentCertificate, pk=pk, project=project, project__account=request.user
        )

        # Generate PDF in memory
        pdf = generate_payment_certificate_pdf(payment_certificate)
        pdf.name = f"payment_certificate_{payment_certificate.certificate_number}.pdf"
        pdf.type = "application/pdf"  # type: ignore
        payment_certificate.pdf = pdf
        payment_certificate.save()
        # Wrap ContentFile in BytesIO for FileResponse
        file = payment_certificate.pdf.open("rb")

        # Return PDF as download from memory
        response = FileResponse(
            file,
            content_type="application/pdf",
            as_attachment=True,
            filename=f"payment_certificate_{payment_certificate.certificate_number}.pdf",
        )

        return response
