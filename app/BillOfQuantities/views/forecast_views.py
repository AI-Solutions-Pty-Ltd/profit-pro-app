"""Views for managing forecasts."""

import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.db import transaction
from django.db.models import QuerySet, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView

from app.BillOfQuantities.models import (
    Bill,
    Forecast,
    ForecastTransaction,
    LineItem,
    Package,
    Structure,
)
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role


class ForecastMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for forecast views."""

    roles = [Role.COST_FORECASTS, Role.ADMIN, Role.USER]
    project_slug = "project_pk"


class ForecastCreateView(ForecastMixin, TemplateView):
    """Create a new forecast with period selection."""

    template_name = "forecast/forecast_create.html"

    def get_breadcrumbs(self: "ForecastCreateView") -> list[BreadcrumbItem]:
        """Get breadcrumbs for the current view."""
        project = self.get_project()
        return [
            {
                "title": project.name,
                "url": reverse(
                    "bill_of_quantities:forecast-list",
                    kwargs={"project_pk": project.pk},
                ),
            },
            {"title": "Create Forecast", "url": None},
        ]

    def get_context_data(self: "ForecastCreateView", **kwargs):
        """Add project and check for active forecast."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project

        # Check if there's an active (draft) forecast
        active_forecast = Forecast.objects.filter(
            project=project, status=Forecast.Status.DRAFT
        ).first()
        context["active_forecast"] = active_forecast

        # Default to current month
        today = date.today()
        context["default_period"] = today.replace(day=1)

        return context

    def get_form(self: "ForecastCreateView", form_class=None):
        """Override to prevent FormMixin from trying to create a form."""
        return None

    def get_form_class(self: "ForecastCreateView"):
        """Override to prevent FormMixin from trying to get form class."""
        return None

    def post(self: "ForecastCreateView", request, *args, **kwargs):
        """Handle forecast creation."""
        project = self.get_project()

        # Check if there's already an active forecast
        active_forecast = Forecast.objects.filter(
            project=project, status=Forecast.Status.DRAFT
        ).first()

        if active_forecast:
            messages.error(
                request,
                "Cannot create new forecast. There is already an active forecast.",
            )
            return redirect(
                reverse(
                    "bill_of_quantities:forecast-create",
                    kwargs={"project_pk": project.pk},
                )
            )

        # Get period from form
        period_str = request.POST.get("period")
        if not period_str:
            messages.error(request, "Please select a period for the forecast.")
            return redirect(
                reverse(
                    "bill_of_quantities:forecast-create",
                    kwargs={"project_pk": project.pk},
                )
            )

        try:
            period = date.fromisoformat(f"{period_str}-01")
        except ValueError:
            messages.error(request, "Invalid period format.")
            return redirect(
                reverse(
                    "bill_of_quantities:forecast-create",
                    kwargs={"project_pk": project.pk},
                )
            )

        # Validate period falls within project dates
        if project.start_date and period < project.start_date.replace(day=1):
            messages.error(
                request,
                f"Forecast period cannot be before project start date ({project.start_date.strftime('%b %Y')}).",
            )
            return redirect(
                reverse(
                    "bill_of_quantities:forecast-create",
                    kwargs={"project_pk": project.pk},
                )
            )
        if project.end_date and period > project.end_date.replace(day=1):
            messages.error(
                request,
                f"Forecast period cannot be after project end date ({project.end_date.strftime('%b %Y')}).",
            )
            return redirect(
                reverse(
                    "bill_of_quantities:forecast-create",
                    kwargs={"project_pk": project.pk},
                )
            )

        if Forecast.objects.filter(project=project, period=period).exists():
            messages.error(
                request,
                f"Forecast for {period.strftime('%B %Y')} already exists.",
            )
            return redirect(
                reverse(
                    "bill_of_quantities:forecast-create",
                    kwargs={"project_pk": project.pk},
                )
            )

        # Create forecast
        with transaction.atomic():
            forecast = Forecast.objects.create(
                project=project,
                period=period,
                captured_by=request.user,
                status=Forecast.Status.DRAFT,
            )

            # Clone forecast transactions from latest forecast or create from line items
            self._create_forecast_transactions(forecast)

        messages.success(
            request, f"Forecast for {period.strftime('%B %Y')} created successfully!"
        )
        return redirect(
            reverse(
                "bill_of_quantities:forecast-edit",
                kwargs={"project_pk": project.pk, "pk": forecast.pk},
            )
        )

    def _create_forecast_transactions(self: "ForecastCreateView", forecast):
        """Create ForecastTransactions based on latest forecast or original line items."""
        project = forecast.project

        # Get latest forecast (excluding the one we just created)
        latest_forecast = (
            Forecast.objects.filter(project=project)
            .exclude(pk=forecast.pk)
            .order_by("-created_at")
            .first()
        )

        if latest_forecast:
            # Clone from latest forecast
            latest_transactions = latest_forecast.forecast_transactions.all()
            for transaction in latest_transactions:
                ForecastTransaction.objects.create(
                    forecast=forecast,
                    line_item=transaction.line_item,
                    quantity=transaction.quantity,
                    unit_price=transaction.unit_price,
                    total_price=transaction.total_price,
                )
        else:
            # Create from original line items
            line_items = LineItem.objects.filter(
                project=project,
                is_work=True,  # Only create for work items
                special_item=False,  # Exclude special items
            ).select_related("structure", "bill", "package")

            for line_item in line_items:
                ForecastTransaction.objects.create(
                    forecast=forecast,
                    line_item=line_item,
                    quantity=line_item.budgeted_quantity or Decimal("0.00"),
                    unit_price=line_item.unit_price or Decimal("0.00"),
                    total_price=line_item.total_price or Decimal("0.00"),
                )


