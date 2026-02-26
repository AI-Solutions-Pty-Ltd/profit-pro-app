"""CRUD views for Meeting."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models.meeting import Meeting


class MeetingMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Meeting views."""

    model = Meeting
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return Meeting.objects.filter(project=self.get_project())


class MeetingListView(MeetingMixin, ListView):
    """List all meetings for a project."""

    template_name = "site_management/meeting/list.html"
    context_object_name = "meetings"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["open_count"] = self.get_queryset().filter(status="OPEN").count()
        context["closed_count"] = self.get_queryset().filter(status="CLOSED").count()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management",
                        kwargs={"pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Meetings", url=None),
        ]


class MeetingDetailView(MeetingMixin, DetailView):
    """View details of a meeting."""

    template_name = "site_management/meeting/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management",
                        kwargs={"pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(
                title="Meetings",
                url=str(
                    reverse_lazy(
                        "site_management:meeting-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=str(self.get_object()), url=None),
        ]


class MeetingCreateView(MeetingMixin, CreateView):
    """Create a new meeting."""

    template_name = "site_management/meeting/form.html"
    fields = [
        "meeting_type",
        "date",
        "key_decisions",
        "attachment",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = DateInput(attrs={"type": "date"})
        form.fields["key_decisions"].widget.attrs["placeholder"] = (
            "Summarise key decisions, actions, and outcomes from this meeting"
        )
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Meeting record created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:meeting-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management",
                        kwargs={"pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(
                title="Meetings",
                url=str(
                    reverse_lazy(
                        "site_management:meeting-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Create Meeting", url=None),
        ]


class MeetingUpdateView(MeetingMixin, UpdateView):
    """Update a meeting."""

    template_name = "site_management/meeting/form.html"
    fields = [
        "meeting_type",
        "date",
        "key_decisions",
        "attachment",
        "status",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = DateInput(attrs={"type": "date"})
        form.fields["key_decisions"].widget.attrs["placeholder"] = (
            "Summarise key decisions, actions, and outcomes from this meeting"
        )
        return form

    def form_valid(self, form):
        obj = form.save(commit=False)
        if obj.status == "CLOSED" and not obj.date_closed:
            obj.date_closed = timezone.now().date()
        elif obj.status == "OPEN":
            obj.date_closed = None
        obj.save()
        messages.success(self.request, "Meeting record updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:meeting-detail",
            kwargs={"project_pk": self.get_project().pk, "pk": self.object.pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management",
                        kwargs={"pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(
                title="Meetings",
                url=str(
                    reverse_lazy(
                        "site_management:meeting-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=str(self.get_object()), url=None),
        ]


class MeetingDeleteView(MeetingMixin, DeleteView):
    """Delete a meeting."""

    template_name = "site_management/meeting/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Meeting record deleted successfully.")
        return reverse_lazy(
            "site_management:meeting-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
