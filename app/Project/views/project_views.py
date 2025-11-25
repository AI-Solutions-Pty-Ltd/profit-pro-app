"""Views for Project app."""

import json
from datetime import datetime, timedelta
from typing import cast

from django.db.models import QuerySet, Sum
from django.http import Http404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.Account.models import Account
from app.BillOfQuantities.models import ActualTransaction, PaymentCertificate
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import FilterForm, ProjectForm
from app.Project.models import Project


class ProjectMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    permissions = ["contractor"]

    def get_queryset(self: "ProjectMixin") -> QuerySet[Project]:
        return Project.objects.filter(account=self.request.user).order_by("-created_at")

    def get_object(self: "ProjectMixin") -> Project:
        project = super().get_object()  # type: ignore
        if project.account != self.request.user:
            raise Http404("You do not have permission to view this project.")
        return project


class ProjectDashboardView(UserHasGroupGenericMixin, BreadcrumbMixin, ListView):
    """Projects dashboard showing financial metrics for all projects."""

    model = Project
    template_name = "project/project_dashboard.html"
    context_object_name = "projects"
    permissions = ["consultant", "contractor"]

    filter_form: FilterForm | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filter_form = None

    def setup(self, request, *args, **kwargs):
        """Initialize filter form during view setup."""
        super().setup(request, *args, **kwargs)
        self.filter_form = FilterForm(request.GET or {})  # Ensure form is never None

    def get_breadcrumbs(self):
        return [
            {"title": "All Projects", "url": reverse("project:project-list")},
            {"title": "Projects Dashboard", "url": None},
        ]

    def get_queryset(self) -> QuerySet[Project]:
        """Get filtered projects for dashboard view."""
        # Ensure filter_form exists and is valid
        if not self.filter_form or not self.filter_form.is_valid():
            # Return unfiltered queryset if form is invalid
            return Project.objects.filter(account=self.request.user).order_by(
                "-created_at"
            )

        projects = Project.objects.filter(account=self.request.user).order_by(
            "-created_at"
        )

        # Apply filters from form
        search = self.filter_form.cleaned_data.get("search")
        active_only = self.filter_form.cleaned_data.get("active_projects")

        if search:
            projects = projects.filter(name__icontains=search)

        if active_only:
            projects = projects.filter(status=Project.Status.ACTIVE)

        return projects

    def get_context_data(self, **kwargs):
        """Add financial metrics to context."""
        context = super().get_context_data(**kwargs)
        projects = context["projects"]

        # Add the already-validated form to context
        context["filter_form"] = self.filter_form

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

            # Get CPI and SPI for this project
            current_date = datetime.now()
            try:
                project_cpi = project.cost_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                project_cpi = None
            try:
                project_spi = project.schedule_performance_index(current_date)
            except (ZeroDivisionError, TypeError):
                project_spi = None

            dashboard_data.append(
                {
                    "project": project,
                    "contract_value": contract_value,
                    "certified_amount": certified_amount,
                    "forecast_amount": forecast_amount,
                    "certified_percentage": certified_percentage,
                    "forecast_percentage": forecast_percentage,
                    "cpi": project_cpi,
                    "spi": project_spi,
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
        portfolio = cast(Account, self.request.user).portfolio
        context["portfolio"] = portfolio
        context["current_date"] = datetime.now()

        # Generate 12 months of CPI/SPI data for charts
        performance_data = self._get_performance_chart_data(portfolio)
        context["performance_labels"] = json.dumps(performance_data["labels"])
        context["cpi_data"] = json.dumps(performance_data["cpi"])
        context["spi_data"] = json.dumps(performance_data["spi"])
        context["current_cpi"] = performance_data["current_cpi"]
        context["current_spi"] = performance_data["current_spi"]

        return context

    def _get_performance_chart_data(self, portfolio) -> dict:
        """Generate 12 months of CPI/SPI data for portfolio."""
        labels = []
        cpi_values = []
        spi_values = []

        current_date = datetime.now()

        # Generate data for last 12 months (oldest to newest)
        for i in range(11, -1, -1):
            # Calculate the date for this month
            month_date = current_date - timedelta(days=i * 30)
            # Normalize to first of month
            month_date = month_date.replace(day=1)

            labels.append(month_date.strftime("%b %Y"))

            if portfolio:
                try:
                    cpi = portfolio.cost_performance_index(month_date)
                    cpi_values.append(float(cpi) if cpi else None)
                except (ZeroDivisionError, TypeError, Exception):
                    cpi_values.append(None)

                try:
                    spi = portfolio.schedule_performance_index(month_date)
                    spi_values.append(float(spi) if spi else None)
                except (ZeroDivisionError, TypeError, Exception):
                    spi_values.append(None)
            else:
                cpi_values.append(None)
                spi_values.append(None)

        return {
            "labels": labels,
            "cpi": cpi_values,
            "spi": spi_values,
            "current_cpi": cpi_values[-1] if cpi_values else None,
            "current_spi": spi_values[-1] if spi_values else None,
        }


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

        # Add CPI/SPI chart data
        performance_data = self._get_project_performance_data(self.object)
        context["performance_labels"] = json.dumps(performance_data["labels"])
        context["cpi_data"] = json.dumps(performance_data["cpi"])
        context["spi_data"] = json.dumps(performance_data["spi"])
        context["current_cpi"] = performance_data["current_cpi"]
        context["current_spi"] = performance_data["current_spi"]
        context["current_date"] = datetime.now()

        return context

    def _get_project_performance_data(self, project: Project) -> dict:
        """Generate 12 months of CPI/SPI data for a single project."""
        labels = []
        cpi_values = []
        spi_values = []

        current_date = datetime.now()

        # Generate data for last 12 months (oldest to newest)
        for i in range(11, -1, -1):
            # Calculate the date for this month
            month_date = current_date - timedelta(days=i * 30)
            # Normalize to first of month
            month_date = month_date.replace(day=1)

            labels.append(month_date.strftime("%b %Y"))

            try:
                cpi = project.cost_performance_index(month_date)
                cpi_values.append(float(cpi) if cpi else None)
            except (ZeroDivisionError, TypeError, Exception):
                cpi_values.append(None)

            try:
                spi = project.schedule_performance_index(month_date)
                spi_values.append(float(spi) if spi else None)
            except (ZeroDivisionError, TypeError, Exception):
                spi_values.append(None)

        return {
            "labels": labels,
            "cpi": cpi_values,
            "spi": spi_values,
            "current_cpi": cpi_values[-1] if cpi_values else None,
            "current_spi": spi_values[-1] if spi_values else None,
        }


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
        """Redirect to the project detail."""
        if self.object and self.object.pk:
            return reverse_lazy("project:project-detail", kwargs={"pk": self.object.pk})
        return reverse_lazy("project:project-list")


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
