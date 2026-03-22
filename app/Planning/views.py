"""Views for Planning & Procurement app."""

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Planning.forms import (
    DesignCategoryFileForm,
    DesignCategoryForm,
    DesignDisciplineFileForm,
    DesignDisciplineForm,
    DesignGroupFileForm,
    DesignGroupForm,
    DesignSubCategoryFileForm,
    DesignSubCategoryForm,
    TenderDocumentForm,
    WorkPackageForm,
)
from app.Planning.models import (
    DesignCategory,
    DesignCategoryFile,
    DesignDiscipline,
    DesignDisciplineFile,
    DesignGroup,
    DesignGroupFile,
    DesignSubCategory,
    DesignSubCategoryFile,
    TenderDocument,
    WorkPackage,
)
from app.Project.models import Project, Role

# =============================================================================
# Shared Mixin
# =============================================================================


class PlanningMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Base mixin for all Planning views."""

    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        """Get the project from the URL kwargs."""
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """Default breadcrumbs for Planning views."""
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
            BreadcrumbItem(title="Planning & Procurement", url=None),
        ]


# =============================================================================
# A: Work Package Views
# =============================================================================


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
        context["design_categories"] = self.object.design_categories.select_related(
            "category"
        ).all()
        context["design_subcategories"] = (
            self.object.design_subcategories.select_related("sub_category").all()
        )
        context["design_groups"] = self.object.design_groups.select_related(
            "group"
        ).all()
        context["design_disciplines"] = self.object.design_disciplines.select_related(
            "discipline"
        ).all()
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


# =============================================================================
# B: Tender Document Views
# =============================================================================


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
            "planning:work-package-detail",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["wp_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
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
            "planning:work-package-detail",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["wp_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["action"] = "Add"
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


# =============================================================================
# C: Design Development Views
# =============================================================================


class DesignListView(PlanningMixin, DetailView):
    """List all design items for a work package, categorized by L1-L4."""

    model = WorkPackage
    template_name = "planning/design/list.html"
    context_object_name = "work_package"

    def get_queryset(self):
        return WorkPackage.objects.filter(project=self.get_project())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        wp = self.object
        context["design_categories"] = wp.design_categories.select_related(
            "category"
        ).prefetch_related("files")
        context["design_subcategories"] = wp.design_subcategories.select_related(
            "sub_category"
        ).prefetch_related("files")
        context["design_groups"] = wp.design_groups.select_related(
            "group"
        ).prefetch_related("files")
        context["design_disciplines"] = wp.design_disciplines.select_related(
            "discipline"
        ).prefetch_related("files")
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        wp = self.get_object()
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
            BreadcrumbItem(
                title=wp.name,
                url=str(
                    reverse_lazy(
                        "planning:work-package-detail",
                        kwargs={"project_pk": project.pk, "pk": wp.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Design Development", url=None),
        ]


# --- Design Category (L1) ---


class DesignCategoryCreateView(PlanningMixin, CreateView):
    """Create a design category entry for a work package."""

    model = DesignCategory
    form_class = DesignCategoryForm
    template_name = "planning/design/design_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        project = self.get_project()
        form.fields["category"].queryset = project.categories.all()
        return form

    def form_valid(self, form):
        form.instance.work_package = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        messages.success(self.request, "Design category added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-list",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["wp_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["level"] = "L1 - Category"
        context["action"] = "Add"
        return context


class DesignCategoryFileUploadView(PlanningMixin, CreateView):
    """Upload a file to a design category (auto-approves)."""

    model = DesignCategoryFile
    form_class = DesignCategoryFileForm
    template_name = "planning/design/upload_form.html"

    def form_valid(self, form):
        form.instance.design_category = DesignCategory.objects.get(
            pk=self.kwargs["design_pk"]
        )
        messages.success(self.request, "File uploaded and design category approved.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-list",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["wp_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["design_item"] = DesignCategory.objects.select_related("category").get(
            pk=self.kwargs["design_pk"]
        )
        context["level"] = "L1 - Category"
        return context


# --- Design SubCategory (L2) ---


class DesignSubCategoryCreateView(PlanningMixin, CreateView):
    """Create a design subcategory entry for a work package."""

    model = DesignSubCategory
    form_class = DesignSubCategoryForm
    template_name = "planning/design/design_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        project = self.get_project()
        form.fields["sub_category"].queryset = project.subcategories.all()
        return form

    def form_valid(self, form):
        form.instance.work_package = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        messages.success(self.request, "Design subcategory added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-list",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["wp_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["level"] = "L2 - SubCategory"
        context["action"] = "Add"
        return context


class DesignSubCategoryFileUploadView(PlanningMixin, CreateView):
    """Upload a file to a design subcategory (auto-approves)."""

    model = DesignSubCategoryFile
    form_class = DesignSubCategoryFileForm
    template_name = "planning/design/upload_form.html"

    def form_valid(self, form):
        form.instance.design_sub_category = DesignSubCategory.objects.get(
            pk=self.kwargs["design_pk"]
        )
        messages.success(self.request, "File uploaded and design subcategory approved.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-list",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["wp_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["design_item"] = DesignSubCategory.objects.select_related(
            "sub_category"
        ).get(pk=self.kwargs["design_pk"])
        context["level"] = "L2 - SubCategory"
        return context


# --- Design Group (L3) ---


class DesignGroupCreateView(PlanningMixin, CreateView):
    """Create a design group entry for a work package."""

    model = DesignGroup
    form_class = DesignGroupForm
    template_name = "planning/design/design_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        project = self.get_project()
        form.fields["group"].queryset = project.groups.all()  # type: ignore
        return form

    def form_valid(self, form):
        form.instance.work_package = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        messages.success(self.request, "Design group added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-list",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["wp_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["level"] = "L3 - Group"
        context["action"] = "Add"
        return context


class DesignGroupFileUploadView(PlanningMixin, CreateView):
    """Upload a file to a design group (auto-approves)."""

    model = DesignGroupFile
    form_class = DesignGroupFileForm
    template_name = "planning/design/upload_form.html"

    def form_valid(self, form):
        form.instance.design_group = DesignGroup.objects.get(
            pk=self.kwargs["design_pk"]
        )
        messages.success(self.request, "File uploaded and design group approved.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-list",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["wp_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["design_item"] = DesignGroup.objects.select_related("group").get(
            pk=self.kwargs["design_pk"]
        )
        context["level"] = "L3 - Group"
        return context


# --- Design Discipline (L4) ---


class DesignDisciplineCreateView(PlanningMixin, CreateView):
    """Create a design discipline entry for a work package."""

    model = DesignDiscipline
    form_class = DesignDisciplineForm
    template_name = "planning/design/design_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        project = self.get_project()
        form.fields["discipline"].queryset = project.disciplines.all()
        return form

    def form_valid(self, form):
        form.instance.work_package = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        messages.success(self.request, "Design discipline added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-list",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["wp_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["level"] = "L4 - Discipline"
        context["action"] = "Add"
        return context


class DesignDisciplineFileUploadView(PlanningMixin, CreateView):
    """Upload a file to a design discipline (auto-approves)."""

    model = DesignDisciplineFile
    form_class = DesignDisciplineFileForm
    template_name = "planning/design/upload_form.html"

    def form_valid(self, form):
        form.instance.design_discipline = DesignDiscipline.objects.get(
            pk=self.kwargs["design_pk"]
        )
        messages.success(self.request, "File uploaded and design discipline approved.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-list",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["wp_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["design_item"] = DesignDiscipline.objects.select_related(
            "discipline"
        ).get(pk=self.kwargs["design_pk"])
        context["level"] = "L4 - Discipline"
        return context
