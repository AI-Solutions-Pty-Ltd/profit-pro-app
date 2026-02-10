"""Views for Structure app."""

import pandas as pd
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import (
    DeleteView,
    DetailView,
    UpdateView,
)
from django.views.generic.edit import FormView

from app.BillOfQuantities.forms import (
    LineItemExcelUploadForm,
    StructureExcelUploadForm,
    StructureForm,
)
from app.BillOfQuantities.models import Bill, LineItem, Package, Structure
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role


class StructureDetailView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, DetailView):
    """Display a single structure."""

    model = Structure
    template_name = "structure/structure_detail.html"
    context_object_name = "structure"
    roles = [Role.CONTRACT_BOQ]
    project_slug = "pk"

    def get_queryset(self):
        """Filter structures by the current project."""
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        self.project = project
        return Structure.objects.filter(project=project).select_related("project")

    def test_func(self):
        """Check user has project role."""
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        return self.request.user.has_project_role(project, self.roles)  # type: ignore

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Structures",
                "url": reverse(
                    "project:project-management", kwargs={"pk": self.project.pk}
                ),
            },
            {"title": self.object.name, "url": None},
        ]


class StructureUpdateView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, UpdateView):
    """Update an existing structure."""

    model = Structure
    form_class = StructureForm
    template_name = "structure/structure_form.html"
    roles = [Role.CONTRACT_BOQ]
    project_slug = "pk"

    def form_valid(self, form):
        """Add success message."""
        messages.success(
            self.request, f"Structure '{form.instance.name}' updated successfully!"
        )
        return super().form_valid(form)

    def get_queryset(self):
        """Filter structures by the current project."""
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        self.project = project
        return Structure.objects.filter(project=project)

    def test_func(self):
        """Check user has project role."""
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        return self.request.user.has_project_role(project, self.roles)  # type: ignore

    def get_success_url(self):
        """Redirect to project's structure list."""
        return reverse("project:project-management", kwargs={"pk": self.project.pk})

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Structures",
                "url": reverse(
                    "project:project-management", kwargs={"pk": self.project.pk}
                ),
            },
            {"title": f"Edit {self.object.name}", "url": None},
        ]


