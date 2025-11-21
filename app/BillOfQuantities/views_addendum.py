"""Views for managing addendum line items."""

from django.contrib import messages
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.BillOfQuantities.models import Bill, LineItem, Structure
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Project


class AddendumMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    """Mixin for addendum views."""

    permissions = ["contractor"]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        """Get the project for the current view."""
        if not hasattr(self, "project") or not self.project:
            self.project = get_object_or_404(
                Project,
                pk=self.kwargs[self.project_slug],
                account=self.request.user,
            )
        return self.project


class AddendumListView(AddendumMixin, ListView):
    """List all addendum items for a project."""

    model = LineItem
    template_name = "addendum/addendum_list.html"
    context_object_name = "addendum_items"

    def get_breadcrumbs(self: "AddendumListView", **kwargs) -> list[BreadcrumbItem]:
        return [
            {
                "title": "Return to Project",
                "url": reverse(
                    "project:project-detail",
                    kwargs={"pk": self.get_project().pk},
                ),
            },
            {
                "title": "Addendum List",
                "url": None,
            },
        ]

    def get_queryset(self: "AddendumListView"):
        """Get addendum items for the project."""
        project = self.get_project()
        return (
            LineItem.objects.filter(project=project, addendum=True)
            .select_related("structure", "bill", "package")
            .order_by("row_index")
        )

    def get_context_data(self: "AddendumListView", **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class AddendumCreateView(AddendumMixin, CreateView):
    """Create a new addendum item."""

    model = LineItem
    template_name = "addendum/addendum_form.html"
    fields = [
        "structure",
        "bill",
        "package",
        "item_number",
        "payment_reference",
        "description",
        "is_work",
        "unit_measurement",
        "unit_price",
        "budgeted_quantity",
    ]

    def get_breadcrumbs(self: "AddendumCreateView", **kwargs) -> list[BreadcrumbItem]:
        return [
            {
                "title": "Return to Project",
                "url": reverse(
                    "project:project-detail",
                    kwargs={"pk": self.get_project().pk},
                ),
            },
            {
                "title": "Add Addendum Item",
                "url": None,
            },
        ]

    def get_form(self: "AddendumCreateView", form_class=None):
        """Filter structure and bill choices to current project."""
        form = super().get_form(form_class)
        project = self.get_project()

        # Filter structure to current project
        form.fields["structure"].queryset = Structure.objects.filter(project=project)
        form.fields["structure"].required = True

        # Filter bill to current project's structures
        form.fields["bill"].queryset = Bill.objects.filter(structure__project=project)
        form.fields["bill"].required = True

        # Filter package to current project's bills
        from app.BillOfQuantities.models import Package

        form.fields["package"].queryset = Package.objects.filter(
            bill__structure__project=project
        )
        form.fields["package"].required = False

        return form

    def form_valid(self: "AddendumCreateView", form):
        """Set project, addendum flag, and calculate row_index."""
        project = self.get_project()
        form.instance.project = project
        form.instance.addendum = True

        # Calculate row_index: start where normal line items end
        max_row_index = (
            LineItem.objects.filter(project=project).aggregate(Max("row_index"))[
                "row_index__max"
            ]
            or 0
        )
        form.instance.row_index = max_row_index + 1

        # Calculate total_price if is_work
        if form.instance.is_work:
            form.instance.total_price = (
                form.instance.unit_price * form.instance.budgeted_quantity
            )
        else:
            form.instance.total_price = 0

        messages.success(self.request, "Addendum item created successfully!")
        return super().form_valid(form)

    def get_success_url(self: "AddendumCreateView"):
        """Redirect to addendum list."""
        return reverse(
            "bill_of_quantities:addendum-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self: "AddendumCreateView", **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class AddendumUpdateView(AddendumMixin, UpdateView):
    """Update an existing addendum item."""

    model = LineItem
    template_name = "addendum/addendum_form.html"
    fields = [
        "structure",
        "bill",
        "package",
        "item_number",
        "payment_reference",
        "description",
        "is_work",
        "unit_measurement",
        "unit_price",
        "budgeted_quantity",
    ]

    def get_breadcrumbs(self: "AddendumUpdateView", **kwargs) -> list[BreadcrumbItem]:
        return [
            {
                "title": "Return to Project",
                "url": reverse(
                    "project:project-detail",
                    kwargs={"pk": self.get_project().pk},
                ),
            },
            {
                "title": "Update Addendum Item",
                "url": None,
            },
        ]

    def get_queryset(self: "AddendumUpdateView"):
        """Only allow editing addendum items from this project."""
        project = self.get_project()
        return LineItem.objects.filter(project=project, addendum=True)

    def get_form(self: "AddendumUpdateView", form_class=None):
        """Filter structure and bill choices to current project."""
        form = super().get_form(form_class)
        project = self.get_project()

        # Filter structure to current project
        form.fields["structure"].queryset = Structure.objects.filter(project=project)
        form.fields["structure"].required = True

        # Filter bill to current project's structures
        form.fields["bill"].queryset = Bill.objects.filter(structure__project=project)
        form.fields["bill"].required = True

        # Filter package to current project's bills
        from app.BillOfQuantities.models import Package

        form.fields["package"].queryset = Package.objects.filter(
            bill__structure__project=project
        )
        form.fields["package"].required = False

        return form

    def form_valid(self: "AddendumUpdateView", form):
        """Recalculate total_price if is_work."""
        if form.instance.is_work:
            form.instance.total_price = (
                form.instance.unit_price * form.instance.budgeted_quantity
            )
        else:
            form.instance.total_price = 0

        messages.success(self.request, "Addendum item updated successfully!")
        return super().form_valid(form)

    def get_success_url(self: "AddendumUpdateView"):
        """Redirect to addendum list."""
        return reverse(
            "bill_of_quantities:addendum-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self: "AddendumUpdateView", **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class AddendumDeleteView(AddendumMixin, DeleteView):
    """Delete an addendum item."""

    model = LineItem
    template_name = "addendum/addendum_confirm_delete.html"
    context_object_name = "addendum_item"

    def get_breadcrumbs(self: "AddendumDeleteView", **kwargs) -> list[BreadcrumbItem]:
        return [
            {
                "title": "Return to Project",
                "url": reverse(
                    "project:project-detail",
                    kwargs={"pk": self.get_project().pk},
                ),
            },
            {
                "title": "Delete Addendum Item",
                "url": None,
            },
        ]

    def get_queryset(self: "AddendumDeleteView"):
        """Only allow deleting addendum items from this project."""
        project = self.get_project()
        return LineItem.objects.filter(project=project, addendum=True)

    def form_valid(self: "AddendumDeleteView", form):
        """Soft delete the addendum item."""
        self.object.soft_delete()
        messages.success(self.request, "Addendum item deleted successfully!")
        return redirect(self.get_success_url())

    def get_success_url(self: "AddendumDeleteView"):
        """Redirect to addendum list."""
        return reverse(
            "bill_of_quantities:addendum-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self: "AddendumDeleteView", **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
