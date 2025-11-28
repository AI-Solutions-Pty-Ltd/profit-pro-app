"""Views for Project app."""

import json
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.db.models import QuerySet, Sum
from django.http import Http404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
)

from app.BillOfQuantities.models import ActualTransaction, Forecast, PaymentCertificate
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import ProjectForm
from app.Project.models import PlannedValue, Project


class ProjectMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    permissions = ["contractor"]

    def get_queryset(self: "ProjectMixin") -> QuerySet[Project]:
        return Project.objects.filter(account=self.request.user).order_by("-created_at")

    def get_object(self: "ProjectMixin") -> Project:
        project = super().get_object()  # type: ignore
        if project.account != self.request.user:
            raise Http404("You do not have permission to view this project.")
        return project


class ProjectDashboardView(ProjectMixin, DetailView):
    """Display project dashboard with graphs only."""

    model = Project
    template_name = "project/project_dashboard.html"
    context_object_name = "project"

    def get_breadcrumbs(self):
        return [
            {"title": "Portfolio", "url": reverse("project:portfolio-list")},
            {"title": f"{self.object.name} Dashboard", "url": None},
        ]

    def get_context_data(self: "ProjectDashboardView", **kwargs):
        """Add chart data to context."""
        context = super().get_context_data(**kwargs)
        project = self.object
        current_date = datetime.now()

        # Contract values
        original_contract_value = project.get_original_contract_value
        revised_contract_value = project.get_total_contract_value
        context["original_contract_value"] = original_contract_value
        context["revised_contract_value"] = revised_contract_value

        # Latest forecast value and variance
        latest_forecast = (
            Forecast.objects.filter(project=project, status=Forecast.Status.APPROVED)
            .order_by("-period")
            .first()
        )
        if latest_forecast:
            latest_forecast_value = latest_forecast.total_forecast
            context["latest_forecast_value"] = latest_forecast_value
            if revised_contract_value and revised_contract_value != 0:
                variance = (
                    (latest_forecast_value - revised_contract_value)
                    / revised_contract_value
                ) * 100
                context["forecast_variance_percent"] = round(variance, 1)
            else:
                context["forecast_variance_percent"] = None
        else:
            context["latest_forecast_value"] = None
            context["forecast_variance_percent"] = None

        # Certified to date - sum all approved payment certificate transactions
        certified_to_date = (
            ActualTransaction.objects.filter(
                line_item__project=project,
                payment_certificate__status=PaymentCertificate.Status.APPROVED,
            ).aggregate(total=Sum("total_price"))["total"]
            or 0
        )
        context["certified_to_date"] = certified_to_date
        if revised_contract_value and revised_contract_value != 0:
            certified_percent = (
                float(certified_to_date) / float(revised_contract_value)
            ) * 100
            context["certified_percent"] = round(certified_percent, 1)
        else:
            context["certified_percent"] = None

        # Latest CPI and SPI
        context["current_cpi"] = project.cost_performance_index(current_date)
        context["current_spi"] = project.schedule_performance_index(current_date)
        context["current_date"] = current_date

        # Add financial comparison chart data
        financial_data = self._get_financial_comparison_data(project)
        context["financial_labels"] = json.dumps(financial_data["labels"])
        context["planned_values"] = json.dumps(financial_data["planned_values"])
        context["forecast_values"] = json.dumps(financial_data["forecast_values"])
        context["certified_values"] = json.dumps(financial_data["certified_values"])
        context["contract_value"] = float(revised_contract_value)

        return context

    def _get_project_performance_data(self, project: Project) -> dict:
        """Generate CPI/SPI data bounded by project dates (up to 12 months)."""
        labels = []
        cpi_values = []
        spi_values = []

        today = date.today()

        if not project.start_date or not project.end_date:
            # No project dates set, return empty data
            messages.error(self.request, "Project dates not set")
            return {
                "labels": [],
                "cpi": [],
                "spi": [],
                "current_cpi": None,
                "current_spi": None,
            }

        # Normalize to first of month
        project_start = project.start_date.replace(day=1)
        project_end = project.end_date.replace(day=1)

        # Determine initial chart range based on current date
        chart_start = project_start
        chart_end = min(project_end, today.replace(day=1))

        # If chart_end is before chart_start (project hasn't started), start from project start
        if chart_end < chart_start:
            chart_end = chart_start

        # Calculate current months coverage
        months_diff = (
            (chart_end.year - chart_start.year) * 12
            + (chart_end.month - chart_start.month)
            + 1
        )

        # Pad into future if less than 12 months, but cap at project end
        if months_diff < 12:
            needed_months = 12 - months_diff
            extended_end = chart_end + relativedelta(months=needed_months)
            chart_end = min(extended_end, project_end)

        # Recalculate months after potential extension
        months_diff = (
            (chart_end.year - chart_start.year) * 12
            + (chart_end.month - chart_start.month)
            + 1
        )

        # If more than 12 months, show most recent 12
        if months_diff > 12:
            chart_start = chart_end - relativedelta(months=11)

        # Generate data for each month in the range (oldest to newest)
        current_month = chart_start
        while current_month <= chart_end:
            labels.append(current_month.strftime("%b %Y"))

            # Convert to datetime for performance index methods
            month_datetime = datetime(current_month.year, current_month.month, 1)

            try:
                cpi = project.cost_performance_index(month_datetime)
                cpi_values.append(float(cpi) if cpi else None)
            except (ZeroDivisionError, TypeError, Exception):
                cpi_values.append(None)

            try:
                spi = project.schedule_performance_index(month_datetime)
                spi_values.append(float(spi) if spi else None)
            except (ZeroDivisionError, TypeError, Exception):
                spi_values.append(None)

            # Move to next month
            current_month = current_month + relativedelta(months=1)

        return {
            "labels": labels,
            "cpi": cpi_values,
            "spi": spi_values,
            "current_cpi": cpi_values[-1] if cpi_values else None,
            "current_spi": spi_values[-1] if spi_values else None,
        }

    def _get_financial_comparison_data(self, project: Project) -> dict:
        """Generate monthly Planned Value, Forecast, and Cumulative Certified data.

        Chart is bounded by project start_date and end_date, showing up to 12 months.
        """
        labels = []
        planned_values = []
        forecast_values = []
        certified_values = []

        # Determine date range from project dates
        today = date.today()

        if not project.start_date or not project.end_date:
            # No project dates set, return empty data
            return {
                "labels": [],
                "planned_values": [],
                "forecast_values": [],
                "certified_values": [],
            }

        # Normalize to first of month
        project_start = project.start_date.replace(day=1)
        project_end = project.end_date.replace(day=1)

        # Determine initial chart range based on current date
        chart_start = project_start
        chart_end = min(project_end, today.replace(day=1))

        # If chart_end is before chart_start (project hasn't started), start from project start
        if chart_end < chart_start:
            chart_end = chart_start

        # Calculate current months coverage
        months_diff = (
            (chart_end.year - chart_start.year) * 12
            + (chart_end.month - chart_start.month)
            + 1
        )

        # Pad into future if less than 12 months, but cap at project end
        if months_diff < 12:
            needed_months = 12 - months_diff
            extended_end = chart_end + relativedelta(months=needed_months)
            chart_end = min(extended_end, project_end)

        # Recalculate months after potential extension
        months_diff = (
            (chart_end.year - chart_start.year) * 12
            + (chart_end.month - chart_start.month)
            + 1
        )

        # If more than 12 months, show most recent 12
        if months_diff > 12:
            chart_start = chart_end - relativedelta(months=11)

        # Generate data for each month in the range (oldest to newest)
        current_month = chart_start
        while current_month <= chart_end:
            labels.append(current_month.strftime("%b %Y"))

            # Get planned value for this month
            planned_value = PlannedValue.objects.filter(
                project=project,
                period__year=current_month.year,
                period__month=current_month.month,
            ).first()
            planned_values.append(float(planned_value.value) if planned_value else 0)

            # Get forecast for this month
            forecast = Forecast.objects.filter(
                project=project,
                period__year=current_month.year,
                period__month=current_month.month,
                status=Forecast.Status.APPROVED,
            ).first()
            forecast_values.append(float(forecast.total_forecast) if forecast else 0)

            # Get cumulative certified up to end of this month
            end_of_month = current_month + relativedelta(months=1)
            cumulative_certified = ActualTransaction.objects.filter(
                line_item__project=project,
                payment_certificate__status=PaymentCertificate.Status.APPROVED,
                payment_certificate__approved_on__lt=end_of_month,
            ).aggregate(total=Sum("total_price"))["total"]
            certified_values.append(
                float(cumulative_certified) if cumulative_certified else 0
            )

            # Move to next month
            current_month = current_month + relativedelta(months=1)

        return {
            "labels": labels,
            "planned_values": planned_values,
            "forecast_values": forecast_values,
            "certified_values": certified_values,
        }


