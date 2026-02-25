"""CRUD views for Daily Diary."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import DailyDiary


class DailyDiaryMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Daily Diary views."""

    model = DailyDiary
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return DailyDiary.objects.filter(project=self.get_project())

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy("project:project-dashboard", kwargs={"pk": project.pk})
                ),
            ),
            BreadcrumbItem(
                title="Site Management",
                url=str(
                    reverse_lazy(
                        "site_management:site-management",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Daily Diary", url=None),
        ]


class DailyDiaryListView(DailyDiaryMixin, ListView):
    """List all daily diaries."""

    template_name = "site_management/daily_diary/list.html"
    context_object_name = "daily_diaries"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class DailyDiaryCreateView(DailyDiaryMixin, CreateView):
    """Create a new daily diary."""

    template_name = "site_management/daily_diary/form.html"
    fields = [
        "date",
        "weather",
        "work_activities",
        "visitors",
        "issues_delays",
        "site_instructions",
        "remarks",
    ]
    widgets = {"date": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = self.widgets["date"]
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Daily diary created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:daily-diary-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class DailyDiaryUpdateView(DailyDiaryMixin, UpdateView):
    """Update a daily diary."""

    template_name = "site_management/daily_diary/form.html"
    fields = [
        "date",
        "weather",
        "work_activities",
        "visitors",
        "issues_delays",
        "site_instructions",
        "remarks",
    ]
    widgets = {"date": DateInput(attrs={"type": "date"})}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = self.widgets["date"]
        return form

    def form_valid(self, form):
        messages.success(self.request, "Daily diary updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:daily-diary-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class DailyDiaryDeleteView(DailyDiaryMixin, DeleteView):
    """Delete a daily diary."""

    template_name = "site_management/daily_diary/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Daily diary deleted successfully!")
        return reverse_lazy(
            "site_management:daily-diary-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
