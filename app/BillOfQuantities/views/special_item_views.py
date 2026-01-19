"""Views for managing special line items."""

from django.contrib import messages
from django.db.models import Max
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.BillOfQuantities.models import LineItem
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Project


class SpecialItemMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    """Mixin for special item views."""

    permissions = ["contractor"]
    project_slug = "project_pk"

    def get_project(self):
        """Get the project for the current view."""
        if not hasattr(self, "project") or not self.project:
            self.project = get_object_or_404(
                Project,
                pk=self.kwargs[self.project_slug],
                users=self.request.user,
            )
        return self.project


class SpecialItemListView(SpecialItemMixin, ListView):
    """List all special items for a project."""

    model = LineItem
    template_name = "special_item/special_item_list.html"
    context_object_name = "special_items"

    def get_breadcrumbs(self: "SpecialItemListView") -> list[BreadcrumbItem]:
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": self.get_project().name,
                "url": reverse(
                    "project:project-management",
                    kwargs={"pk": self.get_project().pk},
                ),
            },
            {
                "title": "Special Items",
                "url": None,
            },
        ]

    def get_queryset(self: "SpecialItemListView") -> QuerySet[LineItem]:
        """Get special items for the project."""
        project = self.get_project()
        return (
            LineItem.objects.filter(project=project, special_item=True, addendum=False)
            .select_related("structure", "bill", "package")
            .order_by("row_index")
        )

    def get_context_data(self: "SpecialItemListView", **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SpecialItemCreateView(SpecialItemMixin, CreateView):
    """Create a new special item."""

    model = LineItem
    template_name = "special_item/special_item_form.html"
    fields = [
        "description",
    ]

    def get_form(self, form_class=None):
        """Override form to make description required."""
        form = super().get_form(form_class)
        # Make description field required
        form.fields["description"].required = True
        return form

    def get_breadcrumbs(self: "SpecialItemCreateView") -> list[BreadcrumbItem]:
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": self.get_project().name,
                "url": reverse(
                    "project:project-management",
                    kwargs={"pk": self.get_project().pk},
                ),
            },
            {
                "title": "Special Items",
                "url": reverse(
                    "bill_of_quantities:special-item-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            },
            {
                "title": "Create Special Item",
                "url": None,
            },
        ]

    def form_valid(self: "SpecialItemCreateView", form):
        """Set project, special_item flag, and calculate row_index."""
        project = self.get_project()
        form.instance.project = project
        form.instance.special_item = True

        # Leave structure and bill FKs blank/null (as per requirement #1)
        form.instance.structure = None
        form.instance.bill = None
        form.instance.package = None
        form.instance.unit_price = 0
        form.instance.budgeted_quantity = 0
        form.instance.total_price = 0

        # Calculate row_index: start where normal line items end (requirement #2)
        max_row_index = (
            LineItem.objects.filter(project=project).aggregate(Max("row_index"))[
                "row_index__max"
            ]
            or 0
        )
        form.instance.row_index = max_row_index + 1

        messages.success(self.request, "Special item created successfully!")
        return super().form_valid(form)

    def get_success_url(self: "SpecialItemCreateView"):
        """Redirect to special item list."""
        return reverse(
            "bill_of_quantities:special-item-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self: "SpecialItemCreateView", **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SpecialItemUpdateView(SpecialItemMixin, UpdateView):
    """Update an existing special item."""

    model = LineItem
    template_name = "special_item/special_item_form.html"
    fields = [
        "description",
    ]

    def get_form(self, form_class=None):
        """Override form to make description required."""
        form = super().get_form(form_class)
        # Make description field required
        form.fields["description"].required = True
        return form

    def get_breadcrumbs(self: "SpecialItemUpdateView") -> list[BreadcrumbItem]:
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": self.get_project().name,
                "url": reverse(
                    "project:project-management",
                    kwargs={"pk": self.get_project().pk},
                ),
            },
            {
                "title": "Special Items",
                "url": reverse(
                    "bill_of_quantities:special-item-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            },
            {
                "title": self.get_object().description,
                "url": None,
            },
        ]

    def get_queryset(self: "SpecialItemUpdateView") -> QuerySet[LineItem]:
        """Only allow editing special items from this project."""
        project = self.get_project()
        return LineItem.objects.filter(project=project, special_item=True)

    def form_valid(self: "SpecialItemUpdateView", form):
        """Recalculate total_price if is_work."""
        messages.success(self.request, "Special item updated successfully!")
        return super().form_valid(form)

    def get_success_url(self: "SpecialItemUpdateView"):
        """Redirect to special item list."""
        return reverse(
            "bill_of_quantities:special-item-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self: "SpecialItemUpdateView", **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SpecialItemDeleteView(SpecialItemMixin, DeleteView):
    """Delete a special item."""

    model = LineItem
    template_name = "special_item/special_item_confirm_delete.html"
    context_object_name = "special_item"

    def get_breadcrumbs(self: "SpecialItemDeleteView") -> list[BreadcrumbItem]:
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": self.get_project().name,
                "url": reverse(
                    "project:project-management",
                    kwargs={"pk": self.get_project().pk},
                ),
            },
            {
                "title": "Special Items",
                "url": reverse(
                    "bill_of_quantities:special-item-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            },
            {
                "title": self.get_object().description,
                "url": None,
            },
        ]

    def get_queryset(self: "SpecialItemDeleteView") -> QuerySet[LineItem]:
        """Only allow deleting special items from this project."""
        project = self.get_project()
        return LineItem.objects.filter(project=project, special_item=True)

    def form_valid(self: "SpecialItemDeleteView", form):
        """Soft delete the special item."""
        self.object.soft_delete()
        messages.success(self.request, "Special item deleted successfully!")
        return redirect(self.get_success_url())

    def get_success_url(self: "SpecialItemDeleteView"):
        """Redirect to special item list."""
        return reverse(
            "bill_of_quantities:special-item-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self: "SpecialItemDeleteView", **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
