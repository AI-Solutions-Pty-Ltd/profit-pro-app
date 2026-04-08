from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
)

from app.core.Utilities.mixins import BreadcrumbItem
from app.Planning.forms import (
    DesignCategoryFileForm,
    DesignCategoryForm,
    DesignDisciplineFileForm,
    DesignDisciplineForm,
    DesignGroupFileForm,
    DesignGroupForm,
    DesignSubCategoryFileForm,
    DesignSubCategoryForm,
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
)
from app.Planning.views import PlanningMixin
from app.Project.models import Project


# =============================================================================
# Overview Pages
# =============================================================================
class DesignDevelopmentOverviewView(PlanningMixin, DetailView):
    """Overview of design development across all work packages in a project."""

    model = Project
    template_name = "planning/overview/design_development.html"
    context_object_name = "work_packages"
    pk_url_kwarg = "project_pk"

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
            BreadcrumbItem(title="Design Development", url=None),
        ]


# =============================================================================
# C: Design Development Views
# =============================================================================
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
        messages.success(self.request, "Design category added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

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
                title="Design Development",
                url=str(
                    reverse_lazy(
                        "planning:design-development-overview",
                        kwargs={
                            "project_pk": self.kwargs["project_pk"],
                        },
                    )
                ),
            ),
            BreadcrumbItem(title="Add L1 Category", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
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
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        design_item = DesignCategory.objects.select_related("category").get(
            pk=self.kwargs["design_pk"]
        )
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
                title="Design Development",
                url=str(
                    reverse_lazy(
                        "planning:design-development-overview",
                        kwargs={
                            "project_pk": self.kwargs["project_pk"],
                        },
                    )
                ),
            ),
            BreadcrumbItem(title=f"Upload: {design_item.category.name}", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
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
        messages.success(self.request, "Design subcategory added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
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
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
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
        messages.success(self.request, "Design group added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
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
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
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
        messages.success(self.request, "Design discipline added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
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
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["design_item"] = DesignDiscipline.objects.select_related(
            "discipline"
        ).get(pk=self.kwargs["design_pk"])
        context["level"] = "L4 - Discipline"
        return context


# Design Edit Views


class DesignCategoryUpdateView(PlanningMixin, UpdateView):
    """Edit a design category (L1)."""

    model = DesignCategory
    form_class = DesignCategoryForm
    template_name = "planning/design/design_form.html"

    def get_queryset(self):
        return DesignCategory.objects.filter(
            category__project=self.get_project(),
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        project = self.get_project()
        form.fields["category"].queryset = project.categories.all()
        return form

    def form_valid(self, form):
        messages.success(self.request, "Design category updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

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
                title="Design Development",
                url=str(
                    reverse_lazy(
                        "planning:design-development-overview",
                        kwargs={
                            "project_pk": self.kwargs["project_pk"],
                        },
                    )
                ),
            ),
            BreadcrumbItem(title=f"Edit: {self.object.category.name}", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["level"] = "L1 - Category"
        context["action"] = "Edit"
        return context


class DesignSubCategoryUpdateView(PlanningMixin, UpdateView):
    """Edit a design subcategory (L2)."""

    model = DesignSubCategory
    form_class = DesignSubCategoryForm
    template_name = "planning/design/design_form.html"

    def get_queryset(self):
        return DesignSubCategory.objects.filter(
            sub_category__category__project=self.get_project(),
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        project = self.get_project()
        form.fields["sub_category"].queryset = project.subcategories.all()
        return form

    def form_valid(self, form):
        messages.success(self.request, "Design subcategory updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["level"] = "L2 - SubCategory"
        context["action"] = "Edit"
        return context


class DesignGroupUpdateView(PlanningMixin, UpdateView):
    """Edit a design group (L3)."""

    model = DesignGroup
    form_class = DesignGroupForm
    template_name = "planning/design/design_form.html"

    def get_queryset(self):
        return DesignGroup.objects.filter(
            group__sub_category__category__project=self.get_project(),
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        project = self.get_project()
        form.fields["group"].queryset = project.groups.all()  # type: ignore
        return form

    def form_valid(self, form):
        messages.success(self.request, "Design group updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["level"] = "L3 - Group"
        context["action"] = "Edit"
        return context


class DesignDisciplineUpdateView(PlanningMixin, UpdateView):
    """Edit a design discipline (L4)."""

    model = DesignDiscipline
    form_class = DesignDisciplineForm
    template_name = "planning/design/design_form.html"

    def get_queryset(self):
        return DesignDiscipline.objects.filter(
            discipline__project=self.get_project(),
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        project = self.get_project()
        form.fields["discipline"].queryset = project.disciplines.all()
        return form

    def form_valid(self, form):
        messages.success(self.request, "Design discipline updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["level"] = "L4 - Discipline"
        context["action"] = "Edit"
        return context


# Design Delete Views


class DesignCategoryDeleteView(PlanningMixin, DeleteView):
    """Delete a design category (L1)."""

    model = DesignCategory
    template_name = "planning/design/confirm_delete.html"

    def get_queryset(self):
        return DesignCategory.objects.filter(
            category__project=self.get_project(),
        )

    def get_success_url(self):
        messages.success(self.request, "Design category deleted successfully.")
        return reverse_lazy(
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

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
                title="Design Development",
                url=str(
                    reverse_lazy(
                        "planning:design-development-overview",
                        kwargs={
                            "project_pk": self.kwargs["project_pk"],
                        },
                    )
                ),
            ),
            BreadcrumbItem(title=f"Delete: {self.object.category.name}", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["level"] = "L1 - Category"
        return context


class DesignSubCategoryDeleteView(PlanningMixin, DeleteView):
    """Delete a design subcategory (L2)."""

    model = DesignSubCategory
    template_name = "planning/design/confirm_delete.html"

    def get_queryset(self):
        return DesignSubCategory.objects.filter(
            sub_category__category__project=self.get_project(),
        )

    def get_success_url(self):
        messages.success(self.request, "Design subcategory deleted successfully.")
        return reverse_lazy(
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["level"] = "L2 - SubCategory"
        return context


class DesignGroupDeleteView(PlanningMixin, DeleteView):
    """Delete a design group (L3)."""

    model = DesignGroup
    template_name = "planning/design/confirm_delete.html"

    def get_queryset(self):
        return DesignGroup.objects.filter(
            group__sub_category__category__project=self.get_project(),
        )

    def get_success_url(self):
        messages.success(self.request, "Design group deleted successfully.")
        return reverse_lazy(
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["level"] = "L3 - Group"
        return context


class DesignDisciplineDeleteView(PlanningMixin, DeleteView):
    """Delete a design discipline (L4)."""

    model = DesignDiscipline
    template_name = "planning/design/confirm_delete.html"

    def get_queryset(self):
        return DesignDiscipline.objects.filter(
            discipline__project=self.get_project(),
        )

    def get_success_url(self):
        messages.success(self.request, "Design discipline deleted successfully.")
        return reverse_lazy(
            "planning:design-development-overview",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["level"] = "L4 - Discipline"
        return context
