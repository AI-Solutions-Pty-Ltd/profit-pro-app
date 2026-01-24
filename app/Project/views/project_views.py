"""Views for Project app."""

import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet, Sum
from django.http import Http404, JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.BillOfQuantities.models import ActualTransaction, Forecast, PaymentCertificate
from app.core.Utilities.dates import get_end_of_month, get_previous_n_months
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.models import sum_queryset
from app.core.Utilities.permissions import (
    UserHasProjectRoleGenericMixin,
)
from app.Project.forms import FilterForm, ProjectForm
from app.Project.models import PlannedValue, Project, ProjectRole, Role


class ProjectMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    def get_queryset(self: "ProjectMixin") -> QuerySet[Project]:
        return Project.objects.filter(users=self.request.user).order_by("-created_at")

    def get_object(self: "ProjectMixin") -> Project:
        project = super().get_object()  # type: ignore
        if self.request.user not in project.users.all():
            raise Http404("You do not have permission to view this project.")
        return project


class ProjectListView(LoginRequiredMixin, BreadcrumbMixin, ListView):
    """Project list view that reuses dashboard filtering logic."""

    template_name = "project/project_list.html"
    filter_form: FilterForm | None = None
    context_object_name = "projects"

    def setup(self, request, *args, **kwargs):
        """Initialize filter form during view setup."""
        super().setup(request, *args, **kwargs)
        self.filter_form = FilterForm(request.GET or {}, user=request.user)

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Update breadcrumbs for project list page."""
        return [
            {"title": "Portfolio", "url": "/"},
            {"title": "Projects", "url": None},
        ]

    def get_queryset(self: "ProjectListView") -> QuerySet[Project]:
        """Get filtered projects for dashboard view."""
        # Ensure filter_form exists and is valid
        projects = self.request.user.get_projects.order_by("-created_at")
        if not self.filter_form or not self.filter_form.is_valid():
            # Return unfiltered queryset if form is invalid
            return projects

        # Apply filters from form
        search = self.filter_form.cleaned_data.get("search")
        active_only = self.filter_form.cleaned_data.get("active_projects")
        category = self.filter_form.cleaned_data.get("category")
        status = self.filter_form.cleaned_data.get("status")

        if search:
            projects = projects.filter(name__icontains=search)

        if category:
            projects = projects.filter(category=category)

        selected_project = self.filter_form.cleaned_data.get("projects")
        if selected_project:
            projects = projects.filter(pk=selected_project.pk)

        consultant = self.filter_form.cleaned_data.get("consultant")
        if consultant:
            projects = projects.filter(lead_consultant=consultant)

        if status and status != "ALL":
            projects = projects.filter(status=status)
        elif active_only:
            # Legacy support for active_only toggle
            projects = projects.filter(status=Project.Status.ACTIVE)

        return projects

    def get_context_data(self: "ProjectListView", **kwargs):
        """Add financial metrics to context."""
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        return context

    def get(self: "ProjectListView", request, *args, **kwargs):
        """Handle both regular GET and AJAX requests for filtering."""
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            # Return JSON response for AJAX requests
            self.object_list = self.get_queryset()
            context = self.get_context_data()

            # Render just the table body
            from django.template.loader import render_to_string

            html = render_to_string(
                "portfolio/_project_table_rows.html", context, request=request
            )

            return JsonResponse({"html": html})

        return super().get(request, *args, **kwargs)


class ProjectDashboardView(ProjectMixin, DetailView):
    """Display project dashboard with graphs only."""

    model = Project
    template_name = "project/project_dashboard.html"
    context_object_name = "project"
    roles = [Role.ADMIN]
    project_slug = "pk"

    def get_breadcrumbs(self):
        return [
            {"title": "Portfolio", "url": reverse("project:portfolio-dashboard")},
            {"title": f"{self.object.name} Dashboard", "url": None},
        ]

    def get_context_data(self: "ProjectDashboardView", **kwargs):
        """Add chart data to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        current_date = get_end_of_month(datetime.now())

        # Contract values
        original_contract_value = project.original_contract_value
        revised_contract_value = project.total_contract_value
        context["original_contract_value"] = original_contract_value
        context["revised_contract_value"] = revised_contract_value

        # Latest forecast value and variance
        if project.latest_forecast:
            context["latest_forecast_value"] = project.latest_forecast
            context["forecast_variance_percent"] = project.forecast_variance_percent
        else:
            context["latest_forecast_value"] = None
            context["forecast_variance_percent"] = None

        # Certified to date - sum all approved payment certificate transactions
        certified_to_date = project.total_certified_to_date
        context["certified_to_date"] = certified_to_date
        context["certified_percent"] = project.total_certified_to_date_percentage

        # Latest CPI and SPI
        context["current_cpi"] = project.get_cost_performance_index(current_date)
        context["current_spi"] = project.get_schedule_performance_index(current_date)
        context["current_date"] = current_date

        # Add financial comparison chart data
        financial_data = self._get_financial_comparison_data(project)
        context["financial_labels"] = json.dumps(financial_data["labels"])
        context["planned_values"] = json.dumps(financial_data["planned_values"])
        context["forecast_values"] = json.dumps(financial_data["forecast_values"])
        context["certified_values"] = json.dumps(financial_data["certified_values"])
        context["contract_value"] = float(revised_contract_value)

        return context

    def _get_financial_comparison_data(self, project: Project) -> dict:
        """Generate monthly Planned Value, Forecast, and Cumulative Certified data.

        Chart is bounded by project start_date and end_date, showing up to 12 months.
        """
        labels = []
        planned_values = []
        forecast_values = []
        certified_values = []

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

        # Generate data for each month in the range (oldest to newest)
        for current_month in get_previous_n_months(
            starting_date=project_start, end_cap=project_end
        ):
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
            end_of_month = get_end_of_month(current_month)
            cumulative_certified = ActualTransaction.objects.filter(
                line_item__project=project,
                payment_certificate__status=PaymentCertificate.Status.APPROVED,
                payment_certificate__approved_on__lt=end_of_month,
            ).aggregate(total=Sum("total_price"))["total"]
            certified_values.append(
                float(cumulative_certified) if cumulative_certified else 0
            )

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
    roles = [Role.USER]
    project_slug = "pk"

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
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
    roles = [Role.CONTRACT_BOQ, Role.ADMIN, Role.USER]
    project_slug = "pk"

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
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


