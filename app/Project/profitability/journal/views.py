from django.db.models import Sum
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calculate summary of expenses by category for the filtered queryset
        # Note: self.get_queryset() already handles project and monthly filtering via ProfitabilityMixin
        expenses = self.get_queryset().filter(transaction_type=JournalEntry.EntryType.DEBIT)
        summary_query = (
            expenses.values("category").annotate(total=Sum("amount")).order_by("category")
        )

        # Mapping for UI richness (Matching premium style guide colors)
        category_metadata = {
            JournalEntry.Category.MATERIAL: {"icon": "cube", "color": "indigo"},
            JournalEntry.Category.LABOUR: {"icon": "user-group", "color": "purple"},
            JournalEntry.Category.SUBCONTRACTOR: {"icon": "briefcase", "color": "blue"},
            JournalEntry.Category.OVERHEAD: {"icon": "building-office", "color": "gray"},
            JournalEntry.Category.PLANT: {"icon": "truck", "color": "amber"},
            JournalEntry.Category.OTHER: {"icon": "ellipsis-horizontal", "color": "slate"},
            JournalEntry.Category.REVENUE: {"icon": "banknotes", "color": "emerald"},
        }

        expense_summary = []
        total_expense = 0
        total_revenue = 0

        # Calculate Total Revenue
        revenue_total = expenses.model.objects.filter(
            project=self.project,
            date__month=self.display_date.month,
            date__year=self.display_date.year,
            transaction_type=JournalEntry.EntryType.CREDIT,
        ).aggregate(total=Sum("amount"))["total"] or 0
        total_revenue = revenue_total

        for item in summary_query:
            cat = item["category"]
            total = item["total"] or 0
            total_expense += total

            metadata = category_metadata.get(
                cat, {"icon": "document-text", "color": "gray"}
            )
            cat_label = dict(JournalEntry.Category.choices).get(cat, cat)

            expense_summary.append(
                {
                    "category": cat,
                    "label": cat_label,
                    "total": total,
                    "icon": metadata["icon"],
                    "color": metadata["color"],
                }
            )

        context["expense_summary"] = expense_summary
        context["total_expense"] = total_expense
        context["total_revenue"] = total_revenue
        return context


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