class StructureDeleteView(UserHasProjectRoleGenericMixin, BreadcrumbMixin, DeleteView):
    """Delete a structure."""

    model = Structure
    template_name = "structure/structure_confirm_delete.html"
    roles = [Role.CONTRACT_BOQ]
    project_slug = "pk"

    def get_queryset(self):
        """Filter structures by the current project."""
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        self.project = project
        return Structure.objects.filter(project=project)

    def test_func(self):
        """Check user has project role."""
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        return self.request.user.has_project_role(project, self.roles)  # type: ignore

    def form_valid(self, form):
        """Add success message."""
        structure_name = self.object.name
        messages.success(
            self.request, f"Structure '{structure_name}' deleted successfully!"
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to project's structure list."""
        return reverse("project:project-management", kwargs={"pk": self.project.pk})

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Get breadcrumb navigation."""
        return [
            {
                "title": "Structures",
                "url": reverse(
                    "project:project-management", kwargs={"pk": self.project.pk}
                ),
            },
            {"title": f"Delete {self.object.name}", "url": None},
        ]


class StructureExcelUploadView(
    UserHasProjectRoleGenericMixin, BreadcrumbMixin, FormView
):
    """Upload structures from Excel file."""

    form_class = StructureExcelUploadForm
    template_name = "structure/structure_excel_upload.html"
    roles = [Role.CONTRACT_BOQ]
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL."""
        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        return project

    def get_form_kwargs(self):
        """Pass user and project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["project"] = self.get_project()
        return kwargs

    def test_func(self):
        """Check user has project role."""
        project = self.get_project()
        return self.request.user.has_project_role(project, self.roles)  # type: ignore

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
        excel_file = form.cleaned_data["excel_file"]
        project = self.get_project()

        try:
            # Check number of sheets in Excel file
            excel_file_obj = pd.ExcelFile(excel_file)
            sheet_names = excel_file_obj.sheet_names

            if len(sheet_names) > 1:
                messages.error(
                    self.request,
                    f"Excel file must contain only one sheet. Found {len(sheet_names)} sheets: {', '.join(sheet_names)}",
                )
                return self.form_invalid(form)

            # Read the single sheet
            df = pd.read_excel(excel_file_obj, sheet_name=0)
        except Exception as e:
            messages.error(
                self.request,
                f"Error reading Excel file: {str(e)}",
            )
            return self.form_invalid(form)

        try:
            # Validate required columns
            columns = [
                "Structure",  # structure name
                "Bill No.",  # bill name
                "Package",  # package name
                "Item No.",  # item_number
                "Pay Ref",  # payment_reference
                "Description",  # description
                "Unit",  # unit_measurement
                "Contract Quantity",  # budgeted_quantity
                "Contract Rate",  # unit_price
                "Contract Amount",  # total_price
            ]
            for column in columns:
                if column not in df.columns:
                    messages.error(
                        self.request,
                        f"Excel file must contain a '{column}' column.",
                    )
                    return self.form_invalid(form)

            # Collect all validation errors before saving
            errors = []
            valid_forms = []

            for row_index, row in df.iterrows():
                # Excel rows are 1-indexed, and we add 2 to account for header row
                display_row = int(str(row_index)) + 1

                try:
                    structure = self.clean_pd_data(row["Structure"])
                    bill = self.clean_pd_data(row["Bill No."])
                    package = self.clean_pd_data(row["Package"])
                    item_number = self.clean_pd_data(row["Item No."])
                    payment_reference = self.clean_pd_data(row["Pay Ref"])
                    description = self.clean_pd_data(row["Description"])
                    unit_measurement = self.clean_pd_data(row["Unit"])
                    budgeted_quantity = self.clean_pd_data(row["Contract Quantity"])
                    unit_price = self.clean_pd_data(row["Contract Rate"])
                    total_price = self.clean_pd_data(row["Contract Amount"])

                    if budgeted_quantity.lower().strip() == "rate only":
                        budgeted_quantity = 0
                        unit_price = 0
                        total_price = 0

                    data = {
                        "project": project,
                        "structure": structure,
                        "bill": bill,
                        "package": package,
                        "row_index": row_index,
                        "item_number": item_number,
                        "payment_reference": payment_reference,
                        "description": description,
                        "unit_measurement": unit_measurement,
                        "budgeted_quantity": round(float(budgeted_quantity), 2)
                        if budgeted_quantity
                        else 0,
                        "unit_price": round(float(unit_price), 2)
                        if unit_price
                        else 0.0,
                        "total_price": round(float(total_price), 2)
                        if total_price
                        else 0.0,
                    }
                    if not data["package"]:
                        del data["package"]

                    line_item_form = LineItemExcelUploadForm(data=data)
                    if line_item_form.is_valid():
                        valid_forms.append(line_item_form)
                    else:
                        # Format errors for this row
                        row_errors = []
                        for field, field_errors in line_item_form.errors.items():
                            for error in field_errors:
                                row_errors.append(f"{field}: {error}")
                        errors.append(f"Row {display_row}: {'; '.join(row_errors)}")

                except (ValueError, TypeError) as e:
                    errors.append(
                        f"Row {display_row}: Data conversion error - {str(e)}"
                    )

            # If there are any errors, show them all and don't save anything
            if errors:
                # Parse errors into structured data for table display
                error_data = []
                for error in errors:
                    # Extract row number and error details
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

            # no errors, erase previous structures, bills, packages and line items
            Structure.objects.filter(project=project).delete()
            Bill.objects.filter(structure__project=project).delete()
            Package.objects.filter(bill__structure__project=project).delete()
            LineItem.objects.filter(structure__project=project).delete()

            # All validations passed - save everything in a transaction
            with transaction.atomic():
                created_count = 0
                for idx, line_item_form in enumerate(valid_forms):
                    line_item_form.save(row_index=idx)
                    created_count += 1

            messages.success(
                self.request, f"Successfully uploaded {created_count} line item(s)!"
            )
            return redirect(self.get_success_url())

        except Exception as e:
            messages.error(
                self.request,
                f"Error processing Excel file: {str(e)}",
            )
            return self.form_invalid(form)

    def get_success_url(self):
        """Redirect to project's structure list."""
        return reverse(
            "project:project-management",
            kwargs={"pk": self.get_project().pk},
        )
