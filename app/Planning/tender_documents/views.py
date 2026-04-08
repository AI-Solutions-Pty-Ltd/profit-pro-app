from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    UpdateView,
)

from app.core.Utilities.mixins import BreadcrumbItem
from app.Planning.forms import (
    TenderDocumentFileForm,
    TenderDocumentForm,
)
from app.Planning.models import (
    TenderDocument,
    TenderDocumentFile,
    WorkPackage,
)
from app.Planning.views import PlanningMixin


class TenderDocumentationOverviewView(PlanningMixin, ListView):
    """Overview of tender documentation across all work packages in a project."""

    model = WorkPackage
    template_name = "planning/overview/tender_documentation.html"
    context_object_name = "work_packages"

    def get_queryset(self):
        project = self.get_project()
        return WorkPackage.objects.filter(project=project).prefetch_related(
            "tender_documents"
        )

    def get_breadcrumbs(self):
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects",
                url=str(reverse_lazy("project:project-list")),
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(reverse_lazy("project:project-management", args=[project.pk])),
            ),
            BreadcrumbItem(title="Tender Documentation Overview", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class TenderDocumentUpdateView(PlanningMixin, UpdateView):
    """Update a tender document (edit name, upload file, set dates)."""

    model = TenderDocument
    form_class = TenderDocumentForm
    template_name = "planning/tender_document/form.html"

    def get_queryset(self):
        return TenderDocument.objects.filter(
            work_package__project=self.get_project(),
            work_package_id=self.kwargs["wp_pk"],
        )

    def form_valid(self, form):
        messages.success(self.request, "Tender document updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:tender-documentation-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management", kwargs={"pk": project.pk}
                    )
                ),
            ),
            BreadcrumbItem(
                title="Tender Document Overview",
                url=str(
                    reverse_lazy(
                        "planning:tender-documentation-overview",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=f"Edit: {self.object.name}", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["action"] = "Edit"
        return context


class TenderDocumentCreateView(PlanningMixin, CreateView):
    """Create a new tender document for a work package."""

    model = TenderDocument
    form_class = TenderDocumentForm
    template_name = "planning/tender_document/form.html"

    def form_valid(self, form):
        form.instance.work_package = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        messages.success(self.request, "Tender document added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:tender-documentation-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management", kwargs={"pk": project.pk}
                    )
                ),
            ),
            BreadcrumbItem(
                title="Tender Document Overview",
                url=str(
                    reverse_lazy(
                        "planning:tender-documentation-overview",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Add Tender Document", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["action"] = "Add"
        return context


class TenderDocumentFileUploadView(PlanningMixin, CreateView):
    """Upload a file to a tender document."""

    model = TenderDocumentFile
    form_class = TenderDocumentFileForm
    template_name = "planning/tender_document/file_upload.html"

    def form_valid(self, form):
        form.instance.tender_document = TenderDocument.objects.get(
            pk=self.kwargs["doc_pk"]
        )
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, "File uploaded successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:tender-documentation-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        tender_doc = TenderDocument.objects.get(pk=self.kwargs["doc_pk"])
        return [
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management", kwargs={"pk": project.pk}
                    )
                ),
            ),
            BreadcrumbItem(
                title="Tender Document Overview",
                url=str(
                    reverse_lazy(
                        "planning:tender-documentation-overview",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=f"Upload: {tender_doc.name}", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["tender_document"] = TenderDocument.objects.get(
            pk=self.kwargs["doc_pk"]
        )
        return context


class TenderDocumentDeleteView(PlanningMixin, DeleteView):
    """Delete a tender document."""

    model = TenderDocument
    template_name = "planning/tender_document/confirm_delete.html"

    def get_queryset(self):
        return TenderDocument.objects.filter(
            work_package__project=self.get_project(),
            work_package_id=self.kwargs["wp_pk"],
        )

    def get_success_url(self):
        messages.success(self.request, "Tender document deleted successfully.")
        return reverse_lazy(
            "planning:work-package-detail",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["wp_pk"],
            },
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        work_package = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        return [
            BreadcrumbItem(
                title="Projects",
                url=str(reverse_lazy("project:project-list")),
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
                title="Procurement Packages",
                url=str(
                    reverse_lazy(
                        "planning:work-package-list", kwargs={"project_pk": project.pk}
                    )
                ),
            ),
            BreadcrumbItem(
                title=work_package.name,
                url=str(
                    reverse_lazy(
                        "planning:work-package-detail",
                        kwargs={"project_pk": project.pk, "pk": work_package.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=f"Delete: {self.object.name}", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
