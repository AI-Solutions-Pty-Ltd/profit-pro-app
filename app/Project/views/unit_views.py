"""Views for Centralized Unit Management."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from ..forms.unit_forms import UnitOfMeasureForm
from ..models.unit_models import UnitOfMeasure


class UnitOfMeasureListView(LoginRequiredMixin, ListView):
    """List view for units of measure."""

    model = UnitOfMeasure
    template_name = "unit_management/list.html"
    context_object_name = "units"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_units = UnitOfMeasure.objects.filter(deleted=False)
        context["total_count"] = all_units.count()
        context["base_units_count"] = all_units.filter(
            reference_unit__isnull=True
        ).count()
        context["categories_count"] = all_units.values("category").distinct().count()
        return context


class UnitOfMeasureCreateView(LoginRequiredMixin, CreateView):
    """Create view for units of measure."""

    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = "unit_management/form.html"
    success_url = reverse_lazy("project:unit-list")


class UnitOfMeasureUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for units of measure."""

    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = "unit_management/form.html"
    success_url = reverse_lazy("project:unit-list")


class UnitOfMeasureDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for units of measure."""

    model = UnitOfMeasure
    template_name = "unit_management/confirm_delete.html"
    success_url = reverse_lazy("project:unit-list")
