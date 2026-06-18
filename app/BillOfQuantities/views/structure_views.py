"""Views for Structure app."""

from pathlib import Path

import pandas as pd
from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import (
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.views.generic.edit import FormView

from app.Account.subscription_config import Subscription
from app.BillOfQuantities.forms import (
    StructureExcelUploadForm,
    StructureForm,
)
from app.BillOfQuantities.models import Structure
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.subscription_and_role_mixin import (
    SubscriptionAndRoleRequiredMixin,
)
from app.Project.models import Role


class StructureListView(SubscriptionAndRoleRequiredMixin, BreadcrumbMixin, ListView):
    """List all structures for a project."""

    model = Structure
    template_name = "structure/structure_list.html"
    context_object_name = "structures"
    roles = [Role.CONTRACT_BOQ]
    project_slug = "project_pk"
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]

    def get_queryset(self):
        """Filter structures by the current project."""
        project = self.get_project()
        from django.db.models import Prefetch
        from app.BillOfQuantities.models import LineItem
        
        return Structure.objects.filter(project=project).select_related("project").prefetch_related(
            Prefetch(
                "line_items",
                queryset=LineItem.objects.filter(is_work=True).order_by("row_index"),
                to_attr="work_line_items"
            )
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Project Management",
                "url": reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            },
            {"title": "Sections", "url": None},
        ]


