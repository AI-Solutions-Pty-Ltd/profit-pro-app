from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView, UpdateView, View

from app.BillOfQuantities.models import ActualTransaction, LineItem, PaymentCertificate
from app.BillOfQuantities.tasks import (
    generate_pdf_async,
    group_line_items_by_hierarchy,
    send_payment_certificate_to_signatories,
)
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Project


class PaymentCertificateMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    permissions = ["contractor"]
    project_slug = "project_pk"

    def dispatch(self, request, *args, **kwargs):
        """Check if project has line items before allowing any view access."""
        project = self.get_project()
        if not project.line_items.exists():
            messages.error(request, "Project has no WBS loaded, please upload!")
            return redirect(
                "bill_of_quantities:structure-upload", project_pk=project.pk
            )
        return super().dispatch(request, *args, **kwargs)

    def get_project(self) -> Project:
        if not hasattr(self, "project"):
            self.project = get_object_or_404(
                Project,
                pk=self.kwargs[self.project_slug],  # type: ignore
                account=self.request.user,  # type: ignore
            )
        return self.project

    def get_queryset(self):
        if not hasattr(self, "queryset") or not self.queryset:
            self.queryset = (
                PaymentCertificate.objects.filter(
                    project=self.get_project(),
                    project__account=self.request.user,  # type: ignore
                )
                .select_related("project")
                .prefetch_related(
                    "actual_transactions",
                    "actual_transactions__line_item",
                    "actual_transactions__line_item__structure",
                    "actual_transactions__line_item__bill",
                    "actual_transactions__line_item__package",
                )
                .order_by("certificate_number")
            )
        return self.queryset


class LineItemDetailMixin:
    def get_context_data(self: "LineItemDetailMixin", **kwargs):
        context = super().get_context_data(**kwargs)  # type: ignore
        context["project"] = self.get_project()  # type: ignore
        all_line_items = LineItem.abridged_payment_certificate(self.object)  # type: ignore
        line_items = all_line_items.filter(special_item=False, addendum=False)
        special_line_items = all_line_items.filter(special_item=True, addendum=False)
        addendum_line_items = all_line_items.filter(addendum=True, special_item=False)
        context["grouped_line_items"] = group_line_items_by_hierarchy(line_items)
        context["special_line_items"] = special_line_items
        context["addendum_line_items"] = group_line_items_by_hierarchy(
            addendum_line_items
        )

        return context


class PaymentCertificateListView(PaymentCertificateMixin, ListView):
    model = PaymentCertificate
    template_name = "payment_certificate/payment_certificate_list.html"
    context_object_name = "payment_certificates"

    def get_breadcrumbs(
        self: "PaymentCertificateListView",
    ) -> list[dict[str, str | None]]:
        return [
            {
                "title": "Projects",
                "url": reverse("project:project-list"),
            },
            {
                "title": self.get_project().name,
                "url": reverse(
                    "project:project-detail",
                    kwargs={"pk": self.get_project().pk},
                ),
            },
            {
                "title": "Payment Certificates",
                "url": None,
            },
        ]

    def get_context_data(self: "PaymentCertificateListView", **kwargs):
        context = super().get_context_data(**kwargs)  # type: ignore
        context["project"] = self.get_project()  # type: ignore

        # Active payment certificate (DRAFT or SUBMITTED)
        active_payment_certificate: PaymentCertificate | None = (
            self.get_project().get_active_payment_certificate
        )
        print(f"get_active_payment_certificate returned: {active_payment_certificate}")
        context["active_certificate"] = active_payment_certificate

        # Completed payment certificates (APPROVED or REJECTED)
        completed_certificates = self.get_queryset().order_by("-certificate_number")
        if active_payment_certificate and completed_certificates:
            completed_certificates = completed_certificates.exclude(
                pk=active_payment_certificate.pk
            )

        context["completed_payment_certificates"] = completed_certificates
        total_claimed = (
            sum(t.total_claimed for t in completed_certificates)
            if completed_certificates
            else Decimal(0)
        )
        active_claimed = 0
        if active_payment_certificate:
            active_claimed = sum_queryset(
                active_payment_certificate.actual_transactions.all(), "total_price"
            )
        remaining_amount = (
            self.project.get_total_contract_value - total_claimed - active_claimed
        )
        context["total_claimed"] = total_claimed
        context["active_claimed"] = active_claimed
        context["remaining_amount"] = remaining_amount
        return context