class ProjectCreateView(LoginRequiredMixin, BreadcrumbMixin, CreateView):
    """Create a new project."""

    model = Project
    form_class = ProjectForm
    template_name = "project/project_form.html"
    permissions = ["contractor"]

    def get_breadcrumbs(self):
        return [
            {
                "title": "Return to Projects",
                "url": reverse("project:portfolio-dashboard"),
            },
        ]

    def form_valid(self, form):
        """Set the portfolio and add current user to the project."""
        form.instance.portfolio = self.request.user.portfolio  # type: ignore
        response = super().form_valid(form)
        self.object.users.add(self.request.user)  # type: ignore
        ProjectRole.objects.create(
            project=self.object, user=self.request.user, role=Role.ADMIN
        )
        return response

    def get_success_url(self: "ProjectCreateView"):
        """Redirect to the project dashboard."""
        if self.object and self.object.pk:
            return reverse_lazy(
                "project:project-dashboard", kwargs={"pk": self.object.pk}
            )
        return reverse_lazy("project:portfolio-dashboard")


class ProjectUpdateView(ProjectMixin, UpdateView):
    """Update an existing project."""

    model = Project
    form_class = ProjectForm
    template_name = "project/project_form.html"
    roles = [Role.ADMIN]
    project_slug = "pk"

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
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

    def form_valid(self, form):
        """Set the portfolio to the current user's portfolio before saving."""
        form.instance.portfolio = self.request.user.portfolio  # type: ignore
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to project management."""
        return reverse_lazy("project:project-management", kwargs={"pk": self.object.pk})


class ProjectDeleteView(ProjectMixin, DeleteView):
    """Delete a project."""

    model = Project
    template_name = "project/project_confirm_delete.html"
    success_url = reverse_lazy("project:portfolio-dashboard")
    roles = [Role.ADMIN]
    project_slug = "pk"

    def get_breadcrumbs(self):
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
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


class ProjectResetFinalAccountView(ProjectMixin, DetailView):
    """Reset project final account status."""

    model = Project
    roles = [Role.ADMIN]
    project_slug = "pk"

    def post(self, request, *args, **kwargs):
        """Handle POST request to reset final account."""
        from django.shortcuts import redirect

        project = self.get_object()

        if project.final_payment_certificate:
            # Unmark the payment certificate as final
            final_cert = project.final_payment_certificate
            final_cert.is_final = False
            final_cert.save(update_fields=["is_final"])

            # Clear the final payment certificate reference
            project.final_payment_certificate = None

        # Set project status back to ACTIVE
        project.status = Project.Status.ACTIVE
        project.save(update_fields=["status", "final_payment_certificate"])

        messages.success(
            request,
            f"Project '{project.name}' has been reset to Active status.",
        )

        return redirect("project:project-management", pk=project.pk)

    def get(self, request, *args, **kwargs):
        """Redirect GET requests to project management."""
        from django.shortcuts import redirect

        return redirect("project:project-management", pk=self.kwargs["pk"])
