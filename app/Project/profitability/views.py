from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from app.Project.projects.projects_models import Project

from .utils import (
    get_project_profitability_metrics,
    import_labour_logs_to_profitability,
    import_material_logs_to_profitability,
    import_subcontractor_logs_to_profitability,
)


class ProfitabilityMixin(LoginRequiredMixin):
    """Mixin for profitability submodule views scoping to project."""

    project: Project

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.get("project_pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(project=self.project)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["project"] = self.project

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
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
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
            from .utils import import_plant_logs_to_profitability

            count = import_plant_logs_to_profitability(self.project)
            messages.success(
                request, f"Successfully imported {count} plant log entries."
            )
            return redirect(
                "project:profitability-plant-list", project_pk=self.project.pk
            )

        return redirect("project:profitability-dashboard", project_pk=self.project.pk)
