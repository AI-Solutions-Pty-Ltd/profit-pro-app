"""CRUD views for Non-Conformance Reports (NCR)."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project, Role
from app.SiteManagement.models import NonConformance


class NCRMixin(
    SubscriptionRequiredMixin, UserHasProjectRoleGenericMixin, BreadcrumbMixin
):
    """Mixin for NCR views."""

    model = NonConformance
    required_tiers = [Subscription.SITE_MANAGEMENT]
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return NonConformance.objects.filter(project=self.get_project())

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
            BreadcrumbItem(title="NCRs", url=None),
        ]


class NCRListView(NCRMixin, ListView):
    """List all NCRs."""

    template_name = "site_management/ncr/list.html"
    context_object_name = "ncrs"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class NCRCreateView(NCRMixin, CreateView):
    """Create a new NCR."""

    template_name = "site_management/ncr/form.html"
    fields = [
        "ncr_type",
        "description",
        "defect_description",
        "root_cause",
        "responsible_person",
        "corrective_action",
        "preventative_action",
        "status",
        "photo",
    ]

    def form_valid(self, form):
        form.instance.project = self.get_project()
        messages.success(self.request, "NCR created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:ncr-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class NCRUpdateView(NCRMixin, UpdateView):
    """Update an NCR."""

    template_name = "site_management/ncr/form.html"
    fields = [
        "ncr_type",
        "description",
        "defect_description",
        "root_cause",
        "responsible_person",
        "corrective_action",
        "preventative_action",
        "status",
        "photo",
    ]

    def form_valid(self, form):
        messages.success(self.request, "NCR updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:ncr-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class NCRDeleteView(NCRMixin, DeleteView):
    """Delete an NCR."""

    template_name = "site_management/ncr/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "NCR deleted successfully!")
        return reverse_lazy(
            "site_management:ncr-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