class ForecastEditView(ForecastMixin, DetailView):
    """Edit forecast transactions for a forecast."""

    model = Forecast
    template_name = "forecast/forecast_edit.html"
    context_object_name = "forecast"

    def get_breadcrumbs(self: "ForecastEditView") -> list[BreadcrumbItem]:
        """Get breadcrumbs for the forecast edit view."""
        project = self.get_project()
        forecast = self.get_object()
        return [
            BreadcrumbItem(
                title=project.name,
                url=reverse(
                    "bill_of_quantities:forecast-list",
                    kwargs={"project_pk": project.pk},
                ),
            ),
            BreadcrumbItem(
                title=forecast.period,
                url=reverse(
                    "bill_of_quantities:forecast-edit",
                    kwargs={"project_pk": project.pk, "pk": forecast.pk},
                ),
            ),
        ]

    def get_object(self: "ForecastEditView", queryset=None) -> Forecast:
        """Get forecast for the project."""
        if not queryset:
            self.get_queryset()
        project = self.get_project()
        return get_object_or_404(Forecast, pk=self.kwargs["pk"], project=project)

    def get_context_data(self: "ForecastEditView", **kwargs):
        """Add forecast transactions and project to context."""
        context = super().get_context_data(**kwargs)
        forecast = self.get_object()
        project = self.get_project()

        # Get filter parameters from GET request
        structure_filter = self.request.GET.get("structure")
        bill_filter = self.request.GET.get("bill")
        package_filter = self.request.GET.get("package")
        description = self.request.GET.get("description")

        # Get all structures, bills, packages for filter options
        structures = Structure.objects.filter(project=project).distinct()
        bills = Bill.objects.filter(structure__project=project).distinct()
        packages = Package.objects.filter(bill__structure__project=project).distinct()

        # Apply cascading filters to filter options
        if structure_filter:
            bills = bills.filter(structure_id=structure_filter)
        if bill_filter:
            packages = packages.filter(bill_id=bill_filter)

        # Get all forecast transactions with related data
        transactions = forecast.forecast_transactions.select_related(
            "line_item",
            "line_item__structure",
            "line_item__bill",
            "line_item__package",
        ).order_by("line_item__row_index")

        # Apply filters if provided
        if structure_filter:
            transactions = transactions.filter(line_item__structure_id=structure_filter)
        if bill_filter:
            transactions = transactions.filter(line_item__bill_id=bill_filter)
        if package_filter:
            transactions = transactions.filter(line_item__package_id=package_filter)
        if description:
            transactions = transactions.filter(
                line_item__description__icontains=description
            )

        transactions = list(transactions)

        # Group transactions by structure, then bill, then package
        grouped_transactions = {}

        for forecast_transaction in transactions:
            line_item = forecast_transaction.line_item
            structure = line_item.structure
            bill = line_item.bill
            package = line_item.package

            # Group by structure
            if structure not in grouped_transactions:
                grouped_transactions[structure] = {}

            # Group by bill within structure
            if bill not in grouped_transactions[structure]:
                grouped_transactions[structure][bill] = {}

            # Group by package within bill
            if package not in grouped_transactions[structure][bill]:
                grouped_transactions[structure][bill][package] = []

            grouped_transactions[structure][bill][package].append(forecast_transaction)

        context["project"] = project
        context["grouped_transactions"] = grouped_transactions
        context["structures"] = structures
        context["bills"] = bills
        context["packages"] = packages

        return context

    def post(self: "ForecastEditView", request, *args, **kwargs):
        """Update forecast transactions."""
        forecast: Forecast = self.get_object()

        if forecast.status != Forecast.Status.DRAFT:
            messages.error(request, "Cannot edit a forecast that has been approved.")
            return redirect(
                reverse(
                    "bill_of_quantities:forecast-edit",
                    kwargs={"project_pk": forecast.project.pk, "pk": forecast.pk},
                )
            )

        # Update each transaction
        transaction_data = {}
        for key, value in request.POST.items():
            if key.startswith("quantity_"):
                transaction_id = key.split("_")[1]
                if transaction_id not in transaction_data:
                    transaction_data[transaction_id] = {}
                transaction_data[transaction_id]["quantity"] = value
            elif key.startswith("unit_price_"):
                transaction_id = key.split("_")[2]
                if transaction_id not in transaction_data:
                    transaction_data[transaction_id] = {}
                transaction_data[transaction_id]["unit_price"] = value
            elif key.startswith("total_price_"):
                transaction_id = key.split("_")[2]
                if transaction_id not in transaction_data:
                    transaction_data[transaction_id] = {}
                transaction_data[transaction_id]["total_price"] = value
            elif key.startswith("notes_"):
                transaction_id = key.split("_")[1]
                if transaction_id not in transaction_data:
                    transaction_data[transaction_id] = {}
                transaction_data[transaction_id]["notes"] = value

        with transaction.atomic():
            for transaction_id, data in transaction_data.items():
                try:
                    ft = ForecastTransaction.objects.get(
                        id=transaction_id, forecast=forecast
                    )

                    # Update quantity and unit price, then recalculate total
                    if "quantity" in data:
                        ft.quantity = Decimal(data["quantity"])
                    if "unit_price" in data:
                        ft.unit_price = Decimal(data["unit_price"])
                    if "notes" in data:
                        ft.notes = data["notes"]

                    # Recalculate total price
                    ft.total_price = ft.quantity * ft.unit_price
                    ft.save()

                except (
                    ForecastTransaction.DoesNotExist,
                    ValueError,
                    InvalidOperation,
                ):
                    messages.error(
                        request, f"Invalid data for transaction {transaction_id}"
                    )
                    return redirect(
                        reverse(
                            "bill_of_quantities:forecast-edit",
                            kwargs={
                                "project_pk": forecast.project.pk,
                                "pk": forecast.pk,
                            },
                        )
                    )

        messages.success(request, "Forecast updated successfully!")

        # Check if we should redirect to approve page
        if request.GET.get("next") == "approve":
            return redirect(
                reverse(
                    "bill_of_quantities:forecast-approve",
                    kwargs={"project_pk": forecast.project.pk, "pk": forecast.pk},
                )
            )

        return redirect(
            reverse(
                "bill_of_quantities:forecast-edit",
                kwargs={"project_pk": forecast.project.pk, "pk": forecast.pk},
            )
        )


