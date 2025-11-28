"""Views for PlannedValue management."""

from datetime import date
from decimal import Decimal
from typing import Any

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.db.models import QuerySet, Sum
from django.http import Http404, HttpRequest, HttpResponse
from django.urls import reverse
from django.views.generic import TemplateView

from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import PlannedValueForm
from app.Project.models import PlannedValue, Project


def get_months_between(start_date: date, end_date: date) -> list[date]:
    """Generate a list of month start dates between start_date and end_date."""
    months = []
    current = start_date.replace(day=1)
    end = end_date.replace(day=1)

    while current <= end:
        months.append(current)
        current += relativedelta(months=1)

    return months


class PlannedValueMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    """Mixin for PlannedValue views."""

    permissions = ["contractor"]
    project: Project

    def get_project(self) -> Project:
        """Get the project for this view."""
        if hasattr(self, "project") and self.project:
            return self.project

        project_pk = self.kwargs.get("project_pk")
        try:
            self.project = Project.objects.get(pk=project_pk, account=self.request.user)
            return self.project
        except Project.DoesNotExist as err:
            raise Http404(
                "Project not found or you don't have permission to access it."
            ) from err

    def get_queryset(self) -> QuerySet[PlannedValue]:
        """Get planned values for the project."""
        return PlannedValue.objects.filter(project=self.get_project()).order_by(
            "period"
        )


class PlannedValueEditView(PlannedValueMixin, TemplateView):
    """View for editing all planned values for a project at once."""

    template_name = "planned_value/planned_value_edit.html"

    def get_breadcrumbs(self) -> list[dict[str, str | None]]:
        project = self.get_project()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-list")},
            {
                "title": project.name,
                "url": reverse("project:project-management", kwargs={"pk": project.pk}),
            },
            {"title": "Planned Values", "url": None},
        ]

    def get_months(self) -> list[date]:
        """Get the list of months based on project start and end dates."""
        project = self.get_project()

        if not project.start_date or not project.end_date:
            return []

        return get_months_between(project.start_date, project.end_date)

    def get_planned_values_dict(self) -> dict[date, PlannedValue]:
        """Get existing planned values as a dictionary keyed by period."""
        planned_values = self.get_queryset()
        return {pv.period: pv for pv in planned_values}

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        months = self.get_months()
        existing_values = self.get_planned_values_dict()

        # Build form data for each month
        month_forms = []
        for month in months:
            existing_pv = existing_values.get(month)
            initial = {"value": existing_pv.value if existing_pv else Decimal("0.00")}
            form = PlannedValueForm(
                initial=initial,
                prefix=f"month_{month.strftime('%Y_%m')}",
            )
            month_forms.append(
                {
                    "month": month,
                    "month_label": month.strftime("%B %Y"),
                    "form": form,
                    "existing_value": existing_pv,
                }
            )

        # Calculate totals
        total_planned = sum(
            (mf["existing_value"].value if mf["existing_value"] else Decimal("0"))
            for mf in month_forms
        )
        contract_value = project.get_total_contract_value

        # Warning if totals don't match
        warning_message = None
        if total_planned != contract_value and contract_value > 0:
            difference = contract_value - total_planned
            if difference > 0:
                warning_message = (
                    f"Planned values are R {difference:,.2f} less than contract value."
                )
            else:
                warning_message = (
                    f"Planned values exceed contract value by R {abs(difference):,.2f}."
                )

        context.update(
            {
                "project": project,
                "month_forms": month_forms,
                "total_planned": total_planned,
                "contract_value": contract_value,
                "warning_message": warning_message,
                "has_dates": bool(project.start_date and project.end_date),
            }
        )
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle form submission for all planned values."""
        project = self.get_project()
        months = self.get_months()

        if not months:
            messages.error(request, "Please set project start and end dates first.")
            return self.get(request, *args, **kwargs)

        existing_values = self.get_planned_values_dict()
        errors = []
        saved_count = 0

        for month in months:
            prefix = f"month_{month.strftime('%Y_%m')}"
            form = PlannedValueForm(request.POST, prefix=prefix)

            if form.is_valid():
                value = form.cleaned_data.get("value") or Decimal("0.00")

                # Get or create the planned value
                existing_pv = existing_values.get(month)
                if existing_pv:
                    existing_pv.value = value
                    existing_pv.save()
                else:
                    PlannedValue.objects.create(
                        project=project,
                        period=month,
                        value=value,
                    )
                saved_count += 1
            else:
                errors.append(f"{month.strftime('%B %Y')}: {form.errors}")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Check if total matches contract value
            total_planned = PlannedValue.objects.filter(project=project).aggregate(
                total=Sum("value")
            )["total"] or Decimal("0")
            contract_value = project.get_total_contract_value

            if total_planned != contract_value and contract_value > 0:
                difference = contract_value - total_planned
                if difference > 0:
                    messages.warning(
                        request,
                        f"Saved {saved_count} planned values. Warning: Total (R {total_planned:,.2f}) is R {difference:,.2f} less than contract value (R {contract_value:,.2f}).",
                    )
                else:
                    messages.warning(
                        request,
                        f"Saved {saved_count} planned values. Warning: Total (R {total_planned:,.2f}) exceeds contract value (R {contract_value:,.2f}) by R {abs(difference):,.2f}.",
                    )
            else:
                messages.success(
                    request,
                    f"Successfully saved {saved_count} planned values. Total matches contract value.",
                )

        return self.get(request, *args, **kwargs)
