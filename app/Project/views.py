"""Views for Project app."""

from datetime import timedelta

from django.db.models import QuerySet, Sum
from django.db.models.functions import TruncMonth
from django.http import Http404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.BillOfQuantities.models import ActualTransaction, PaymentCertificate
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import ProjectForm
from app.Project.models import Project


class ProjectDashboardView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Projects dashboard showing financial metrics for all projects."""

    model = Project
    template_name = "project/project_dashboard.html"
    context_object_name = "projects"
    permissions = ["consultant", "contractor"]

    def get_breadcrumbs(self):
        return [
            {"title": "All Projects", "url": reverse("project:project-list")},
            {"title": "Projects Dashboard", "url": None},
        ]

    def get_queryset(self):
        """Get all projects for dashboard view."""
        if self.request.user.groups.filter(name="consultant").exists():  # type: ignore[attr-defined]
            return Project.objects.all().order_by("-created_at")
        return Project.objects.filter(account=self.request.user).order_by("-created_at")

    def get_context_data(self, **kwargs):
        """Add financial metrics to context."""
        context = super().get_context_data(**kwargs)
        projects = context["projects"]

        dashboard_data = []
        for project in projects:
            # Get contract value
            contract_value = project.get_total_contract_value

            # Get cumulative certified to date (sum of all approved payment certificates)
            certified_amount = (
                ActualTransaction.objects.filter(
                    line_item__project=project,
                    payment_certificate__status=PaymentCertificate.Status.APPROVED,
                ).aggregate(total=Sum("total_price"))["total"]
                or 0
            )

            # Get latest forecast to date
            latest_forecast = project.forecasts.order_by("-period").first()
            forecast_amount = 0
            if latest_forecast:
                forecast_amount = latest_forecast.total_forecast

            # Calculate percentages
            certified_percentage = 0
            forecast_percentage = 0
            if contract_value > 0:
                certified_percentage = (certified_amount / contract_value) * 100
                forecast_percentage = (forecast_amount / contract_value) * 100

            dashboard_data.append(
                {
                    "project": project,
                    "contract_value": contract_value,
                    "certified_amount": certified_amount,
                    "forecast_amount": forecast_amount,
                    "certified_percentage": certified_percentage,
                    "forecast_percentage": forecast_percentage,
                }
            )

        context["total_contract_value"] = sum_queryset(
            projects, "line_items__total_price"
        )
        context["total_certified_amount"] = sum_queryset(
            projects, "payment_certificates__actual_transactions__total_price"
        )
        context["total_forecast_amount"] = sum_queryset(
            projects, "forecasts__forecast_transactions__total_price"
        )
        context["dashboard_data"] = dashboard_data
        return context


class ProjectPerformanceReportView(
    UserHasGroupGenericMixin, BreadcrumbMixin, DetailView
):
    """Project performance report showing cumulative certified amounts month-by-month."""

    model = Project
    template_name = "project/project_performance_report.html"
    context_object_name = "project"
    permissions = ["consultant", "contractor"]

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:project-list")},
            {
                "title": "Project Details",
                "url": reverse("project:project-detail", kwargs={"pk": self.object.pk}),
            },
            {"title": f"{self.object.name} Performance Report", "url": None},
        ]

    def get_context_data(self, **kwargs):
        """Add performance data to context."""
        context = super().get_context_data(**kwargs)
        project = context["project"]

        # Get monthly certified amounts for last 12 months
        twelve_months_ago = timezone.now() - timedelta(days=365)
        monthly_data = (
            ActualTransaction.objects.filter(
                line_item__project=project,
                payment_certificate__status=PaymentCertificate.Status.APPROVED,
                payment_certificate__created_at__gte=twelve_months_ago,
            )
            .annotate(month=TruncMonth("payment_certificate__created_at"))
            .values("month")
            .annotate(monthly_total=Sum("total_price"))
            .order_by("month")
        )

        # Prepare data for Chart.js
        chart_labels = []
        monthly_amounts = []
        cumulative_amounts = []

        running_total = 0
        contract_value = float(project.get_total_contract_value)

        for item in monthly_data:
            month_label = item["month"].strftime("%b %Y")
            monthly_amount = float(item["monthly_total"] or 0)

            running_total += monthly_amount

            chart_labels.append(month_label)
            monthly_amounts.append(monthly_amount)
            cumulative_amounts.append(running_total)

        # Create contract value baseline (same value for all months)
        contract_baseline = [contract_value] * len(chart_labels)

        context.update(
            {
                "chart_labels": chart_labels,
                "monthly_amounts": monthly_amounts,
                "cumulative_amounts": cumulative_amounts,
                "contract_baseline": contract_baseline,
                "contract_value": contract_value,
                "total_certified": running_total,
                "performance_data": cumulative_amounts,  # Keep for summary section
            }
        )

        return context


class ProjectMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    permissions = ["contractor"]

    def get_queryset(self: "ProjectMixin") -> QuerySet[Project]:
        return Project.objects.filter(account=self.request.user).order_by("-created_at")

    def get_object(self: "ProjectMixin") -> Project:
        project = super().get_object()  # type: ignore
        if project.account != self.request.user:
            raise Http404("You do not have permission to view this project.")
        return project


class ProjectListView(ProjectMixin, ListView):
    """List all projects for the current user."""

    model = Project
    template_name = "project/project_list.html"
    context_object_name = "projects"
    paginate_by = 10

    def get_breadcrumbs(self):
        return [
            {"title": "All Projects", "url": None},
        ]

    def get_queryset(self: "ProjectListView") -> QuerySet[Project]:
        """Filter projects by current user and search query."""
        queryset = super().get_queryset()

        # Search filter
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset


class ProjectDetailView(ProjectMixin, DetailView):
    """Display a single project."""

    model = Project
    template_name = "project/project_detail.html"
    context_object_name = "project"

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:project-list")},
            {"title": f"{self.object.name} Details", "url": None},
        ]

    def get_context_data(self: "ProjectDetailView", **kwargs):
        """Add structures to context."""
        context = super().get_context_data(**kwargs)
        line_items = self.object.line_items.all()
        # Calculate total
        total = sum_queryset(line_items, "total_price")
        context["line_items_total"] = total

        return context


class ProjectWBSDetailView(ProjectMixin, DetailView):
    """Display project WBS/BOQ detailed view."""

    model = Project
    template_name = "project/project_detail_wbs.html"
    context_object_name = "project"

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:project-list")},
            {
                "title": "Project Details",
                "url": reverse("project:project-detail", kwargs={"pk": self.object.pk}),
            },
            {"title": f"{self.object.name} WBS", "url": None},
        ]

    def get_context_data(self, **kwargs):
        """Add line items total and filter options to context."""
        from django.db.models import Sum

        from app.BillOfQuantities.models import Bill, Package, Structure

        context = super().get_context_data(**kwargs)
        project: Project = self.get_object()

        # Get unique structures, bills, packages for dropdowns
        structures = Structure.objects.filter(project=project).distinct()
        bills = Bill.objects.filter(structure__project=project).distinct()
        packages = Package.objects.filter(bill__structure__project=project).distinct()

        # Get filter parameters
        structure_id = self.request.GET.get("structure")
        bill_id = self.request.GET.get("bill")
        package_id = self.request.GET.get("package")
        description = self.request.GET.get("description")

        # Filter line items
        all_line_items = project.get_line_items
        line_items = all_line_items.filter(special_item=False, addendum=False)
        special_items = all_line_items.filter(special_item=True, addendum=False)
        addendum_items = all_line_items.filter(addendum=True, special_item=False)
        if structure_id:
            bills = bills.filter(structure__id=structure_id)
            line_items = line_items.filter(structure_id=structure_id)
        if bill_id:
            packages = packages.filter(bill__id=bill_id)
            line_items = line_items.filter(bill_id=bill_id)
        if package_id:
            line_items = line_items.filter(package_id=package_id)
        if description:
            line_items = line_items.filter(description__icontains=description)

        # Calculate total of filtered line items
        line_items_total = line_items.aggregate(total=Sum("total_price"))["total"] or 0

        context["filtered_line_items"] = line_items
        context["line_items_total"] = line_items_total
        context["structures"] = structures
        context["bills"] = bills
        context["packages"] = packages
        context["special_items"] = special_items
        context["addendum_items"] = addendum_items

        return context


class ProjectCreateView(UserHasGroupGenericMixin, BreadcrumbMixin, CreateView):
    """Create a new project."""

    model = Project
    form_class = ProjectForm
    template_name = "project/project_form.html"
    permissions = ["contractor"]

    def get_breadcrumbs(self):
        return [
            {"title": "Return to Projects", "url": reverse("project:project-list")},
        ]

    def form_valid(self, form):
        """Set the account to the current user before saving."""
        form.instance.account = self.request.user
        return super().form_valid(form)

    def get_success_url(self: "ProjectCreateView"):
        """Redirect to the project list."""
        return reverse_lazy(
            "project:project-detail", kwargs={"pk": self.get_object().pk}
        )


class ProjectUpdateView(ProjectMixin, UpdateView):
    """Update an existing project."""

    model = Project
    form_class = ProjectForm
    template_name = "project/project_form.html"
    permissions = ["contractor"]

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:project-list")},
            {
                "title": "Return to Project Detail",
                "url": reverse("project:project-detail", kwargs={"pk": self.object.pk}),
            },
            {"title": f"Update: {self.object.name} Project", "url": None},
        ]

    def get_success_url(self):
        """Redirect to the project list."""
        return reverse_lazy("project:project-detail", kwargs={"pk": self.object.pk})


class ProjectDeleteView(ProjectMixin, DeleteView):
    """Delete a project."""

    model = Project
    template_name = "project/project_confirm_delete.html"
    success_url = reverse_lazy("project:project-list")

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:project-list")},
            {
                "title": "Return to Project Detail",
                "url": reverse("project:project-detail", kwargs={"pk": self.object.pk}),
            },
            {"title": f"Delete: {self.object.name} Project", "url": None},
        ]