class ForecastApproveView(ForecastMixin, DetailView):
    """Approve a forecast."""

    model = Forecast
    template_name = "forecast/forecast_approve.html"
    context_object_name = "forecast"

    def get_breadcrumbs(self: "ForecastApproveView") -> list[BreadcrumbItem]:
        """Get breadcrumbs for the forecast approve view."""
        project = self.get_project()
        forecast = self.get_object()
        return [
            BreadcrumbItem(
                title=f"{project.name}: Forecast",
                url=reverse(
                    "bill_of_quantities:forecast-list",
                    kwargs={"project_pk": project.pk},
                ),
            ),
            BreadcrumbItem(
                title=f"{forecast.period.strftime('%B %Y')}",
                url=reverse(
                    "bill_of_quantities:forecast-approve",
                    kwargs={"project_pk": project.pk, "pk": forecast.pk},
                ),
            ),
        ]

    def get_object(self, queryset=None):
        """Get forecast for the project."""
        if not self.queryset:
            self.get_queryset()
        project = self.get_project()
        return get_object_or_404(Forecast, pk=self.kwargs["pk"], project=project)

    def get_context_data(self, **kwargs):
        """Add forecast summary and project to context."""
        context = super().get_context_data(**kwargs)
        forecast = self.get_object()
        project = self.get_project()

        context["project"] = project

        # Get all forecast transactions
        all_transactions = forecast.forecast_transactions.select_related(
            "line_item",
            "line_item__structure",
            "line_item__bill",
            "line_item__package",
        ).order_by("line_item__row_index")

        # Filter to only show transactions that differ from original line item
        # (quantity or total_price differs)
        changed_transactions = [
            t
            for t in all_transactions
            if t.quantity != t.line_item.budgeted_quantity
            or t.total_price != t.line_item.total_price
            or t.notes  # Also show if there are notes
        ]

        # Group changed transactions by structure > bill > package for header rows
        grouped_transactions = []
        current_structure = None
        current_bill = None
        current_package = None

        for t in changed_transactions:
            structure = t.line_item.structure
            bill = t.line_item.bill
            package = t.line_item.package

            # Add structure header if changed
            if structure != current_structure:
                current_structure = structure
                current_bill = None
                current_package = None
                if structure:
                    grouped_transactions.append(
                        {
                            "type": "structure",
                            "name": structure.name,
                            "object": structure,
                        }
                    )

            # Add bill header if changed
            if bill != current_bill:
                current_bill = bill
                current_package = None
                if bill:
                    grouped_transactions.append(
                        {
                            "type": "bill",
                            "name": bill.name,
                            "object": bill,
                        }
                    )

            # Add package header if changed
            if package != current_package:
                current_package = package
                if package:
                    grouped_transactions.append(
                        {
                            "type": "package",
                            "name": package.name,
                            "object": package,
                        }
                    )

            # Add the transaction
            grouped_transactions.append(
                {
                    "type": "transaction",
                    "transaction": t,
                }
            )

        context["forecast_transactions"] = grouped_transactions
        context["total_transactions"] = all_transactions.count()
        context["changed_count"] = len(changed_transactions)

        # Calculate totals
        total_forecast = forecast.forecast_transactions.aggregate(
            total=Sum("total_price")
        )["total"] or Decimal("0.00")

        # Calculate original budget total
        original_budget = LineItem.objects.filter(
            project=project, is_work=True, special_item=False
        ).aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")

        # Get prior forecast (most recent approved forecast before this one)
        prior_forecast = (
            Forecast.objects.filter(
                project=project,
                status=Forecast.Status.APPROVED,
                period__lt=forecast.period,
            )
            .order_by("-period")
            .first()
        )

        if prior_forecast:
            prior_forecast_total = prior_forecast.forecast_transactions.aggregate(
                total=Sum("total_price")
            )["total"] or Decimal("0.00")
            context["prior_forecast"] = prior_forecast
            context["prior_forecast_total"] = prior_forecast_total
        else:
            context["prior_forecast"] = None
            context["prior_forecast_total"] = None

        context["total_forecast"] = total_forecast
        context["original_budget"] = original_budget
        context["difference"] = total_forecast - original_budget

        # Build L1/L2 summary data (structures and bills) - use default ordering
        structure_summary = []
        for structure in project.structures.all():
            budget_total = structure.budget_total
            forecast_total = structure.get_forecast_total(forecast)
            variance = forecast_total - budget_total

            bills_data = []
            for bill in structure.bills.all():
                bill_budget = bill.budget_total
                bill_forecast = bill.get_forecast_total(forecast)
                bill_variance = bill_forecast - bill_budget
                bills_data.append(
                    {
                        "bill": bill,
                        "budget_total": bill_budget,
                        "forecast_total": bill_forecast,
                        "variance": bill_variance,
                    }
                )

            structure_summary.append(
                {
                    "structure": structure,
                    "budget_total": budget_total,
                    "forecast_total": forecast_total,
                    "variance": variance,
                    "bills": bills_data,
                }
            )

        context["structure_summary"] = structure_summary

        return context

    def post(self, request, *args, **kwargs):
        """Approve the forecast."""
        forecast = self.get_object()

        if forecast.status != Forecast.Status.DRAFT:
            messages.error(request, "This forecast has already been approved.")
            return redirect(
                reverse(
                    "bill_of_quantities:forecast-approve",
                    kwargs={"project_pk": forecast.project.pk, "pk": forecast.pk},
                )
            )

        # Capture approval notes and approve the forecast
        forecast.notes = request.POST.get("notes", "")
        forecast.status = Forecast.Status.APPROVED
        forecast.approved_by = request.user
        forecast.save()

        messages.success(
            request,
            f"Forecast for {forecast.period.strftime('%B %Y')} approved successfully!",
        )
        return redirect(
            reverse(
                "bill_of_quantities:forecast-list",
                kwargs={"project_pk": forecast.project.pk},
            )
        )


