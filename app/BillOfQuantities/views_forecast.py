"""Views for managing forecasts."""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

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
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Project


class ForecastMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    """Mixin for forecast views."""

    permissions = ["contractor"]
    project_slug = "project_pk"

    def get_project(self: Any) -> Project:
        """Get the project for the current view."""
        if not hasattr(self, "project") or not self.project:
            self.project = get_object_or_404(
                Project,
                pk=self.kwargs[self.project_slug],
                account=self.request.user,
            )
        return self.project


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

    def get_object(self: "ForecastEditView") -> Forecast:
        """Get forecast for the project."""
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
                transaction_data[transaction_id] = {"quantity": value}
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

    def get_object(self):
        """Get forecast for the project."""
        project = self.get_project()
        return get_object_or_404(Forecast, pk=self.kwargs["pk"], project=project)

    def get_context_data(self, **kwargs):
        """Add forecast summary and project to context."""
        context = super().get_context_data(**kwargs)
        forecast = self.get_object()
        project = self.get_project()

        context["project"] = project
        context["forecast_transactions"] = (
            forecast.forecast_transactions.select_related(
                "line_item",
                "line_item__structure",
                "line_item__bill",
                "line_item__package",
            ).order_by("line_item__row_index")
        )

        # Calculate totals
        total_forecast = forecast.forecast_transactions.aggregate(
            total=Sum("total_price")
        )["total"] or Decimal("0.00")

        # Calculate original budget total
        original_budget = LineItem.objects.filter(
            project=project, is_work=True, special_item=False
        ).aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")

        context["total_forecast"] = total_forecast
        context["original_budget"] = original_budget
        context["difference"] = total_forecast - original_budget

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

        # Approve the forecast
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
    """List all forecasts for a project."""

    model = Forecast
    template_name = "forecast/forecast_list.html"
    context_object_name = "forecasts"

    def get_breadcrumbs(self: "ForecastListView") -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(title="Projects", url=reverse("project:project-list")),
            BreadcrumbItem(
                title=project.name,
                url=reverse("project:project-detail", kwargs={"pk": project.pk}),
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
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()

        context["project"] = project
        return context


class ForecastReportView(ForecastMixin, DetailView):
    """Generate Chart.js report showing 12 months forecast vs budget."""

    model = Project
    template_name = "forecast/forecast_report.html"
    context_object_name = "project"

    def get_breadcrumbs(self: "ForecastReportView") -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(title="Projects", url=reverse("project:project-list")),
            BreadcrumbItem(
                title=project.name,
                url=reverse("project:project-detail", kwargs={"pk": project.pk}),
            ),
            BreadcrumbItem(
                title="Forecast Report",
                url=None,
            ),
        ]

    def get_object(self: "ForecastReportView") -> Project:
        """Get project for the current view."""
        return self.get_project()

    def get_context_data(self: "ForecastReportView", **kwargs):
        """Add chart data to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_object()

        # Get original budget total first
        original_budget = LineItem.objects.filter(
            project=project, is_work=True, special_item=False
        ).aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")

        # Get last 12 months of data with proper month calculation
        last_forecast: Forecast | None = project.forecasts.last()
        if not last_forecast:
            today = date.today()
        else:
            today = last_forecast.period
        months_data = []

        for i in range(11, -1, -1):
            # Calculate month start and end properly
            if today.month - i <= 0:
                month = today.month - i + 12
                year = today.year - 1
            else:
                month = today.month - i
                year = today.year

            month_start = date(year, month, 1)

            # Get forecast for this month
            forecast = Forecast.objects.filter(
                project=project,
                period__year=year,
                period__month=month,
                status=Forecast.Status.APPROVED,
            ).first()

            forecast_total = Decimal("0.00")
            if forecast:
                forecast_total = forecast.forecast_transactions.aggregate(
                    total=Sum("total_price")
                )["total"] or Decimal("0.00")

            # Calculate variance and percentage
            variance = forecast_total - original_budget
            variance_pct = (
                ((forecast_total / original_budget - 1) * 100)
                if original_budget > 0
                else Decimal("0.00")
            )

            months_data.append(
                {
                    "month": month_start.strftime("%b %Y"),
                    "forecast": float(forecast_total),
                    "variance": float(variance),
                    "variance_pct": float(variance_pct),
                }
            )

        # Calculate average forecast
        total_forecast = sum(item["forecast"] for item in months_data)
        average_forecast = (
            total_forecast / 12 if total_forecast > 0 else Decimal("0.00")
        )

        context["months_data"] = months_data
        context["original_budget"] = float(original_budget)
        context["average_forecast"] = float(average_forecast)
        context["chart_labels"] = [item["month"] for item in months_data]
        context["forecast_data"] = [item["forecast"] for item in months_data]
        context["budget_data"] = [
            float(original_budget)
        ] * 12  # Same budget for all months

        return context
