from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.core.Utilities.mixins import BreadcrumbItem
from app.Planning.forms import (
    TenderProcessForm,
    WorkPackageForm,
    WorkPackageProcessForm,
)
from app.Planning.models import (
    WorkPackage,
)
from app.Planning.views import PlanningMixin


class WorkPackageListView(PlanningMixin, ListView):
    """List all work packages for a project."""

    model = WorkPackage
    template_name = "planning/work_package/list.html"
    context_object_name = "work_packages"
    paginate_by = 20

    def get_queryset(self):
        return WorkPackage.objects.filter(project=self.get_project())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects",
                url=str(reverse_lazy("project:project-list")),
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
            BreadcrumbItem(title="Work Packages", url=None),
        ]


class WorkPackageCreateView(PlanningMixin, CreateView):
    """Create a new work package."""

    model = WorkPackage
    form_class = WorkPackageForm
    template_name = "planning/work_package/form.html"

    def form_valid(self, form):
        form.instance.project = self.get_project()
        response = super().form_valid(form)
        self.object.create_default_tender_documents()  # type: ignore
        messages.success(self.request, "Work package created successfully.")
        return response

    def get_success_url(self):
        return reverse_lazy(
            "planning:work-package-detail",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.object.pk,  # type: ignore
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["action"] = "Create"
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects",
                url=str(reverse_lazy("project:project-list")),
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
                title="Work Packages",
                url=str(
                    reverse_lazy(
                        "planning:work-package-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Create", url=None),
        ]


class WorkPackageDetailView(PlanningMixin, DetailView):
    """View work package details with tender documents and design items."""

    model = WorkPackage
    template_name = "planning/work_package/detail.html"
    context_object_name = "work_package"

    def get_queryset(self):
        return WorkPackage.objects.filter(project=self.get_project())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["tender_documents"] = self.object.tender_documents.all()
        # Design items are now managed at project level, not work package level
        context["design_categories"] = []
        context["design_subcategories"] = []
        context["design_groups"] = []
        context["design_disciplines"] = []
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects",
                url=str(reverse_lazy("project:project-list")),
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
                title="Work Packages",
                url=str(
                    reverse_lazy(
                        "planning:work-package-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=self.object.name, url=None),
        ]


class WorkPackageUpdateView(PlanningMixin, UpdateView):
    """Update a work package."""

    model = WorkPackage
    form_class = WorkPackageForm
    template_name = "planning/work_package/form.html"

    def get_queryset(self):
        return WorkPackage.objects.filter(project=self.get_project())

    def form_valid(self, form):
        messages.success(self.request, "Work package updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:work-package-detail",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.object.pk,
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["action"] = "Update"
        return context


class WorkPackageProcessUpdateView(PlanningMixin, UpdateView):
    """Edit work package process tracking dates and budget."""

    model = WorkPackage
    form_class = WorkPackageProcessForm
    template_name = "planning/work_package/process_form.html"

    def get_queryset(self):
        return WorkPackage.objects.filter(project=self.get_project())

    def form_valid(self, form):
        messages.success(self.request, "Work package process updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:work-package-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
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
                        "project:project-management", kwargs={"pk": project.pk}
                    )
                ),
            ),
            BreadcrumbItem(
                title="Work Packages",
                url=str(
                    reverse_lazy(
                        "planning:work-package-list", kwargs={"project_pk": project.pk}
                    )
                ),
            ),
            BreadcrumbItem(title=f"Edit: {self.object.name}", url=None),
        ]


class WorkPackageDeleteView(PlanningMixin, DeleteView):
    """Delete a work package."""

    model = WorkPackage
    template_name = "planning/work_package/confirm_delete.html"

    def get_queryset(self):
        return WorkPackage.objects.filter(project=self.get_project())

    def get_success_url(self):
        messages.success(self.request, "Work package deleted successfully.")
        return reverse_lazy(
            "planning:work-package-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class TenderProcessUpdateView(PlanningMixin, UpdateView):
    """Edit tender process milestone dates and completion flags."""

    model = WorkPackage
    form_class = TenderProcessForm
    template_name = "planning/work_package/tender_process_form.html"

    def get_queryset(self):
        return WorkPackage.objects.filter(project=self.get_project())

    def form_valid(self, form):
        messages.success(self.request, "Tender process updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:work-package-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
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
                        "project:project-management", kwargs={"pk": project.pk}
                    )
                ),
            ),
            BreadcrumbItem(
                title="Work Packages",
                url=str(
                    reverse_lazy(
                        "planning:work-package-list", kwargs={"project_pk": project.pk}
                    )
                ),
            ),
            BreadcrumbItem(title=f"Tender Process: {self.object.name}", url=None),
        ]
