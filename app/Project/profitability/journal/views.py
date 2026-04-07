from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.forms.profitability_forms import JournalEntryForm
from app.Project.models import JournalEntry, Project


class ProfitabilityMixin(LoginRequiredMixin):
    """Mixin for profitability submodule views scoping to project."""

    project: Project

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.get("project_pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(project=self.project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context

    def form_valid(self, form):
        form.instance.project = self.project
        return super().form_valid(form)


class JournalEntryListView(ProfitabilityMixin, ListView):
    model = JournalEntry
    template_name = "profitability/journal/list.html"
    context_object_name = "entries"


class JournalEntryCreateView(ProfitabilityMixin, CreateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = "profitability/journal/form.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-journal-list", kwargs={"project_pk": self.project.pk}
        )


class JournalEntryUpdateView(ProfitabilityMixin, UpdateView):
    model = JournalEntry
    form_class = JournalEntryForm
    template_name = "profitability/journal/form.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-journal-list", kwargs={"project_pk": self.project.pk}
        )


class JournalEntryDeleteView(ProfitabilityMixin, DeleteView):
    model = JournalEntry
    template_name = "profitability/journal/confirm_delete.html"

    def get_success_url(self):
        return reverse(
            "project:profitability-journal-list", kwargs={"project_pk": self.project.pk}
        )
