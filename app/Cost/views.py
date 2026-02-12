from collections import defaultdict
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from app.BillOfQuantities.models import Bill, Structure
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Cost.models import Cost
from app.Project.models import Project, Role

from .forms import CostForm, CostFormSet


class CostMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for cost views."""

    roles = [Role.USER]
    project_slug = "project_pk"
    bill = None

    def get_bill(self) -> Bill:
        """Get the bill for this view."""
        if not hasattr(self, "bill") or not self.bill:
            self.bill = get_object_or_404(Bill, pk=self.get_kwargs().get("bill_pk"))
        return self.bill

    def get_kwargs(self):
        """Get kwargs for the view."""
        return getattr(self, "kwargs", {})


class ProjectCostTreeView(CostMixin, DetailView):
    """Tree view showing costs grouped by structure and bill."""

    model = Project
    template_name = "Cost/project_cost_tree.html"
    context_object_name = "project"
    pk_url_kwarg = "project_pk"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {"title": "Costs", "url": None},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Build tree structure: structure -> bills -> costs
        tree: dict[Structure, dict[str, Any]] = defaultdict(
            lambda: {"bills": [], "total": 0}
        )

        structures = self.object.structures.prefetch_related("bills__costs").order_by(
            "name"
        )

        for structure in structures:
            bills_data = []
            structure_total = 0

            for bill in structure.bills.all():
                bill_total = sum_queryset(bill.costs, "gross")
                structure_total += bill_total

                bills_data.append(
                    {
                        "bill": bill,
                        "total": bill_total,
                        "cost_count": bill.costs.count(),
                    }
                )

            tree[structure] = {
                "bills": bills_data,
                "total": structure_total,
            }

        context["tree"] = dict(tree)
        context["grand_total"] = sum(data["total"] for data in tree.values())

        return context


class BillCostDetailView(CostMixin, ListView):
    """Detail view showing all costs for a specific bill."""

    model = Bill
    template_name = "Cost/bill_cost_detail.html"
    context_object_name = "costs"
    paginate_by = 20

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        bill = self.get_bill()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {
                "title": "Costs",
                "url": reverse(
                    "cost:project-cost-tree", kwargs={"project_pk": project.pk}
                ),
            },
            {"title": bill.name, "url": None},
        ]

    def get_queryset(self):
        queryset = self.get_bill().costs.order_by("-date", "-created_at")

        # Filter by search query
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(description__icontains=search)

        # Filter by date range
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset

    def get_context_data(self: "BillCostDetailView", **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        bill = self.get_bill()
        context["project"] = project
        context["structure"] = bill.structure
        context["bill"] = bill

        # Calculate totals
        costs = bill.costs
        context["gross"] = sum_queryset(costs, "gross")
        context["vat_amount"] = sum_queryset(costs, "vat_amount")
        context["net"] = sum_queryset(costs, "net")

        # Pass filter values back to template
        context["search"] = self.request.GET.get("search", "")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")

        return context


class BillCostCreateView(CostMixin, CreateView):
    """View to add new costs to a bill."""

    model = Cost
    form_class = CostForm
    template_name = "Cost/cost_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        bill = self.get_bill()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {
                "title": "Costs",
                "url": reverse(
                    "cost:project-cost-tree", kwargs={"project_pk": project.pk}
                ),
            },
            {
                "title": bill.name,
                "url": reverse(
                    "cost:bill-cost-detail",
                    kwargs={"project_pk": project.pk, "bill_pk": bill.pk},
                ),
            },
            {"title": "Add Cost", "url": None},
        ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["bill"] = self.get_bill()
        return kwargs

    def form_valid(self, form):
        form.instance.bill = self.get_bill()
        response = super().form_valid(form)
        messages.success(
            self.request, f"Cost '{form.instance.description}' added successfully."
        )
        return response

    def get_success_url(self):
        return reverse(
            "cost:bill-cost-detail",
            kwargs={
                "project_pk": self.get_project().pk,
                "bill_pk": self.get_bill().pk,
            },
        )

    def get_context_data(self, **kwargs):
        bill = self.get_bill()
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["bill"] = bill
        context["structure"] = bill.structure or None
        return context


class BillCostUpdateView(CostMixin, UpdateView):
    """View to edit an existing cost."""

    model = Cost
    form_class = CostForm
    template_name = "Cost/cost_form.html"
    pk_url_kwarg = "cost_pk"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        bill = self.get_bill()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {
                "title": "Costs",
                "url": reverse(
                    "cost:project-cost-tree", kwargs={"project_pk": project.pk}
                ),
            },
            {
                "title": bill.name,
                "url": reverse(
                    "cost:bill-cost-detail",
                    kwargs={"project_pk": project.pk, "bill_pk": bill.pk},
                ),
            },
            {"title": "Edit Cost", "url": None},
        ]

    def get_bill(self):
        return self.get_object().bill

    def dispatch(self, request, *args, **kwargs):
        # Get the cost object and validate bill belongs to project
        self.object = self.get_object()
        bill = self.object.bill

        if bill.structure.project != self.get_project():
            messages.error(
                request, "This cost does not belong to the selected project."
            )
            return redirect(
                "cost:project-cost-tree",
                project_pk=self.get_project().pk,
            )

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["bill"] = self.get_bill()
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f"Cost '{form.instance.description}' updated successfully."
        )
        return response

    def get_success_url(self):
        return reverse(
            "cost:bill-cost-detail",
            kwargs={
                "project_pk": self.get_project().pk,
                "bill_pk": self.get_bill().pk,
            },
        )

    def get_context_data(self, **kwargs):
        bill = self.get_bill()
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["bill"] = bill
        context["structure"] = bill.structure or None
        context["is_edit"] = True
        return context


class BillCostDeleteView(CostMixin, View):
    """View to delete a cost."""

    def post(self, request, *args, **kwargs):
        # Get the cost object
        cost = get_object_or_404(Cost, pk=kwargs.get("cost_pk"))
        bill = cost.bill

        # Validate bill belongs to project
        if bill.structure.project != self.get_project():
            messages.error(
                request, "This cost does not belong to the selected project."
            )
            return redirect(
                "cost:project-cost-tree",
                project_pk=self.get_project().pk,
            )

        # Store description before deleting
        cost_description = cost.description

        # Delete the cost
        cost.delete()

        messages.success(request, f"Cost '{cost_description}' deleted successfully.")

        return redirect(
            "cost:bill-cost-detail",
            project_pk=self.get_project().pk,
            bill_pk=bill.pk,
        )

    def get_bill(self):
        cost = get_object_or_404(Cost, pk=self.kwargs.get("cost_pk"))
        return cost.bill


class BillCostFormSetView(CostMixin, View):
    """View to add multiple costs using a formset."""

    template_name = "Cost/cost_formset.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        bill = self.get_bill()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {
                "title": "Costs",
                "url": reverse(
                    "cost:project-cost-tree", kwargs={"project_pk": project.pk}
                ),
            },
            {
                "title": bill.name,
                "url": reverse(
                    "cost:bill-cost-detail",
                    kwargs={"project_pk": project.pk, "bill_pk": bill.pk},
                ),
            },
            {"title": "Add Multiple Costs", "url": None},
        ]

    def get(self, request, *args, **kwargs):
        # Get bill and validate it belongs to project
        bill = self.get_bill()
        if bill.structure.project != self.get_project():
            messages.error(
                request, "This bill does not belong to the selected project."
            )
            return redirect(
                "cost:project-cost-tree",
                project_pk=self.get_project().pk,
            )

        formset = CostFormSet(bill=bill)
        return render(
            request,
            self.template_name,
            {
                "formset": formset,
                "project": self.get_project(),
                "bill": bill,
                "structure": bill.structure,
            },
        )

    def post(self, request, *args, **kwargs):
        # Get bill and validate it belongs to project
        bill = self.get_bill()
        if bill.structure.project != self.get_project():
            messages.error(
                request, "This bill does not belong to the selected project."
            )
            return redirect(
                "cost:project-cost-tree",
                project_pk=self.get_project().pk,
            )

        formset = CostFormSet(request.POST, bill=bill)

        if formset.is_valid():
            costs = []
            for form in formset:
                if (
                    form.is_valid()
                    and form.cleaned_data
                    and not form.cleaned_data.get("DELETE")
                ):
                    # Skip empty forms
                    if not form.cleaned_data.get("description"):
                        continue

                    # Save without committing to avoid model save method issues
                    cost = form.save(commit=False)
                    cost.bill = bill

                    # Pre-calculate all fields before save
                    # The model's save() will recalculate but that's fine since bill is now set
                    cost.gross = cost.quantity * cost.unit_price
                    if bill.structure.project.vat:
                        cost.vat_amount = cost.gross * settings.VAT_RATE
                        cost.vat = True
                    else:
                        cost.vat_amount = Decimal("0")
                        cost.vat = False
                    cost.net = cost.gross + cost.vat_amount

                    # Save normally - model's save() will handle timestamps
                    cost.save()
                    costs.append(cost.description)

            if costs:
                messages.success(
                    request,
                    f"Successfully added {len(costs)} cost(s): {', '.join(costs)}",
                )
            else:
                messages.info(request, "No costs were added.")

            return redirect(
                "cost:bill-cost-detail",
                project_pk=self.get_project().pk,
                bill_pk=bill.pk,
            )
        else:
            # If formset is invalid, re-render with errors
            return render(
                request,
                self.template_name,
                {
                    "formset": formset,
                    "project": self.get_project(),
                    "bill": bill,
                    "structure": bill.structure,
                },
            )