class ProjectManagementView(ProjectMixin, DetailView):
    """Display project management page with all buttons (no graphs)."""

    model = Project
    template_name = "project/project_management.html"
    context_object_name = "project"

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:portfolio-list")},
            {
                "title": f"{self.object.name} Dashboard",
                "url": reverse(
                    "project:project-dashboard", kwargs={"pk": self.object.pk}
                ),
            },
            {"title": "Management", "url": None},
        ]

    def get_context_data(self: "ProjectManagementView", **kwargs):
        """Add structures to context."""
        context = super().get_context_data(**kwargs)
        line_items = self.object.line_items.all()
        # Calculate total
        total = sum_queryset(line_items, "total_price")
        context["line_items_total"] = total
        context["current_date"] = datetime.now()

        return context


class ProjectWBSDetailView(ProjectMixin, DetailView):
    """Display project WBS/BOQ detailed view."""

    model = Project
    template_name = "project/project_detail_wbs.html"
    context_object_name = "project"

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:portfolio-list")},
            {
                "title": f"{self.object.name} Dashboard",
                "url": reverse(
                    "project:project-dashboard", kwargs={"pk": self.object.pk}
                ),
            },
            {"title": "WBS", "url": None},
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
            {"title": "Return to Projects", "url": reverse("project:portfolio-list")},
        ]

    def form_valid(self, form):
        """Set the account to the current user before saving."""
        form.instance.account = self.request.user
        return super().form_valid(form)

    def get_success_url(self: "ProjectCreateView"):
        """Redirect to the project dashboard."""
        if self.object and self.object.pk:
            return reverse_lazy(
                "project:project-dashboard", kwargs={"pk": self.object.pk}
            )
        return reverse_lazy("project:portfolio-list")


