from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from django.views.generic import TemplateView

from app.Project.projects.projects_models import Project

from .utils import (
    bulk_sync_all_trackers_to_journal,
    get_project_profitability_metrics,
    import_certificates_to_journal,
    import_labour_logs_to_profitability,
    import_material_logs_to_profitability,
    import_overhead_logs_to_profitability,
    import_plant_logs_to_profitability,
    import_subcontractor_logs_to_profitability,
    import_material_logs_to_profitability,
)


class ProfitabilityMixin(LoginRequiredMixin):
    """Mixin for profitability submodule views scoping to project and monthly pagination."""

    project: Project
    display_date: date

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.get("project_pk"))

        # Monthly Pagination Setup
        from datetime import date

        today = date.today()
        month = request.GET.get("month", today.month)
        year = request.GET.get("year", today.year)

        try:
            self.display_date = date(int(year), int(month), 1)
        except (ValueError, TypeError):
            self.display_date = today.replace(day=1)

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().filter(project=self.project)  # type: ignore
        # Filter by month and year
        return qs.filter(
            date__month=self.display_date.month, date__year=self.display_date.year
        )

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)  # type: ignore
        context["project"] = self.project

        # Pagination Metadata
        context["display_date"] = self.display_date
        context["prev_month"] = (self.display_date - relativedelta(months=1)).month
        context["prev_year"] = (self.display_date - relativedelta(months=1)).year
        context["next_month"] = (self.display_date + relativedelta(months=1)).month
        context["next_year"] = (self.display_date + relativedelta(months=1)).year

        # Automatic Import Logic (Check if empty and trigger sync)
        auto_import_type = getattr(self, "auto_import_type", None)
        if auto_import_type and not context["object_list"].exists():
            count = 0
            if auto_import_type == "labour":
                count = import_labour_logs_to_profitability(self.project)
            elif auto_import_type == "material":
                count = import_material_logs_to_profitability(self.project)
            elif auto_import_type == "subcontractor":
                count = import_subcontractor_logs_to_profitability(self.project)
            elif auto_import_type == "plant":
                count = import_plant_logs_to_profitability(self.project)
            elif auto_import_type == "overhead":
                count = import_overhead_logs_to_profitability(self.project)
            elif auto_import_type == "certificate":
                from .utils import import_certificates_to_journal

                count = import_certificates_to_journal(self.project)

            if count > 0:
                # Refresh the list if data was imported
                context["object_list"] = self.get_queryset()
                # Also update the custom name if it exists (e.g. 'entries' for journal)
                if hasattr(self, "context_object_name") and self.context_object_name:
                    context[self.context_object_name] = context["object_list"]

                messages.info(
                    self.request,  # type: ignore
                    f"Automatically synced {count} new entries from project records.",
                )

        # Add KVI project-level metrics
        metrics = get_project_profitability_metrics(self.project)
        context["kvi_actual_profit"] = metrics["actual_profit"]
        context["kvi_actual_margin"] = metrics["actual_margin"]
        context["kvi_target_margin"] = metrics["target_margin"]

        return context

    def form_valid(self, form):
        from django.views.generic.edit import DeleteView

        if not isinstance(self, DeleteView):
            form.instance.project = self.project
        return super().form_valid(form)  # type: ignore

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()  # type: ignore
        from django.views.generic.edit import DeleteView

        if not isinstance(self, DeleteView):
            kwargs["project"] = self.project
        return kwargs


class ComingSoonView(ProfitabilityMixin, TemplateView):
    """
    Placeholder view for features that are still in development.
    """

    template_name = "profitability/coming_soon.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feature_name"] = self.kwargs.get("feature_name", "Feature")
        return context


class ImportLogsView(ProfitabilityMixin, View):
    """
    View to trigger import of site logs into profitability trackers.
    """

    def post(self, request, *args, **kwargs):
        import_type = request.POST.get("import_type")
        count = 0

        if import_type == "subcontractor":
            count = import_subcontractor_logs_to_profitability(self.project)
            messages.success(
                request, f"Successfully imported {count} subcontractor log entries."
            )
            return redirect(
                "project:profitability-subcontractor-list", project_pk=self.project.pk
            )
        elif import_type == "labour":
            count = import_labour_logs_to_profitability(self.project)
            messages.success(
                request, f"Successfully imported {count} labour log entries."
            )
            return redirect(
                "project:profitability-labour-list", project_pk=self.project.pk
            )
        elif import_type == "material":
            count = import_material_logs_to_profitability(self.project)
            messages.success(
                request, f"Successfully imported {count} material log entries."
            )
            return redirect(
                "project:profitability-material-list", project_pk=self.project.pk
            )
        elif import_type == "plant":
            count = import_plant_logs_to_profitability(self.project)
            messages.success(
                request, f"Successfully imported {count} plant log entries."
            )
            return redirect(
                "project:profitability-plant-list", project_pk=self.project.pk
            )
        elif import_type == "overhead":
            count = import_overhead_logs_to_profitability(self.project)
            messages.success(
                request, f"Successfully imported {count} overhead log entries."
            )
            return redirect(
                "project:profitability-overhead-list", project_pk=self.project.pk
            )
        elif import_type == "certificate":
            count = import_certificates_to_journal(self.project)
            messages.success(
                request,
                f"Successfully imported {count} journal entries from certificates.",
            )
            return redirect(
                "project:profitability-journal-list", project_pk=self.project.pk
            )
        elif import_type == "bulk_journal":
            count = bulk_sync_all_trackers_to_journal(self.project)
            messages.success(
                request,
                f"Successfully synchronized {count} cost and revenue entries to the Journal.",
            )
            return redirect(
                "project:profitability-journal-list", project_pk=self.project.pk
            )

        return redirect("project:profitability-dashboard", project_pk=self.project.pk)
