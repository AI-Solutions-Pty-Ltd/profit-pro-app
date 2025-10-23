from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from app.BillOfQuantities.models import Bill
from app.Cost.models import Cost
from app.Project.models import Project

from .forms import CostForm


class ProjectAccessMixin(LoginRequiredMixin):
    """Mixin to ensure user has access to the project."""

    bill = None
    project = None

    def get_bill(self):
        if not hasattr(self, "bill") or not self.bill:
            self.bill = get_object_or_404(Bill, pk=self.kwargs.get("bill_pk"))
        return self.bill

    def dispatch(self, request, *args, **kwargs):
        project_pk = kwargs.get("project_pk")
        self.project = get_object_or_404(Project, pk=project_pk)

        # Check if user is linked to the project
        if self.project.account != request.user:
            messages.error(
                request, "You do not have permission to access this project."
            )
            return redirect("project:project-list")

        return super().dispatch(request, *args, **kwargs)


class ProjectCostTreeView(ProjectAccessMixin, DetailView):
    """Tree view showing costs grouped by structure and bill."""

    model = Project
    template_name = "cost/project_cost_tree.html"
    context_object_name = "project"
    pk_url_kwarg = "project_pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Build tree structure: structure -> bills -> costs
        tree = defaultdict(lambda: {"bills": [], "total": 0})

        structures = self.object.structures.prefetch_related("bills__costs").order_by(
            "name"
        )

        for structure in structures:
            bills_data = []
            structure_total = 0

            for bill in structure.bills.all():
                bill_total = bill.costs.aggregate(total=Sum("total"))["total"] or 0
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

    model = Cost
    template_name = "cost/bill_cost_detail.html"
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
            return redirect("cost:project-cost-tree", project_pk=self.project.pk)

        return response

    def get_queryset(self):
        queryset = Cost.objects.filter(bill=self.get_bill()).order_by(
            "-date", "-created_at"
        )

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["bill"] = self.get_bill()
        context["structure"] = self.get_bill().structure

        # Calculate totals
        costs = self.get_queryset()
        context["total_amount"] = costs.aggregate(total=Sum("amount"))["total"] or 0
        context["total_with_vat"] = costs.aggregate(total=Sum("total"))["total"] or 0
        context["cost_count"] = costs.count()

        # Pass filter values back to template
        context["search"] = self.request.GET.get("search", "")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")

        return context


class BillCostCreateView(ProjectAccessMixin, CreateView):
    """View to add new costs to a bill."""

    model = Cost
    form_class = CostForm
    template_name = "cost/cost_form.html"

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
            return redirect("cost:project-cost-tree", project_pk=self.project.pk)

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
                "project_pk": self.project.pk,
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
    template_name = "cost/cost_form.html"
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
            return redirect("cost:project-cost-tree", project_pk=self.project.pk)

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
                "project_pk": self.project.pk,
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