class ForecastListView(ForecastMixin, ListView):
    """Forecast Dashboard - List all forecasts with chart and summary."""

    model = Forecast
    template_name = "forecast/forecast_dashboard.html"
    context_object_name = "forecasts"

    def get_breadcrumbs(self: "ForecastListView") -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=reverse("project:portfolio-dashboard")
            ),
            BreadcrumbItem(
                title=project.name,
                url=reverse("project:project-management", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Forecasts",
                url=None,
            ),
        ]

    def get_queryset(self: "ForecastListView") -> QuerySet[Forecast]:
        """Get forecasts for the project."""
        project = self.get_project()
        return Forecast.objects.filter(project=project).order_by("-period")

    def get_context_data(self: "ForecastListView", **kwargs):
        """Add project and chart data to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project
        current_date = datetime.now()

        # Get original budget total (excl addendums)
        original_budget = project.original_contract_value

        # Get revised contract value (total including addendums)
        revised_contract_value = project.total_contract_value

        # Get draft forecast if any
        draft_forecast = Forecast.objects.filter(
            project=project, status=Forecast.Status.DRAFT
        ).first()
        context["draft_forecast"] = draft_forecast

        # Get approved forecasts
        approved_forecasts = context["forecasts"].filter(
            status=Forecast.Status.APPROVED
        )

        # Latest approved forecast total
        latest_approved = approved_forecasts.order_by("-period").first()
        latest_forecast_total = Decimal("0.00")
        if latest_approved:
            latest_forecast_total = latest_approved.forecast_transactions.aggregate(
                total=Sum("total_price")
            )["total"] or Decimal("0.00")

        # CPI and SPI
        context["current_cpi"] = project.get_cost_performance_index(current_date)
        context["current_spi"] = project.get_schedule_performance_index(current_date)

        # Chart data - prepare waterfall data
        chart_labels = []
        forecast_values = []
        contract_value = float(revised_contract_value)

        # Prepare waterfall data: Original → Variations → Current Forecast
        waterfall_data = []
        waterfall_labels = []

        if project.start_date and project.end_date:
            # Normalize to first of month
            project_start = project.start_date.replace(day=1)
            project_end = project.end_date.replace(day=1)
            today = date.today().replace(day=1)

            # Determine chart range
            chart_start = project_start
            chart_end = min(project_end, today)

            # If chart_end is before chart_start, start from project start
            if chart_end < chart_start:
                chart_end = chart_start

            # Calculate months coverage
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

            # Recalculate months
            months_diff = (
                (chart_end.year - chart_start.year) * 12
                + (chart_end.month - chart_start.month)
                + 1
            )

            # If more than 12 months, show most recent 12
            if months_diff > 12:
                chart_start = chart_end - relativedelta(months=11)

            # Generate data for each month
            current_month = chart_start
            while current_month <= chart_end:
                chart_labels.append(current_month.strftime("%b %Y"))

                # Get approved forecast for this month
                forecast = Forecast.objects.filter(
                    project=project,
                    period__year=current_month.year,
                    period__month=current_month.month,
                    status=Forecast.Status.APPROVED,
                ).first()

                if forecast:
                    forecast_total = forecast.forecast_transactions.aggregate(
                        total=Sum("total_price")
                    )["total"] or Decimal("0.00")
                    forecast_values.append(float(forecast_total))
                else:
                    forecast_values.append(None)  # No data for this month

                current_month = current_month + relativedelta(months=1)

        # Build waterfall data structure using monthly forecast values
        # Use month-by-month data for waterfall chart
        colors = [
            "#3B82F6",  # Blue
            "#10B981",  # Green
            "#8B5CF6",  # Purple
            "#F59E0B",  # Amber
            "#EC4899",  # Pink
            "#06B6D4",  # Cyan
            "#84CC16",  # Lime
            "#F97316",  # Orange
            "#6366F1",  # Indigo
            "#14B8A6",  # Teal
            "#A855F7",  # Violet
            "#EF4444",  # Red
        ]
        for i, (label, value) in enumerate(
            zip(chart_labels, forecast_values, strict=False)
        ):
            if value is not None:
                waterfall_labels.append(label)
                waterfall_data.append(
                    {
                        "value": value,
                        "color": colors[i % len(colors)],
                    }
                )

        context["original_budget"] = float(original_budget)
        context["revised_contract_value"] = float(revised_contract_value)
        context["latest_forecast_total"] = float(latest_forecast_total)
        context["chart_labels"] = json.dumps(chart_labels)
        context["forecast_values"] = json.dumps(forecast_values)
        context["contract_value"] = contract_value
        context["has_chart_data"] = any(v is not None for v in forecast_values)

        # Waterfall chart data
        context["waterfall_labels"] = json.dumps(waterfall_labels)
        context["waterfall_data"] = json.dumps(waterfall_data)
        context["has_waterfall_data"] = len(waterfall_data) > 0

        return context


# Keep ForecastReportView for backwards compatibility but redirect to dashboard
class ForecastReportView(ForecastMixin, DetailView):
    """Redirect to forecast dashboard."""

    model = Project

    def get(self, request, *args, **kwargs):
        """Redirect to forecast list/dashboard."""
        return redirect(
            reverse(
                "bill_of_quantities:forecast-list",
                kwargs={"project_pk": self.kwargs["project_pk"]},
            )
        )
