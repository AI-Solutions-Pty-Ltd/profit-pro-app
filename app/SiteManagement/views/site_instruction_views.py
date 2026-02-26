"""CRUD views for Site Instruction."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.Account.models import Account
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models import Project, Role
from app.SiteManagement.models.site_instruction import SiteInstruction


class SiteInstructionMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for Site Instruction views."""

    model = SiteInstruction
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return SiteInstruction.objects.filter(
            project=self.get_project()
        ).select_related("issued_by", "to_user")


class SiteInstructionListView(SiteInstructionMixin, ListView):
    """List all site instructions for a project."""

    template_name = "site_management/site_instruction/list.html"
    context_object_name = "site_instructions"
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
            BreadcrumbItem(title="Site Instructions", url=None),
        ]


class SiteInstructionDetailView(SiteInstructionMixin, DetailView):
    """View details of a site instruction."""

    template_name = "site_management/site_instruction/detail.html"

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
                title="Site Instructions",
                url=str(
                    reverse_lazy(
                        "site_management:site-instruction-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=self.get_object().reference_number, url=None),
        ]


class SiteInstructionCreateView(SiteInstructionMixin, CreateView):
    """Create a new site instruction."""

    template_name = "site_management/site_instruction/form.html"
    fields = [
        "to_user",
        "subject",
        "instruction",
        "attachment",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["to_user"].queryset = Account.objects.filter(
            project_roles__project=self.get_project()
        ).distinct()
        form.fields["to_user"].label = "To"
        form.fields["subject"].widget.attrs["placeholder"] = (
            "Brief subject of the site instruction"
        )
        form.fields["instruction"].widget.attrs["placeholder"] = (
            "Detailed instruction or directive"
        )
        return form

    def form_valid(self, form):
        project = self.get_project()
        form.instance.project = project
        form.instance.issued_by = self.request.user
        messages.success(self.request, "Site instruction created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:site-instruction-list",
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
                title="Site Instructions",
                url=str(
                    reverse_lazy(
                        "site_management:site-instruction-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Create Site Instruction", url=None),
        ]


class SiteInstructionUpdateView(SiteInstructionMixin, UpdateView):
    """Update a site instruction."""

    template_name = "site_management/site_instruction/form.html"
    fields = [
        "to_user",
        "subject",
        "instruction",
        "attachment",
        "status",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["to_user"].queryset = Account.objects.filter(
            project_roles__project=self.get_project()
        ).distinct()
        form.fields["to_user"].label = "To"
        form.fields["subject"].widget.attrs["placeholder"] = (
            "Brief subject of the site instruction"
        )
        form.fields["instruction"].widget.attrs["placeholder"] = (
            "Detailed instruction or directive"
        )
        return form

    def form_valid(self, form):
        obj = form.save(commit=False)
        if obj.status == "CLOSED" and not obj.date_closed:
            obj.date_closed = timezone.now().date()
        elif obj.status == "OPEN":
            obj.date_closed = None
        obj.save()
        messages.success(self.request, "Site instruction updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "site_management:site-instruction-detail",
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
                title="Site Instructions",
                url=str(
                    reverse_lazy(
                        "site_management:site-instruction-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=self.get_object().reference_number, url=None),
        ]


class SiteInstructionDeleteView(SiteInstructionMixin, DeleteView):
    """Delete a site instruction."""

    template_name = "site_management/site_instruction/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Site instruction deleted successfully.")
        return reverse_lazy(
            "site_management:site-instruction-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