class ProjectUpdateView(ProjectMixin, UpdateView):
    """Update an existing project."""

    model = Project
    form_class = ProjectForm
    template_name = "project/project_form.html"
    permissions = ["contractor"]

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:portfolio-list")},
            {
                "title": f"{self.object.name} Dashboard",
                "url": reverse(
                    "project:project-dashboard", kwargs={"pk": self.object.pk}
                ),
            },
            {
                "title": "Management",
                "url": reverse(
                    "project:project-management", kwargs={"pk": self.object.pk}
                ),
            },
            {"title": "Update", "url": None},
        ]

    def get_success_url(self):
        """Redirect to project management."""
        return reverse_lazy("project:project-management", kwargs={"pk": self.object.pk})


class ProjectDeleteView(ProjectMixin, DeleteView):
    """Delete a project."""

    model = Project
    template_name = "project/project_confirm_delete.html"
    success_url = reverse_lazy("project:portfolio-list")

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:portfolio-list")},
            {
                "title": f"{self.object.name} Dashboard",
                "url": reverse(
                    "project:project-dashboard", kwargs={"pk": self.object.pk}
                ),
            },
            {
                "title": "Management",
                "url": reverse(
                    "project:project-management", kwargs={"pk": self.object.pk}
                ),
            },
            {"title": "Delete", "url": None},
        ]
