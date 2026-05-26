"""Views for Project app."""

import json
from datetime import date, datetime
from typing import cast

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, QuerySet, Sum
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.Account.models import Account
from app.Account.subscription_config import Subscription
from app.BillOfQuantities.models import (
    ActualTransaction,
    Forecast,
    PaymentCertificate,
    Structure,
)
from app.core.Utilities.dates import (
    get_beginning_of_month,
    get_end_of_month,
    get_month_range,
)
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import (
    UserHasProjectRoleGenericMixin,
)
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import (
    PlannedValue,
    Project,
    ProjectCategory,
    ProjectDocument,
    ProjectRole,
    Role,
)

from .project_forms import BasicProjectCreateForm, ProjectFilterForm, ProjectForm


class ProjectMixin(
    SubscriptionRequiredMixin, UserHasProjectRoleGenericMixin, BreadcrumbMixin
):
    required_tiers = [Subscription.FREE_TIER]

    def get_queryset(self: "ProjectMixin") -> QuerySet[Project]:
        return Project.objects.filter(
            Q(users=self.request.user) | Q(is_demo=True)
        ).order_by("-created_at")

    def get_object(self: "ProjectMixin") -> Project:
        return self.get_project()


class ProjectListView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, ListView
):
    """Project list view that reuses dashboard filtering logic."""

    route = "list/"
    name = "project-list"
    template_name = "project/project_list.html"
    filter_form: ProjectFilterForm | None = None
    context_object_name = "projects"
    required_tiers = [Subscription.FREE_TIER]

    def setup(self, request, *args, **kwargs):
        """Initialize filter form during view setup."""
        super().setup(request, *args, **kwargs)

        form_data = request.GET or {}

        user = cast(Account, request.user)
        if user.is_superuser or user.is_staff:
            projects = Project.objects.all().order_by("-created_at")
        else:
            projects = user.get_projects.order_by("-created_at")

        from app.Account.models import Municipality
        from app.Project.models import Company, ProjectDiscipline, ProjectStage

        consultant_ids = (
            projects.values_list("lead_consultants", flat=True)
            .exclude(lead_consultants__isnull=True)
            .distinct()
        )
        consultant_queryset = Account.objects.filter(id__in=consultant_ids).distinct()

        client_queryset = Company.objects.filter(
            client_projects__in=projects
        ).distinct()
        contractor_queryset = Company.objects.filter(
            contractor_projects__in=projects
        ).distinct()

        category_queryset = ProjectCategory.objects.filter(
            projects__in=projects
        ).distinct()
        area_queryset = Municipality.objects.filter(projects__in=projects).distinct()
        discipline_queryset = ProjectDiscipline.objects.filter(
            projects__in=projects
        ).distinct()
        stage_queryset = ProjectStage.objects.filter(projects__in=projects).distinct()

        self.filter_form = ProjectFilterForm(
            form_data,
            user=user,
            projects_queryset=projects,
            consultant_queryset=consultant_queryset,
            client_queryset=client_queryset,
            contractor_queryset=contractor_queryset,
            category_queryset=category_queryset,
            area_queryset=area_queryset,
            discipline_queryset=discipline_queryset,
            stage_queryset=stage_queryset,
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Update breadcrumbs for project list page."""
        return [
            {"title": "Portfolio", "url": "/"},
            {"title": "Projects", "url": None},
        ]

    def get_queryset(self: "ProjectListView") -> QuerySet[Project]:
        """Get filtered projects for dashboard view."""
        # Ensure filter_form exists and is valid
        user = cast(Account, self.request.user)
        if user.is_superuser or user.is_staff:
            projects = Project.objects.all().order_by("-created_at")
        else:
            projects = user.get_projects.order_by("-created_at")

        if not self.filter_form or not self.filter_form.is_valid():
            return projects

        # Apply filters from form
        search = self.filter_form.cleaned_data.get("search")
        active_only = self.filter_form.cleaned_data.get("active_projects")
        category = self.filter_form.cleaned_data.get("project_category")
        area = self.filter_form.cleaned_data.get("area")
        discipline = self.filter_form.cleaned_data.get("project_discipline")
        stage = self.filter_form.cleaned_data.get("project_stage")

        if search:
            projects = projects.filter(name__icontains=search)

        if category:
            projects = projects.filter(project_category=category)

        if area:
            projects = projects.filter(area=area)

        if discipline:
            projects = projects.filter(project_discipline=discipline)

        if stage:
            projects = projects.filter(project_stage=stage)

        selected_project = self.filter_form.cleaned_data.get("projects")
        if selected_project:
            projects = projects.filter(pk=selected_project.pk)

        consultant = self.filter_form.cleaned_data.get("consultant")
        if consultant:
            projects = projects.filter(lead_consultants=consultant)

        client = self.filter_form.cleaned_data.get("client")
        if client:
            projects = projects.filter(client=client)

        contractor = self.filter_form.cleaned_data.get("contractor")
        if contractor:
            projects = projects.filter(contractor=contractor)

        status = self.filter_form.cleaned_data.get("status")
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

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Portfolio", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(title=f"{self.object.name} Dashboard", url=None),
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

        term_window = self.request.GET.get("term_window") or "current"
        context["term_window"] = term_window

        current_month = current_date.replace(day=1)
        context["current_term_label"] = current_month.strftime("%b %Y")

        financial_data = self._get_financial_comparison_data(
            project=project,
            current_month=current_month,
            term_window=term_window,
        )
        context["financial_labels"] = json.dumps(financial_data["labels"])
        context["planned_values"] = json.dumps(financial_data["planned_values"])
        context["forecast_values"] = json.dumps(financial_data["forecast_values"])
        context["certified_values"] = json.dumps(financial_data["certified_values"])
        context["contract_value"] = float(revised_contract_value)

        return context

    def _get_financial_comparison_data(
        self,
        project: Project,
        current_month: datetime | date,
        term_window: str,
    ) -> dict:
        labels: list[str] = []
        planned_values: list[float] = []
        forecast_values: list[float] = []
        certified_values: list[float] = []

        current_month_dt = get_beginning_of_month(current_month)
        if term_window == "past_3":
            start_month = current_month_dt - relativedelta(months=2)
            end_month = current_month_dt
        elif term_window == "next_3":
            start_month = current_month_dt
            end_month = current_month_dt + relativedelta(months=2)
        else:
            start_month = current_month_dt
            end_month = current_month_dt

        months = get_month_range(start_month, end_month)

        project_start = (
            get_beginning_of_month(project.start_date) if project.start_date else None
        )
        project_end = (
            get_beginning_of_month(project.end_date) if project.end_date else None
        )

        if project_start or project_end:
            months = [
                m
                for m in months
                if (project_start is None or m >= project_start)
                and (project_end is None or m <= project_end)
            ]

        if not months and project_start and project_end:
            if current_month_dt < project_start:
                months = [project_start]
            elif current_month_dt > project_end:
                months = [project_end]

        for month in months:
            labels.append(month.strftime("%b %Y"))

            # Get planned value for this month
            planned_value = PlannedValue.objects.filter(
                project=project,
                period__year=month.year,
                period__month=month.month,
            ).first()
            planned_values.append(float(planned_value.value) if planned_value else 0)

            forecast = Forecast.objects.filter(
                project=project,
                period__year=month.year,
                period__month=month.month,
                status=Forecast.Status.APPROVED,
            ).first()
            forecast_values.append(float(forecast.total_forecast) if forecast else 0)

            end_of_month = get_end_of_month(month)
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


class ProjectSetupView(ProjectMixin, DetailView):
    """Display project setup page with all management options."""

    model = Project
    template_name = "project/project_setup.html"
    context_object_name = "project"
    roles = [Role.USER]
    project_slug = "pk"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=self.object.name,
                url=reverse(
                    "project:project-management", kwargs={"pk": self.object.pk}
                ),
            ),
            BreadcrumbItem(title="Edit Project", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        from app.Estimator.models import ProjectMaterial

        if project.contractor_id:
            context["sibling_projects"] = (
                Project.objects.filter(contractor_id=project.contractor_id)
                .exclude(pk=project.pk)
                .order_by("name")
            )
        else:
            context["sibling_projects"] = Project.objects.none()
        context["has_estimator_data"] = ProjectMaterial.objects.filter(
            project=project
        ).exists()
        context["boq_documents"] = (
            ProjectDocument.objects.filter(
                project=project,
                category=ProjectDocument.DocumentCategory.BILL_OF_QUANTITIES,
            )
            .select_related("uploaded_by")
            .order_by("-created_at")[:5]
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        project = self.object
        action = request.POST.get("action")

        if action == "clone_system":
            from app.Estimator.services import initialize_project_estimator

            try:
                result = initialize_project_estimator(project)
                if result.get("status") == "no_contractor_company":
                    messages.error(
                        request,
                        "This project has no contractor assigned. Set a "
                        "contractor on the project before cloning the library.",
                    )
                elif result.get("status") == "already_initialized":
                    messages.warning(
                        request,
                        "This project already has estimator data. "
                        "Clear existing data first or use a fresh project.",
                    )
                else:
                    messages.success(
                        request,
                        f"Contractor library cloned — "
                        f"{result['trade_codes']} trade codes, "
                        f"{result['materials']} materials, "
                        f"{result['labour_crews']} labour crews, "
                        f"{result['specifications']} specifications, "
                        f"{result['labour_specs']} labour specs.",
                    )
            except Exception as e:
                messages.error(request, f"Clone from contractor library failed: {e}")

        elif action == "clone_project":
            from django.shortcuts import get_object_or_404

            from app.Estimator.services import clone_from_project

            source_pk = request.POST.get("source_project")
            if not source_pk:
                messages.error(request, "Please select a project to clone from.")
            else:
                source_project = get_object_or_404(Project, pk=source_pk)
                try:
                    result = clone_from_project(project, source_project)
                    messages.success(
                        request,
                        f"Cloned from '{source_project.name}' — "
                        f"{result['trade_codes']} trade codes, "
                        f"{result['materials']} materials, "
                        f"{result['labour_crews']} labour crews, "
                        f"{result['specifications']} specifications, "
                        f"{result['labour_specs']} labour specs.",
                    )
                except Exception as e:
                    messages.error(request, f"Clone from project failed: {e}")

        elif action == "upload_boq_attachment":
            boq_file = request.FILES.get("boq_file")
            if not boq_file:
                messages.error(request, "Please select a BOQ file to upload.")
            else:
                title = (request.POST.get("boq_title") or "").strip()
                notes = (request.POST.get("boq_notes") or "").strip()
                if not title:
                    title = f"BOQ upload - {boq_file.name}"

                ProjectDocument.objects.create(
                    project=project,
                    category=ProjectDocument.DocumentCategory.BILL_OF_QUANTITIES,
                    title=title,
                    file=boq_file,
                    uploaded_by=request.user,
                    notes=notes,
                )
                messages.success(
                    request,
                    "BOQ file uploaded. Our team will format it and upload it into the system.",
                )

        elif action == "load_demo_boq":
            from app.BillOfQuantities.services import import_boq_from_excel

            demo_file_path = "Project Upload by WBS_ Demo.xlsx"
            try:
                created_count, errors = import_boq_from_excel(project, demo_file_path)
                if errors:
                    messages.error(
                        request, f"Failed to load demo data: {'; '.join(errors)}"
                    )
                else:
                    messages.success(
                        request,
                        f"Demo project populated successfully with {created_count} line items!",
                    )
                    return HttpResponseRedirect(
                        reverse("project:project-wbs-detail", kwargs={"pk": project.pk})
                    )
            except Exception as e:
                messages.error(request, f"Error loading demo data: {e}")

        return HttpResponseRedirect(
            reverse("project:project-setup", kwargs={"pk": project.pk})
        )


class ProjectManagementView(ProjectMixin, DetailView):
    """Display project management page with all buttons (no graphs)."""

    model = Project
    template_name = "project/project_management.html"
    roles = [Role.USER]
    project_slug = "pk"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=f"{self.object.name} Dashboard",
                url=reverse("project:project-dashboard", kwargs={"pk": self.object.pk}),
            ),
            BreadcrumbItem(title="Management", url=None),
        ]

    def get_context_data(self: "ProjectManagementView", **kwargs):
        """Add structures to context."""
        context = super().get_context_data(**kwargs)
        line_items = self.object.line_items.all()
        # Calculate total
        total = line_items.aggregate(total=Sum("total_price"))["total"] or 0
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

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(title="Projects", url=reverse("project:project-list")),
            BreadcrumbItem(
                title=f"{self.object.name} Dashboard",
                url=reverse(
                    "project:project-management", kwargs={"pk": self.object.pk}
                ),
            ),
            BreadcrumbItem(title="WBS", url=None),
        ]

    def get_context_data(self, **kwargs):
        """Add line items total and filter options to context."""
        from django.db.models import Sum

        from app.BillOfQuantities.models import Bill, Package

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


class ProjectCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, CreateView
):
    """Create a new project."""

    model = Project
    form_class = BasicProjectCreateForm
    template_name = "project/project_form.html"
    required_tiers = [Subscription.FREE_TIER]
    permissions = ["contractor"]

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Return to Projects",
                url=reverse("project:portfolio-dashboard"),
            ),
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
            url = reverse("project:project-setup", kwargs={"pk": self.object.pk})
            return url
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
            "Final account reset successfully. Project status set to ACTIVE.",
        )

        return redirect("project:project-management", pk=project.pk)

    def get(self, request, *args, **kwargs):
        """Redirect GET requests to project management."""
        from django.shortcuts import redirect

        return redirect("project:project-management", pk=self.kwargs["pk"])


class ProjectDeleteView(ProjectMixin, DeleteView):
    """Delete a project (soft delete)."""

    model = Project
    template_name = "project/project_confirm_delete.html"
    success_url = reverse_lazy("project:portfolio-dashboard")
    roles = [Role.ADMIN]
    project_slug = "pk"

    def get_context_data(self, **kwargs):
        """Add project context to delete confirmation."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.object
        return context

    def delete(self, request, *args, **kwargs):
        """Perform soft delete of the project."""
        self.object = self.get_object()
        project_name = self.object.name

        # Perform soft delete
        self.object.soft_delete()

        messages.success(
            request,
            f"Project '{project_name}' has been deleted successfully.",
        )

        return HttpResponseRedirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        """Handle POST request for deletion with confirmation."""
        self.object = self.get_object()
        confirm_name = request.POST.get("confirm_name", "")

        if confirm_name != self.object.name:
            messages.error(
                request,
                "Project name confirmation does not match. Please try again.",
            )
            return self.get(request, *args, **kwargs)

        return self.delete(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Redirect GET requests to project management."""
        from django.shortcuts import redirect

        return redirect("project:project-management", pk=self.kwargs["pk"])


class OrderAmendmentsView(ProjectMixin, DetailView):
    """Display Order Amendments register with charts and form."""

    model = Project
    template_name = "project/order_amendments.html"
    roles = [Role.USER]
    project_slug = "pk"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=f"{self.object.name} Dashboard",
                url=reverse("project:project-dashboard", kwargs={"pk": self.object.pk}),
            ),
            BreadcrumbItem(title="Order Amendments", url=None),
        ]

    def get_context_data(self, **kwargs):
        """Add amendment data and chart data to context."""
        context = super().get_context_data(**kwargs)
        project = self.object

        original_contract_value = float(project.original_contract_value or 0)
        revised_contract_value = float(project.revised_contract_value or 0)

        # Get amendments from database
        from app.Project.models import OrderAmendment

        db_amendments = project.order_amendments.filter(
            status=OrderAmendment.Status.APPROVED
        ).order_by("amendment_number")

        # Convert to list format for template
        amendments = []
        for amendment in db_amendments:
            amendments.append(
                {
                    "amendment_number": amendment.amendment_number,
                    "name": amendment.name,
                    "description": amendment.description,
                    "variation_amount": float(amendment.variation_amount),
                    "category": amendment.category,
                    "date_approved": amendment.date_approved,
                    "status": amendment.status,
                }
            )

        # Calculate running totals
        running_total = original_contract_value
        for amendment in amendments:
            running_total += amendment["variation_amount"]
            amendment["approved_contract_amount"] = running_total
            amendment["percent_change"] = (
                (amendment["variation_amount"] / original_contract_value) * 100
                if original_contract_value > 0
                else 0
            )

        # Summary statistics
        total_variations = revised_contract_value - original_contract_value
        final_contract_value = revised_contract_value
        total_percent_change = (
            (total_variations / original_contract_value) * 100
            if original_contract_value > 0
            else 0
        )

        # Get pending amendments value
        pending_value = (
            project.order_amendments.filter(
                status=OrderAmendment.Status.PENDING
            ).aggregate(total=Sum("variation_amount"))["total"]
            or 0
        )

        # Category data for pie chart
        category_totals: dict[str, float] = {}
        category_names = {
            "scope_change": "Scope Change",
            "design_change": "Design Change",
            "rate_adjustment": "Rate Adjustment",
            "quantity_variance": "Quantity Variance",
            "delay_costs": "Delay Costs",
            "other": "Other",
        }
        for amendment in amendments:
            cat = amendment["category"]
            current_value = category_totals.get(cat, 0.0)
            category_totals[cat] = float(current_value + amendment["variation_amount"])

        category_labels = [category_names[k] for k in category_names.keys()]
        category_signed_values = [
            category_totals.get(k, 0) for k in category_names.keys()
        ]
        category_values = [abs(v) for v in category_signed_values]

        # Waterfall chart data
        waterfall_labels = ["Original Contract"]
        waterfall_values = [original_contract_value]

        current_value = original_contract_value
        for a in amendments:
            waterfall_labels.append(f"Amendment {a['amendment_number']}")
            variation = a["variation_amount"]
            waterfall_values.append(variation)
            current_value += variation

        waterfall_labels.append("Revised Contract Amount")
        waterfall_values.append(final_contract_value)

        # Initialize form
        from app.Project.forms import OrderAmendmentForm

        form = OrderAmendmentForm()

        context.update(
            {
                "project": project,
                "amendments": amendments,
                "form": form,
                "original_contract_value": original_contract_value,
                "total_variations": total_variations,
                "final_contract_value": final_contract_value,
                "total_percent_change": total_percent_change,
                "amendments_count": len(amendments),
                "total_approved_value": total_variations,
                "pending_value": float(pending_value),
                "budget_impact_percentage": round(total_percent_change, 1),
                "category_labels": json.dumps(category_labels),
                "category_values": json.dumps(category_values),
                "category_signed_values": json.dumps(category_signed_values),
                "waterfall_labels": json.dumps(waterfall_labels),
                "waterfall_values": json.dumps(waterfall_values),
                "current_date": datetime.now(),
            }
        )

        return context

    def post(self, request, *args, **kwargs):
        """Handle form submission for new amendment."""
        self.object = self.get_object()
        project = self.object

        from app.Project.forms import OrderAmendmentForm

        form = OrderAmendmentForm(request.POST, project=project, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Amendment added successfully.")
        else:
            messages.error(request, "Please correct the errors below.")
            context = self.get_context_data()
            context["form"] = form
            return self.render_to_response(context)

        return HttpResponseRedirect(request.path)