class PaymentCertificateDetailView(
    PaymentCertificateMixin, LineItemDetailMixin, DetailView
):
    model = PaymentCertificate
    template_name = "payment_certificate/payment_certificate_detail.html"
    context_object_name = "payment_certificate"

    def get_breadcrumbs(
        self: "PaymentCertificateDetailView",
    ) -> list[dict[str, str | None]]:
        return [
            {
                "title": self.get_project().name,
                "url": reverse(
                    "project:project-detail",
                    kwargs={"pk": self.get_project().pk},
                ),
            },
            {
                "title": "Payment Certificates",
                "url": reverse(
                    "bill_of_quantities:payment-certificate-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            },
            {
                "title": f"Payment Certificate: #{self.get_object().certificate_number}",
                "url": None,
            },
        ]

    def dispatch(self, request, *args, **kwargs):
        generate_pdf_async(self.get_object().id, "abridged")
        return super().dispatch(request, *args, **kwargs)


class PaymentCertificateEditView(PaymentCertificateMixin, View):
    template_name = "payment_certificate/payment_certificate_edit.html"

    def get_breadcrumbs(
        self: "PaymentCertificateEditView", **kwargs
    ) -> list[BreadcrumbItem]:
        return [
            {
                "title": "Payment Certificates",
                "url": reverse(
                    "bill_of_quantities:payment-certificate-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            },
            {
                "title": f"Return to Payment Certificate: #{self.kwargs['pk']} Detail",
                "url": reverse(
                    "bill_of_quantities:payment-certificate-detail",
                    kwargs={
                        "pk": self.kwargs["pk"],
                        "project_pk": self.get_project().pk,
                    },
                ),
            },
            {
                "title": "Edit",
                "url": None,
            },
        ]

    def get(self: "PaymentCertificateEditView", request, pk=None, project_pk=None):
        project: Project = self.get_project()

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
                messages.warning(
                    request,
                    "There is an active payment certificate. Please complete it before creating a new one.",
                )
                return redirect(
                    "bill_of_quantities:payment-certificate-edit",
                    project_pk=project_pk,
                    pk=payment_certificates.first().pk,  # type: ignore
                )
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
            payment_certificate: PaymentCertificate = get_object_or_404(
                PaymentCertificate, pk=pk, project=project
            )

        if payment_certificate.status != PaymentCertificate.Status.DRAFT:
            messages.error(
                request, "Payment certificate already approved, cannot edit anymore."
            )
            return redirect(
                "bill_of_quantities:payment-certificate-detail",
                project_pk=project_pk,
                pk=pk,
            )

        # Prefetch line items with related data
        all_line_items = project.get_line_items
        line_items = all_line_items.filter(special_item=False, addendum=False)
        special_line_items = all_line_items.filter(special_item=True, addendum=False)
        addendum_line_items = all_line_items.filter(addendum=True, special_item=False)

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
            "special_line_items": special_line_items,
            "addendum_line_items": addendum_line_items,
            "structures": structures,
            "bills": bills,
            "packages": packages,
            "breadcrumbs": self.get_breadcrumbs(),
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
            actual_transaction_pk = ""
            try:
                value = Decimal(value)
            except (ValueError, TypeError, InvalidOperation):
                # ignore invalid values
                continue
            if value < 0:
                # can be zero, in case someone wants to uncertify everything
                # ignore invalid values
                continue

            if key.startswith("new_actual_quantity_"):
                # new transaction
                line_item_pk = key.replace("new_actual_quantity_", "")
                line_item: LineItem = project.line_items.get(pk=int(line_item_pk))
                if not line_item.special_item:
                    # normal / addendum item - working with quantities
                    new_quantity = value
                    claimed_quantity = new_quantity - line_item.claimed_to_date
                    ActualTransaction.objects.create(
                        payment_certificate=payment_certificate,
                        line_item=line_item,
                        quantity=claimed_quantity,
                        unit_price=line_item.unit_price,
                        total_price=line_item.unit_price * claimed_quantity,
                        captured_by=request.user,
                    )
                    transactions_created += 1

                else:
                    # special item - working with values
                    claimed_value = value - line_item.claimed_to_date_value
                    ActualTransaction.objects.create(
                        payment_certificate=payment_certificate,
                        line_item=line_item,
                        quantity=0,
                        unit_price=0,
                        total_price=claimed_value,
                        captured_by=request.user,
                    )
                    transactions_created += 1

            elif key.startswith("edit_actual_quantity_"):
                # edit previously created transaction
                actual_transaction_pk = key.replace("edit_actual_quantity_", "")
                try:
                    actual_transaction: ActualTransaction = (
                        ActualTransaction.objects.get(pk=actual_transaction_pk)
                    )
                except ActualTransaction.DoesNotExist:
                    continue

                line_item = actual_transaction.line_item
                if not line_item.special_item:
                    # normal item / addendum - update quantity
                    update_quantity = value

                    claimed_quantity = update_quantity - line_item.claimed_to_date
                    actual_transaction.quantity = claimed_quantity
                    actual_transaction.unit_price = (
                        actual_transaction.line_item.unit_price
                    )
                    actual_transaction.total_price = (
                        claimed_quantity * actual_transaction.unit_price
                    )
                    actual_transaction.save()
                    transactions_updated += 1

                else:
                    # special item - update value
                    claimed_value = value - line_item.claimed_to_date_value
                    actual_transaction.quantity = 0
                    actual_transaction.unit_price = 0
                    actual_transaction.total_price = claimed_value
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


class PaymentCertificateSubmitView(
    PaymentCertificateMixin, LineItemDetailMixin, UpdateView
):
    model = PaymentCertificate
    fields = ["status"]
    template_name = "payment_certificate/payment_certificate_submit.html"
    context_object_name = "payment_certificate"

    def get_breadcrumbs(self: "PaymentCertificateSubmitView") -> list[BreadcrumbItem]:
        return [
            {
                "title": "Return to Payment Certificates",
                "url": reverse(
                    "bill_of_quantities:payment-certificate-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            },
            {
                "title": f"Payment Certificate #{self.get_object().certificate_number}",
                "url": reverse(
                    "bill_of_quantities:payment-certificate-detail",
                    kwargs={
                        "project_pk": self.get_project().pk,
                        "pk": self.get_object().pk,
                    },
                ),
            },
            {
                "title": "Submit",
                "url": None,
            },
        ]

    def form_valid(self, form):
        payment_certificate = form.save(commit=False)

        # Mark all transactions as approved or not based on status
        if payment_certificate.status == PaymentCertificate.Status.SUBMITTED:
            payment_certificate.actual_transactions.update(approved=True)
            messages.success(
                self.request,
                f"Payment Certificate #{payment_certificate.certificate_number} has been submitted!",
            )
            payment_certificate.approved_on = datetime.now()
            payment_certificate.approved_by = self.request.user
        else:
            payment_certificate.actual_transactions.update(approved=False)
            messages.warning(
                self.request,
                f"Payment Certificate #{payment_certificate.certificate_number} has been rejected.",
            )

        payment_certificate.save()

        # Generate PDFs asynchronously if they don't exist
        generate_pdf_async(payment_certificate.id, "both")
        messages.info(
            self.request,
            "Payment Certificate is being generated in the background. Please be patient.",
        )

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

        # Check if PDF is currently being generated
        if payment_certificate.pdf_generating:
            messages.info(
                request,
                "PDF is currently being generated. Please try again in a few moments.",
            )
            return redirect(
                "bill_of_quantities:payment-certificate-detail",
                project_pk=project_pk,
                pk=pk,
            )

        # Check if we need to generate or regenerate the PDF
        force_regenerate = bool(request.GET.get("force"))
        if not payment_certificate.pdf or force_regenerate:
            # Start async generation
            generate_pdf_async(payment_certificate.pk, "full")
            return redirect(
                "bill_of_quantities:payment-certificate-detail",
                project_pk=project_pk,
                pk=pk,
            )
        # PDF exists and is ready - serve it
        file = payment_certificate.pdf.open("rb")
        response = FileResponse(
            file,
            content_type="application/pdf",
            as_attachment=True,
            filename=f"payment_certificate_{payment_certificate.certificate_number}.pdf",
        )

        return response


class PaymentCertificateDownloadAbridgedPDFView(PaymentCertificateMixin, View):
    """Download abridged payment certificate as PDF."""

    def get(self, request, pk=None, project_pk=None):
        project = self.get_project()
        payment_certificate = get_object_or_404(
            PaymentCertificate, pk=pk, project=project, project__account=request.user
        )

        # Check if abridged PDF is currently being generated
        if payment_certificate.abridged_pdf_generating:
            messages.info(
                request,
                "Abridged PDF is currently being generated. Please try again in a few moments.",
            )
            return redirect(
                "bill_of_quantities:payment-certificate-detail",
                project_pk=project_pk,
                pk=pk,
            )

        # Check if we need to generate or regenerate the abridged PDF
        force_regenerate = bool(request.GET.get("force"))
        if not payment_certificate.abridged_pdf or force_regenerate:
            # Start async generation
            generate_pdf_async(payment_certificate.pk, "abridged")
            return redirect(
                "bill_of_quantities:payment-certificate-detail",
                project_pk=project_pk,
                pk=pk,
            )
        # Abridged PDF exists and is ready - serve it
        file = payment_certificate.abridged_pdf.open("rb")
        response = FileResponse(
            file,
            content_type="application/pdf",
            as_attachment=True,
            filename=f"payment_certificate_{payment_certificate.certificate_number}_abridged.pdf",
        )

        return response


class PaymentCertificatePDFStatusView(PaymentCertificateMixin, View):
    """API endpoint to check PDF generation status."""

    def get(self, request, pk=None, project_pk=None):
        project = self.get_project()
        payment_certificate = get_object_or_404(
            PaymentCertificate, pk=pk, project=project, project__account=request.user
        )

        return JsonResponse(
            {
                "pdf_generating": payment_certificate.pdf_generating,
                "pdf_available": bool(payment_certificate.pdf),
                "abridged_pdf_generating": payment_certificate.abridged_pdf_generating,
                "abridged_pdf_available": bool(payment_certificate.abridged_pdf),
            }
        )


class PaymentCertificateEmailView(PaymentCertificateMixin, View):
    """Email payment certificate PDF to all signatories."""

    def post(self, request, pk=None, project_pk=None):
        project = self.get_project()
        payment_certificate = get_object_or_404(
            PaymentCertificate, pk=pk, project=project, project__account=request.user
        )

        # Check if payment certificate is approved
        if payment_certificate.status != PaymentCertificate.Status.APPROVED:
            messages.error(
                request,
                "Payment certificate must be approved before sending emails.",
            )
            return redirect(
                "bill_of_quantities:payment-certificate-detail",
                project_pk=project_pk,
                pk=pk,
            )

        # Check if PDFs exists
        generate_pdf = False
        generate_abridged = False
        if not payment_certificate.pdf:
            generate_pdf = True
            generate_pdf_async(payment_certificate.pk, "full")
        if not payment_certificate.abridged_pdf:
            generate_abridged = True
            generate_pdf_async(payment_certificate.pk, "abridged")
        if generate_pdf or generate_abridged:
            messages.error(
                request,
                "Payment certificate is being generated, please wait for the process to complete.",
            )
            return redirect(
                "bill_of_quantities:payment-certificate-detail",
                project_pk=project_pk,
                pk=pk,
            )

        # Send email to signatories
        response, message = send_payment_certificate_to_signatories(
            payment_certificate.pk
        )

        if response:
            messages.success(
                request, "Payment certificate sent to signatories successfully!"
            )
        else:
            messages.error(request, message)

        return redirect(
            "bill_of_quantities:payment-certificate-detail",
            project_pk=project_pk,
            pk=pk,
        )
