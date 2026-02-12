from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Sum
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView, UpdateView, View

from app.BillOfQuantities.forms import (
    PaymentCertificatePhotoForm,
    PaymentCertificateWorkingForm,
)
from app.BillOfQuantities.models import (
    ActualTransaction,
    LineItem,
    PaymentCertificate,
    PaymentCertificatePhoto,
    PaymentCertificateWorking,
)
from app.BillOfQuantities.tasks import (
    generate_pdf_async,
    group_line_items_by_hierarchy,
    send_payment_certificate_to_signatories,
)
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import (
    UserHasProjectRoleGenericMixin,
)
from app.Project.models import PlannedValue, Project, Role


class PaymentCertificateMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    roles = [Role.PAYMENT_CERTIFICATES, Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def dispatch(self, request, *args, **kwargs):
        """Check if project has line items before allowing any view access."""
        # First, let the parent handle authentication and permissions
        response = super().dispatch(request, *args, **kwargs)

        # Only check line items if user is authenticated and has permissions
        if request.user.is_authenticated:
            project = self.get_project()
            if not project.line_items.exists():
                messages.error(request, "Project has no WBS loaded, please upload!")
                return redirect(
                    "bill_of_quantities:structure-upload", project_pk=project.pk
                )

        return response

    def get_queryset(self: "PaymentCertificateMixin"):
        if not hasattr(self, "queryset") or not self.queryset:
            self.queryset = (
                PaymentCertificate.objects.filter(
                    project=self.get_project(),
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
    template_name = "payment_certificate/dashboard.html"
    context_object_name = "payment_certificates"
    project_slug = "project_pk"

    def get_breadcrumbs(
        self: "PaymentCertificateListView",
    ) -> list[BreadcrumbItem]:
        return [
            {
                "title": "Projects",
                "url": reverse("project:portfolio-dashboard"),
            },
            {
                "title": self.get_project().name,
                "url": reverse(
                    "project:project-management",
                    kwargs={"pk": self.get_project().pk},
                ),
            },
            {
                "title": "Payment Certificates",
                "url": None,
            },
        ]

    def get_context_data(self: "PaymentCertificateListView", **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project

        # Active payment certificate (DRAFT or SUBMITTED)
        active_payment_certificate: PaymentCertificate | None = (
            self.get_project().active_payment_certificate
        )
        context["active_certificate"] = active_payment_certificate

        # Completed payment certificates (APPROVED or REJECTED)
        completed_certificates = self.get_queryset().order_by("-certificate_number")
        if active_payment_certificate and completed_certificates:
            completed_certificates = completed_certificates.exclude(
                pk=active_payment_certificate.pk
            )

        context["completed_payment_certificates"] = completed_certificates

        # Contract values
        revised_contract_value = project.total_contract_value
        context["revised_contract_value"] = revised_contract_value

        # Total certified (from approved certificates)
        total_certified = (
            sum(t.total_claimed for t in completed_certificates)
            if completed_certificates
            else Decimal(0)
        )
        context["total_certified"] = total_certified

        # Calculate percentage certified
        if revised_contract_value and revised_contract_value != 0:
            certified_percent = (total_certified / revised_contract_value) * 100
            context["certified_percent"] = round(float(certified_percent), 1)
        else:
            context["certified_percent"] = 0

        # Current claim (active certificate)
        current_claim = 0
        if active_payment_certificate:
            current_claim = sum_queryset(
                active_payment_certificate.actual_transactions.all(), "total_price"
            )
        context["current_claim"] = current_claim

        # Remaining amount
        remaining_amount = revised_contract_value - total_certified - current_claim
        context["remaining_amount"] = remaining_amount

        # Calculate remaining percentage
        if revised_contract_value and revised_contract_value != 0:
            remaining_percent = (remaining_amount / revised_contract_value) * 100
            context["remaining_percent"] = round(float(remaining_percent), 1)
        else:
            context["remaining_percent"] = 0

        # Chart data: Cumulative Actuals vs Planned Values
        chart_data = self._get_chart_data()
        context["chart_labels"] = chart_data["labels"]
        context["chart_planned_cumulative"] = chart_data["planned_cumulative"]
        context["chart_actual_cumulative"] = chart_data["actual_cumulative"]
        context["has_chart_data"] = chart_data["has_data"]

        return context

    def _get_chart_data(self) -> dict:
        """Generate chart data comparing cumulative actuals vs planned values."""
        from dateutil.relativedelta import relativedelta

        project = self.get_project()

        # Get planned values ordered by period
        planned_values = list(
            PlannedValue.objects.filter(project=project).order_by("period")
        )

        if not planned_values:
            return {
                "labels": [],
                "planned_cumulative": [],
                "actual_cumulative": [],
                "has_data": False,
            }

        # Build month labels and cumulative planned values
        labels = []
        planned_cumulative = []
        actual_cumulative = []
        running_planned = Decimal("0")
        running_actual = Decimal("0")

        for pv in planned_values:
            # Period label
            labels.append(pv.period.strftime("%b %Y"))

            # Cumulative planned
            running_planned += pv.value
            planned_cumulative.append(float(running_planned))

            # Calculate actual for this period
            # Get the start and end of this month
            period_start = pv.period.replace(day=1)
            period_end = period_start + relativedelta(months=1)

            # Sum all actual transactions from approved payment certificates
            # where the certificate was approved in this period (using approved_on date)
            period_actual = ActualTransaction.objects.filter(
                payment_certificate__project=project,
                payment_certificate__status=PaymentCertificate.Status.APPROVED,
                payment_certificate__approved_on__gte=period_start,
                payment_certificate__approved_on__lt=period_end,
            ).aggregate(total=Sum("total_price"))["total"] or Decimal("0")

            running_actual += period_actual
            actual_cumulative.append(float(running_actual))

        return {
            "labels": labels,
            "planned_cumulative": planned_cumulative,
            "actual_cumulative": actual_cumulative,
            "has_data": True,
        }


class PaymentCertificateDetailView(
    PaymentCertificateMixin, LineItemDetailMixin, DetailView
):
    model = PaymentCertificate
    template_name = "payment_certificate/payment_certificate_detail.html"
    context_object_name = "payment_certificate"

    def get_breadcrumbs(
        self: "PaymentCertificateDetailView",
    ) -> list[BreadcrumbItem]:
        return [
            {
                "title": self.get_project().name,
                "url": reverse(
                    "project:project-management",
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
        dispatch = super().dispatch(request, *args, **kwargs)
        if dispatch.status_code > 299:
            return dispatch
        generate_pdf_async(self.get_object().id, "abridged")
        return dispatch


class PaymentCertificateEditView(PaymentCertificateMixin, TemplateView):
    template_name: str = "payment_certificate/payment_certificate_edit.html"
    roles = [
        Role.PAYMENT_CERTIFICATES,
        Role.ADMIN,
        Role.USER,
        Role.CLIENT,
        Role.CONSULTANT,
    ]
    project_slug = "project_pk"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure template_name is always a string
        if not self.template_name:
            self.template_name = "payment_certificate/payment_certificate_edit.html"

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

    def get(self: "PaymentCertificateEditView", request, *args, **kwargs):
        project: Project = self.get_project()
        pk = kwargs.get("pk")
        project_pk = kwargs.get("project_pk")

        from app.BillOfQuantities.models import Bill, Package, Structure

        structures = Structure.objects.filter(project=project).distinct()
        bills = Bill.objects.filter(structure__project=project).distinct()
        packages = Package.objects.filter(bill__structure__project=project).distinct()

        if not pk:
            # no payment certificate selected, check if any active, or create new one

            # Validate project dates are set and current date is within project period
            today = date.today()
            if not project.start_date or not project.end_date:
                messages.error(
                    request,
                    "Cannot create payment certificate: Project start date and end date must be set.",
                )
                return redirect(
                    "bill_of_quantities:payment-certificate-list",
                    project_pk=project_pk,
                )

            if today < project.start_date:
                messages.error(
                    request,
                    f"Cannot create payment certificate: Project has not started yet (starts {project.start_date.strftime('%d %b %Y')}).",
                )
                return redirect(
                    "bill_of_quantities:payment-certificate-list",
                    project_pk=project_pk,
                )

            if today > project.end_date:
                messages.error(
                    request,
                    f"Cannot create payment certificate: Project has ended ({project.end_date.strftime('%d %b %Y')}). Please update project end date if needed.",
                )
                return redirect(
                    "bill_of_quantities:payment-certificate-list",
                    project_pk=project_pk,
                )

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
                project.payment_certificates.update(is_final=False)
                project.final_payment_certificate = None
                if project.status == Project.Status.FINAL_ACCOUNT_ISSUED:
                    project.status = Project.Status.ACTIVE
                project.save()
                next_certificate_number = (
                    PaymentCertificate.get_next_certificate_number(project)
                )
                payment_certificate = PaymentCertificate.objects.create(
                    project=project,
                    is_final=False,
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
            "photos": payment_certificate.photos.all().order_by("-created_at"),
            "workings": payment_certificate.workings.all().order_by("-created_at"),
            "photo_form": PaymentCertificatePhotoForm(),
            "working_form": PaymentCertificateWorkingForm(),
        }
        return render(request, str(self.template_name), context)

    def post(self, request, pk=None, project_pk=None):
        project = self.get_project()
        if not project.line_items:
            messages.error(request, "Project has no WBS loaded, please upload!")
            return redirect(
                "bill_of_quantities:structure-upload", project_pk=project_pk
            )

        payment_certificate = get_object_or_404(
            PaymentCertificate, pk=pk, project=project
        )

        # Handle photo uploads
        if "upload_photo" in request.POST:
            photo_form = PaymentCertificatePhotoForm(
                request.POST, request.FILES, payment_certificate=payment_certificate
            )
            if photo_form.is_valid():
                photo_form.save(uploaded_by=request.user)
                messages.success(request, "Photo uploaded successfully!")
            else:
                messages.error(
                    request, "Failed to upload photo. Please check the file."
                )
            return redirect(
                "bill_of_quantities:payment-certificate-edit",
                project_pk=project_pk,
                pk=pk,
            )

        # Handle working document uploads
        if "upload_working" in request.POST:
            working_form = PaymentCertificateWorkingForm(
                request.POST, request.FILES, payment_certificate=payment_certificate
            )
            if working_form.is_valid():
                working_form.save(uploaded_by=request.user)
                messages.success(request, "Working document uploaded successfully!")
            else:
                messages.error(
                    request, "Failed to upload document. Please check the file."
                )
            return redirect(
                "bill_of_quantities:payment-certificate-edit",
                project_pk=project_pk,
                pk=pk,
            )

        # Handle photo deletion
        if "delete_photo" in request.POST:
            photo_id = request.POST.get("delete_photo")
            try:
                photo = PaymentCertificatePhoto.objects.get(
                    id=photo_id, payment_certificate=payment_certificate
                )
                photo.delete()
                messages.success(request, "Photo deleted successfully!")
            except PaymentCertificatePhoto.DoesNotExist:
                messages.error(request, "Photo not found.")
            return redirect(
                "bill_of_quantities:payment-certificate-edit",
                project_pk=project_pk,
                pk=pk,
            )

        # Handle working document deletion
        if "delete_working" in request.POST:
            working_id = request.POST.get("delete_working")
            try:
                working = PaymentCertificateWorking.objects.get(
                    id=working_id, payment_certificate=payment_certificate
                )
                working.delete()
                messages.success(request, "Working document deleted successfully!")
            except PaymentCertificateWorking.DoesNotExist:
                messages.error(request, "Document not found.")
            return redirect(
                "bill_of_quantities:payment-certificate-edit",
                project_pk=project_pk,
                pk=pk,
            )

        # Process actual quantities and create/update ActualTransaction records
        transactions_created = 0
        transactions_updated = 0

        for key, value in request.POST.items():
            line_item_pk = ""
            actual_transaction_pk = ""
            delete = False
            if value == "":
                delete = True
                value = 0
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
                if delete:
                    actual_transaction.delete()
                    transactions_updated += 1
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
            "bill_of_quantities:payment-certificate-list",
            project_pk=project_pk,
        )


class PaymentCertificateSubmitView(
    PaymentCertificateMixin, LineItemDetailMixin, UpdateView
):
    model = PaymentCertificate
    fields = ["status", "is_final"]
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
        project = payment_certificate.project
        today = datetime.now().date()

        # Validate approval date falls within project dates
        if payment_certificate.status == PaymentCertificate.Status.SUBMITTED:
            if project.start_date and today < project.start_date:
                messages.error(
                    self.request,
                    f"Cannot approve certificate before project start date ({project.start_date.strftime('%d %b %Y')}).",
                )
                return redirect(
                    "bill_of_quantities:payment-certificate-submit",
                    project_pk=self.kwargs["project_pk"],
                    pk=payment_certificate.pk,
                )
            if project.end_date and today > project.end_date:
                messages.error(
                    self.request,
                    f"Cannot approve certificate after project end date ({project.end_date.strftime('%d %b %Y')}).",
                )
                return redirect(
                    "bill_of_quantities:payment-certificate-submit",
                    project_pk=self.kwargs["project_pk"],
                    pk=payment_certificate.pk,
                )

        # Mark all transactions as approved or not based on status
        if payment_certificate.status == PaymentCertificate.Status.SUBMITTED:
            payment_certificate.actual_transactions.update(approved=True, claimed=False)
            messages.success(
                self.request,
                f"Payment Certificate #{payment_certificate.certificate_number} has been submitted!",
            )
            payment_certificate.approved_on = datetime.now()
            payment_certificate.approved_by = self.request.user

            # If marked as final, link to project
            if payment_certificate.is_final:
                project.final_payment_certificate = payment_certificate
                project.save(update_fields=["final_payment_certificate"])
                messages.info(
                    self.request,
                    "This certificate has been marked as the Final Payment Certificate.",
                )
        elif payment_certificate.status == PaymentCertificate.Status.APPROVED:
            payment_certificate.actual_transactions.update(approved=True, claimed=True)
            messages.success(
                self.request,
                f"Payment Certificate #{payment_certificate.certificate_number} has been approved!",
            )
        elif payment_certificate.status == PaymentCertificate.Status.REJECTED:
            payment_certificate.actual_transactions.update(
                approved=False, claimed=False
            )
            messages.success(
                self.request,
                f"Payment Certificate #{payment_certificate.certificate_number} has been rejected!",
            )
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
        messages.info(
            self.request,
            "Reminder to capture any payments in the payment statement section.",
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
            PaymentCertificate, pk=pk, project=project, project__users=request.user
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
            PaymentCertificate, pk=pk, project=project, project__users=request.user
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
            PaymentCertificate, pk=pk, project=project, project__users=request.user
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
            PaymentCertificate, pk=pk, project=project, project__users=request.user
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


class PaymentCertificateMarkFinalView(PaymentCertificateMixin, DetailView):
    """Mark a payment certificate as the final payment certificate."""

    model = PaymentCertificate

    def post(self, request, *args, **kwargs):
        """Handle POST request to mark certificate as final."""
        payment_certificate = self.get_object()
        project = payment_certificate.project

        # Validate the certificate is approved
        if payment_certificate.status != PaymentCertificate.Status.APPROVED:
            messages.error(
                request,
                "Only approved payment certificates can be marked as final.",
            )
            return redirect(
                "bill_of_quantities:payment-certificate-dashboard",
                project_pk=project.pk,
            )

        # Mark as final
        payment_certificate.is_final = True
        payment_certificate.save(update_fields=["is_final"])

        # Update project
        project.final_payment_certificate = payment_certificate
        project.status = Project.Status.FINAL_ACCOUNT_ISSUED
        project.save(update_fields=["final_payment_certificate", "status"])

        messages.success(
            request,
            f"Payment Certificate #{payment_certificate.certificate_number} has been marked as the Final Payment Certificate.",
        )

        return redirect(
            "bill_of_quantities:payment-certificate-list",
            project_pk=project.pk,
        )

    def get(self, request, *args, **kwargs):
        """Redirect GET requests to dashboard."""
        return redirect(
            "bill_of_quantities:payment-certificate-list",
            project_pk=self.kwargs["project_pk"],
        )


class PaymentCertificateUnmarkFinalView(PaymentCertificateMixin, DetailView):
    """Unmark a payment certificate as the final payment certificate."""

    model = PaymentCertificate

    def post(self, request, *args, **kwargs):
        """Handle POST request to unmark certificate as final."""
        payment_certificate = self.get_object()
        project = payment_certificate.project

        # Validate the certificate is currently marked as final
        if not payment_certificate.is_final:
            messages.error(
                request,
                "This payment certificate is not marked as final.",
            )
            return redirect(
                "bill_of_quantities:payment-certificate-list",
                project_pk=project.pk,
            )

        # Unmark as final
        payment_certificate.is_final = False
        payment_certificate.save(update_fields=["is_final"])

        # Update project
        project.final_payment_certificate = None
        # Only change status if it was FINAL_ACCOUNT_ISSUED
        if project.status == Project.Status.FINAL_ACCOUNT_ISSUED:
            project.status = Project.Status.ACTIVE
        project.save(update_fields=["final_payment_certificate", "status"])

        messages.success(
            request,
            f"Payment Certificate #{payment_certificate.certificate_number} is no longer marked as the Final Payment Certificate.",
        )

        return redirect(
            "bill_of_quantities:payment-certificate-list",
            project_pk=project.pk,
        )

    def get(self, request, *args, **kwargs):
        """Redirect GET requests to dashboard."""
        return redirect(
            "bill_of_quantities:payment-certificate-list",
            project_pk=self.kwargs["project_pk"],
        )