class StructureDetailView(
    SubscriptionAndRoleRequiredMixin,
    BreadcrumbMixin,
    DetailView,
):
    """Display a single structure."""

    model = Structure
    template_name = "structure/structure_detail.html"
    context_object_name = "structure"
    roles = [Role.CONTRACT_BOQ]
    project_slug = "project_pk"
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]

    def get_queryset(self):
        """Filter structures by the current project."""
        return Structure.objects.filter(project=self.get_project()).select_related(
            "project"
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        project = self.get_project()
        return [
            {
                "title": "Sections",
                "url": reverse(
                    "bill_of_quantities:structure-list",
                    kwargs={"project_pk": project.pk},
                ),
            },
            {"title": self.object.name, "url": None},
        ]


class StructureUpdateView(
    SubscriptionAndRoleRequiredMixin,
    BreadcrumbMixin,
    UpdateView,
):
    """Update an existing structure."""

    model = Structure
    form_class = StructureForm
    template_name = "structure/structure_form.html"
    roles = [Role.CONTRACT_BOQ]
    project_slug = "project_pk"
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]

    def get_context_data(self, **kwargs):
        """Add inline formset to template context."""
        context = super().get_context_data(**kwargs)
        from app.BillOfQuantities.forms import LineItemInlineFormSet

        if self.request.POST:
            context["line_items"] = LineItemInlineFormSet(
                self.request.POST, instance=self.object, prefix="line_items"
            )
        else:
            context["line_items"] = LineItemInlineFormSet(
                instance=self.object, prefix="line_items"
            )
        return context

    def form_valid(self, form):
        """Save structure and inline line items."""
        from decimal import Decimal
        from django.db import models
        from app.BillOfQuantities.models import LineItem

        context = self.get_context_data()
        line_items = context["line_items"]

        if form.is_valid() and line_items.is_valid():
            self.object = form.save()
            instances = line_items.save(commit=False)
            project = self.get_project()

            for instance in instances:
                instance.project = project
                if not instance.row_index:
                    max_row = (
                        LineItem.objects.filter(project=project).aggregate(
                            models.Max("row_index")
                        )["row_index__max"]
                        or 0
                    )
                    instance.row_index = max_row + 1

                # Calculate total_price
                if instance.is_work:
                    qty = instance.budgeted_quantity or Decimal("0.00")
                    rate = instance.unit_price or Decimal("0.00")
                    instance.total_price = qty * rate
                else:
                    instance.total_price = Decimal("0.00")
                instance.save()

            line_items.save_m2m()

            # Handle deleted items
            for deleted_obj in line_items.deleted_objects:
                deleted_obj.delete()

            messages.success(
                self.request,
                f"Section '{form.instance.name}' and its line items updated successfully!",
            )
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_queryset(self):
        """Filter structures by the current project."""
        project = self.get_project()
        return Structure.objects.filter(project=project)

    def get_success_url(self):
        """Redirect to project's structure list."""
        project = self.get_project()
        return reverse(
            "bill_of_quantities:structure-list", kwargs={"project_pk": project.pk}
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        project = self.get_project()
        return [
            {
                "title": "Sections",
                "url": reverse(
                    "bill_of_quantities:structure-list",
                    kwargs={"project_pk": project.pk},
                ),
            },
            {"title": f"Edit {self.object.name}", "url": None},
        ]


class StructureDeleteView(
    SubscriptionAndRoleRequiredMixin,
    BreadcrumbMixin,
    DeleteView,
):
    """Delete a structure."""

    model = Structure
    template_name = "structure/structure_confirm_delete.html"
    roles = [Role.CONTRACT_BOQ]
    project_slug = "project_pk"
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]

    def get_queryset(self):
        """Filter structures by the current project."""
        return Structure.objects.filter(project=self.get_project())

    def form_valid(self, form):
        """Add success message."""
        structure_name = self.object.name
        messages.success(
            self.request, f"Section '{structure_name}' deleted successfully!"
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to project's structure list."""
        project = self.get_project()
        return reverse(
            "bill_of_quantities:structure-list", kwargs={"project_pk": project.pk}
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        project = self.get_project()
        return [
            {
                "title": "Sections",
                "url": reverse(
                    "bill_of_quantities:structure-list",
                    kwargs={"project_pk": project.pk},
                ),
            },
            {"title": f"Delete {self.object.name}", "url": None},
        ]


class StructureExcelUploadView(
    SubscriptionAndRoleRequiredMixin, BreadcrumbMixin, FormView
):
    """Upload structures from Excel file."""

    form_class = StructureExcelUploadForm
    template_name = "structure/structure_excel_upload.html"
    roles = [Role.CONTRACT_BOQ]
    project_slug = "project_pk"
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]

    def get_form_kwargs(self):
        """Pass user and project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["project"] = self.get_project()
        return kwargs

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        # Add validation errors if they exist in session
        if "upload_errors" in self.request.session:
            context["upload_errors"] = self.request.session.pop("upload_errors")
            context["error_count"] = self.request.session.pop("error_count", 0)
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        project = self.get_project()
        return [
            {
                "title": "Structures",
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {"title": "Upload Structures", "url": None},
        ]

    def clean_pd_data(self, value):
        """Clean pandas data: handle NaN, nan, and empty strings."""
        if pd.isna(value) or str(value).lower() == "nan":
            return ""
        return str(value).strip()

    def form_valid(self, form):
        """Process Excel file and create structures."""
        from app.BillOfQuantities.services import import_boq_from_excel

        excel_file = form.cleaned_data["excel_file"]
        project = self.get_project()

        created_count, errors = import_boq_from_excel(project, excel_file)

        if errors:
            # Parse errors into structured data for table display
            error_data = []
            for error in errors:
                if error.startswith("Row "):
                    parts = error.split(": ", 1)
                    row_num = parts[0].replace("Row ", "")
                    error_details = parts[1] if len(parts) > 1 else "Unknown error"
                    error_data.append({"row": row_num, "errors": error_details})
                else:
                    error_data.append({"row": "N/A", "errors": error})

            # Store errors in session to display in template
            self.request.session["upload_errors"] = error_data
            self.request.session["error_count"] = len(errors)
            return self.form_invalid(form)

        messages.success(
            self.request, f"Successfully uploaded {created_count} line item(s)!"
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to project's WBS detail view."""
        return reverse(
            "project:project-wbs-detail",
            kwargs={"pk": self.get_project().pk},
        )


class DownloadBOQTemplateView(SubscriptionAndRoleRequiredMixin, View):
    """View to download the BOQ excel/csv template file securely."""

    roles = [Role.CONTRACT_BOQ]
    project_slug = "project_pk"
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]

    def get(self, request, project_pk):
        """Handle GET request to download the BOQ excel template.

        Args:
            request (HttpRequest): The HTTP request object.
            project_pk (int): The primary key of the project.

        Returns:
            HttpResponse: FileResponse containing the excel template or a redirect with error message.
        """
        template_path = (
            Path(__file__).parent.parent / "data" / "Project set-up Template.xlsx"
        )

        if not template_path.exists():
            messages.error(request, "Template file not found.")
            return redirect(
                reverse(
                    "bill_of_quantities:structure-upload",
                    kwargs={"project_pk": project_pk},
                )
            )

        project = self.get_project()
        from django.utils import timezone

        current_date_time = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_project_name = "".join(
            c for c in project.name if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        filename = f"{safe_project_name} -project-setup -{current_date_time}.xlsx"

        response = FileResponse(open(template_path, "rb"), as_attachment=True)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        return response
