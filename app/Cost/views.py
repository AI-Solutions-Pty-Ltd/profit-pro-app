from collections import defaultdict
from typing import Any, cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from app.Account.models import Account
from app.BillOfQuantities.models import Bill, Structure
from app.core.Utilities.models import sum_queryset
from app.Cost.models import Cost
from app.Project.models import Project

from .forms import CostForm, CostFormSet


class ProjectAccessMixin(LoginRequiredMixin):
    """Mixin to ensure user has access to the project."""

    bill = None
    project: Project | None = None

    def get_bill(self) -> Bill:
        if not hasattr(self, "bill") or not self.bill:
            self.bill = get_object_or_404(Bill, pk=self.kwargs.get("bill_pk"))  # type: ignore
        return self.bill

    def get_project(self) -> Project:
        if not hasattr(self, "project") or not self.project:
            self.project = get_object_or_404(Project, pk=self.kwargs.get("project_pk"))  # type: ignore
        return self.project

    def dispatch(self: "ProjectAccessMixin", request, *args, **kwargs):
        self.project = self.get_project()

        # Check if user is linked to the project
        user: Account = cast(Account, request.user)
        if user not in self.project.users.all():
            messages.error(
                request, "You do not have permission to access this project."
            )
            return redirect("project:portfolio-dashboard")

        return super().dispatch(request, *args, **kwargs)


class ProjectCostTreeView(ProjectAccessMixin, DetailView):
    """Tree view showing costs grouped by structure and bill."""

    model = Project
    template_name = "Cost/project_cost_tree.html"
    context_object_name = "project"
    pk_url_kwarg = "project_pk"

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


class BillCostDetailView(ProjectAccessMixin, ListView):
    """Detail view showing all costs for a specific bill."""

    model = Bill
    template_name = "Cost/bill_cost_detail.html"
    context_object_name = "costs"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        # Call parent dispatch first to set self.project
        response = super().dispatch(request, *args, **kwargs)

        # Get and validate bill
        self.bill = self.get_bill()

        # Ensure bill belongs to project
        if self.bill.structure.project != self.project:
            messages.error(
                request, "This bill does not belong to the selected project."
            )
            return redirect(
                "cost:project-cost-tree",
                project_pk=self.project.pk if self.project else "",
            )

        return response

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
        context["project"] = self.get_project()
        context["structure"] = self.get_bill().structure
        context["bill"] = self.get_bill()

        # Calculate totals
        costs = self.get_bill().costs
        context["gross"] = sum_queryset(costs, "gross")
        context["vat_amount"] = sum_queryset(costs, "vat_amount")
        context["net"] = sum_queryset(costs, "net")

        # Pass filter values back to template
        context["search"] = self.request.GET.get("search", "")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")

        return context


class BillCostCreateView(ProjectAccessMixin, CreateView):
    """View to add new costs to a bill."""

    model = Cost
    form_class = CostForm
    template_name = "Cost/cost_form.html"

    def dispatch(self, request, *args, **kwargs):
        # Call parent dispatch first to set self.project
        response = super().dispatch(request, *args, **kwargs)

        # Get and validate bill
        self.bill = self.get_bill()

        # Ensure bill belongs to project
        if self.bill.structure.project != self.project:
            messages.error(
                request, "This bill does not belong to the selected project."
            )
            return redirect(
                "cost:project-cost-tree",
                project_pk=self.project.pk if self.project else "",
            )

        return response

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
                "project_pk": self.project.pk if self.project else "",
                "bill_pk": self.get_bill().pk,
            },
        )

    def get_context_data(self, **kwargs):
        bill = self.get_bill()
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["bill"] = bill
        context["structure"] = bill.structure or None
        return context


class BillCostUpdateView(ProjectAccessMixin, UpdateView):
    """View to edit an existing cost."""

    model = Cost
    form_class = CostForm
    template_name = "Cost/cost_form.html"
    pk_url_kwarg = "cost_pk"

    def get_bill(self):
        return self.get_object().bill

    def dispatch(self, request, *args, **kwargs):
        # Call parent dispatch first to set self.project
        response = super().dispatch(request, *args, **kwargs)

        # Get the cost object
        self.object = self.get_object()

        # Get and validate bill
        self.bill = self.get_bill()

        # Ensure bill belongs to project
        if self.bill.structure.project != self.project:
            messages.error(
                request, "This cost does not belong to the selected project."
            )
            return redirect(
                "cost:project-cost-tree",
                project_pk=self.project.pk if self.project else "",
            )

        return response

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
                "project_pk": self.project.pk if self.project else "",
                "bill_pk": self.get_bill().pk,
            },
        )

    def get_context_data(self, **kwargs):
        bill = self.get_bill()
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["bill"] = bill
        context["structure"] = bill.structure or None
        context["is_edit"] = True
        return context


class BillCostFormSetView(ProjectAccessMixin, View):
    """View to add multiple costs using a formset."""

    template_name = "Cost/cost_formset.html"

    def dispatch(self: "BillCostFormSetView", request, *args, **kwargs):
        # Call parent dispatch first to set self.project
        response = super().dispatch(request, *args, **kwargs)

        # Get and validate bill
        self.bill = self.get_bill()

        # Ensure bill belongs to project
        if self.bill.structure.project != self.project:
            messages.error(
                request, "This bill does not belong to the selected project."
            )
            return redirect(
                "cost:project-cost-tree",
                project_pk=self.project.pk if self.project else "",
            )

        return response

    def get(self, request, *args, **kwargs):
        formset = CostFormSet(bill=self.get_bill())
        return render(
            request,
            self.template_name,
            {
                "formset": formset,
                "project": self.project,
                "bill": self.get_bill(),
                "structure": self.get_bill().structure,
            },
        )

    def post(self, request, *args, **kwargs):
        bill = self.get_bill()
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

                    cost = form.save(commit=False)
                    cost.bill = bill
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
                project_pk=self.project.pk if self.project else "",
                bill_pk=bill.pk,
            )
        else:
            # If formset is invalid, re-render with errors
            return render(
                request,
                self.template_name,
                {
                    "formset": formset,
                    "project": self.project,
                    "bill": bill,
                    "structure": bill.structure,
                },
            )
