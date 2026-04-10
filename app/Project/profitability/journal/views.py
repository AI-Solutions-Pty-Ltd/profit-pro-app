from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Project.forms.profitability_forms import JournalEntryForm
from app.Project.models import JournalEntry
from app.Project.profitability.views import ProfitabilityMixin


class JournalEntryListView(ProfitabilityMixin, ListView):
    model = JournalEntry
    template_name = "profitability/journal/list.html"
    context_object_name = "entries"
    auto_import_type = "certificate"


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
