"""CRUD views for Snag List."""

from django.contrib import messages
from django.forms import DateInput
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import SnagList


class SnagListMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Snag List views."""

    model = SnagList
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return SnagList.objects.filter(project=self.get_project())

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
            BreadcrumbItem(title="Snag List", url=None),
        ]


class SnagListListView(SnagListMixin, ListView):
    """List all snag items."""

    template_name = "site_management/snag_list/list.html"
    context_object_name = "snag_items"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SnagListCreateView(SnagListMixin, CreateView):
    """Create a new snag item."""

    template_name = "site_management/snag_list/form.html"
    fields = [
        "date_raised",
        "location",
        "issue_description",
        "raised_by",
        "assigned_to",
        "deadline",
        "status",
        "remarks",
    ]
    widgets = {
        "date_raised": DateInput(attrs={"type": "date"}),
        "deadline": DateInput(attrs={"type": "date"}),
    }

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name, widget in self.widgets.items():
            form.fields[field_name].widget = widget
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "Snag item created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:snag-list-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SnagListUpdateView(SnagListMixin, UpdateView):
    """Update a snag item."""

    template_name = "site_management/snag_list/form.html"
    fields = [
        "date_raised",
        "location",
        "issue_description",
        "raised_by",
        "assigned_to",
        "deadline",
        "status",
        "remarks",
    ]
    widgets = {
        "date_raised": DateInput(attrs={"type": "date"}),
        "deadline": DateInput(attrs={"type": "date"}),
    }

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name, widget in self.widgets.items():
            form.fields[field_name].widget = widget
        return form

    def form_valid(self, form):
        messages.success(self.request, "Snag item updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:snag-list-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class SnagListDeleteView(SnagListMixin, DeleteView):
    """Delete a snag item."""

    template_name = "site_management/snag_list/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Snag item deleted successfully!")
        return reverse_lazy(
            "site_management:snag-list-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
