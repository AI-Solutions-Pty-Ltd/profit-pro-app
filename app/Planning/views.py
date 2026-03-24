"""Views for Planning & Procurement app."""

import json

from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
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
    TenderDocumentFileForm,
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
    TenderDocumentFile,
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


class TenderProcessSectionCompleteAPIView(PlanningMixin, View):
    """Update completion state for a tender process section on a work package."""

    section_to_field = {
        "applied_to_advert": "applied_to_advert_completed",
        "site_inspection": "site_inspection_completed",
        "tender_close": "tender_close_completed",
        "tender_evaluation": "tender_evaluation_completed",
        "award": "award_completed",
        "contract_signing": "contract_signing_completed",
        "mobilization": "mobilization_completed",
    }

    @staticmethod
    def _to_bool(value: str | bool | None) -> bool | None:
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
        return None

    def post(self, request, project_pk: int, wp_pk: int):
        project = self.get_project()
        work_package = WorkPackage.objects.filter(project=project, pk=wp_pk).first()
        if work_package is None:
            return JsonResponse(
                {"success": False, "message": "Work package not found."}, status=404
            )

        payload: dict[str, str | bool | None] = {}
        if (request.content_type or "").startswith("application/json"):
            try:
                payload = json.loads(request.body or "{}")
            except json.JSONDecodeError:
                return JsonResponse(
                    {"success": False, "message": "Invalid JSON payload."},
                    status=400,
                )

        section = str(payload.get("section") or request.POST.get("section") or "")
        section = section.strip().lower()
        if section not in self.section_to_field:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Invalid section.",
                    "allowed_sections": sorted(self.section_to_field.keys()),
                },
                status=400,
            )

        requested_completed = payload.get("completed")
        if requested_completed is None:
            requested_completed = request.POST.get("completed")

        completed = self._to_bool(requested_completed)
        field_name = self.section_to_field[section]
        current_value = bool(getattr(work_package, field_name))
        next_value = (not current_value) if completed is None else completed

        setattr(work_package, field_name, next_value)
        work_package.save(update_fields=[field_name])

        statuses = {
            key: bool(getattr(work_package, value))
            for key, value in self.section_to_field.items()
        }
        return JsonResponse(
            {
                "success": True,
                "message": "Section completion updated.",
                "work_package_id": work_package.pk,
                "section": section,
                "completed": next_value,
                "statuses": statuses,
            }
        )


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
            "planning:work-package-detail",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "pk": self.kwargs["wp_pk"],
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
                title="Work Packages",
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

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        work_package = self.object
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
                title="Work Packages",
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
            BreadcrumbItem(title="Design Development", url=None),
        ]

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

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        work_package = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
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
            BreadcrumbItem(
                title=work_package.name,
                url=str(
                    reverse_lazy(
                        "planning:work-package-detail",
                        kwargs={"project_pk": project.pk, "pk": work_package.pk},
                    )
                ),
            ),
            BreadcrumbItem(
                title="Design Development",
                url=str(
                    reverse_lazy(
                        "planning:design-list",
                        kwargs={"project_pk": project.pk, "pk": work_package.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Add L1 Category", url=None),
        ]

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

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        work_package = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
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
                title="Work Packages",
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
            BreadcrumbItem(
                title="Design Development",
                url=str(
                    reverse_lazy(
                        "planning:design-list",
                        kwargs={"project_pk": project.pk, "pk": work_package.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=f"Upload: {design_item.category.name}", url=None),
        ]

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


# Design Edit Views


class DesignCategoryUpdateView(PlanningMixin, UpdateView):
    """Edit a design category (L1)."""

    model = DesignCategory
    form_class = DesignCategoryForm
    template_name = "planning/design/design_form.html"

    def get_queryset(self):
        return DesignCategory.objects.filter(
            work_package__project=self.get_project(),
            work_package_id=self.kwargs["wp_pk"],
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
            "planning:design-list",
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
            BreadcrumbItem(
                title=work_package.name,
                url=str(
                    reverse_lazy(
                        "planning:work-package-detail",
                        kwargs={"project_pk": project.pk, "pk": work_package.pk},
                    )
                ),
            ),
            BreadcrumbItem(
                title="Design Development",
                url=str(
                    reverse_lazy(
                        "planning:design-list",
                        kwargs={"project_pk": project.pk, "pk": work_package.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=f"Edit: {self.object.category.name}", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
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
            work_package__project=self.get_project(),
            work_package_id=self.kwargs["wp_pk"],
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
        context["action"] = "Edit"
        return context


class DesignGroupUpdateView(PlanningMixin, UpdateView):
    """Edit a design group (L3)."""

    model = DesignGroup
    form_class = DesignGroupForm
    template_name = "planning/design/design_form.html"

    def get_queryset(self):
        return DesignGroup.objects.filter(
            work_package__project=self.get_project(),
            work_package_id=self.kwargs["wp_pk"],
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
        context["action"] = "Edit"
        return context


class DesignDisciplineUpdateView(PlanningMixin, UpdateView):
    """Edit a design discipline (L4)."""

    model = DesignDiscipline
    form_class = DesignDisciplineForm
    template_name = "planning/design/design_form.html"

    def get_queryset(self):
        return DesignDiscipline.objects.filter(
            work_package__project=self.get_project(),
            work_package_id=self.kwargs["wp_pk"],
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
        context["action"] = "Edit"
        return context


# Design Delete Views


class DesignCategoryDeleteView(PlanningMixin, DeleteView):
    """Delete a design category (L1)."""

    model = DesignCategory
    template_name = "planning/design/confirm_delete.html"

    def get_queryset(self):
        return DesignCategory.objects.filter(
            work_package__project=self.get_project(),
            work_package_id=self.kwargs["wp_pk"],
        )

    def get_success_url(self):
        messages.success(self.request, "Design category deleted successfully.")
        return reverse_lazy(
            "planning:design-list",
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
            BreadcrumbItem(
                title=work_package.name,
                url=str(
                    reverse_lazy(
                        "planning:work-package-detail",
                        kwargs={"project_pk": project.pk, "pk": work_package.pk},
                    )
                ),
            ),
            BreadcrumbItem(
                title="Design Development",
                url=str(
                    reverse_lazy(
                        "planning:design-list",
                        kwargs={"project_pk": project.pk, "pk": work_package.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=f"Delete: {self.object.category.name}", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["work_package"] = WorkPackage.objects.get(pk=self.kwargs["wp_pk"])
        context["level"] = "L1 - Category"
        return context


class DesignSubCategoryDeleteView(PlanningMixin, DeleteView):
    """Delete a design subcategory (L2)."""

    model = DesignSubCategory
    template_name = "planning/design/confirm_delete.html"

    def get_queryset(self):
        return DesignSubCategory.objects.filter(
            work_package__project=self.get_project(),
            work_package_id=self.kwargs["wp_pk"],
        )

    def get_success_url(self):
        messages.success(self.request, "Design subcategory deleted successfully.")
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
        return context


class DesignGroupDeleteView(PlanningMixin, DeleteView):
    """Delete a design group (L3)."""

    model = DesignGroup
    template_name = "planning/design/confirm_delete.html"

    def get_queryset(self):
        return DesignGroup.objects.filter(
            work_package__project=self.get_project(),
            work_package_id=self.kwargs["wp_pk"],
        )

    def get_success_url(self):
        messages.success(self.request, "Design group deleted successfully.")
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
        return context


class DesignDisciplineDeleteView(PlanningMixin, DeleteView):
    """Delete a design discipline (L4)."""

    model = DesignDiscipline
    template_name = "planning/design/confirm_delete.html"

    def get_queryset(self):
        return DesignDiscipline.objects.filter(
            work_package__project=self.get_project(),
            work_package_id=self.kwargs["wp_pk"],
        )

    def get_success_url(self):
        messages.success(self.request, "Design discipline deleted successfully.")
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
        return context


# =============================================================================
# Overview Pages
# =============================================================================


class DesignDevelopmentOverviewView(PlanningMixin, ListView):
    """Overview of design development across all work packages in a project."""

    model = WorkPackage
    template_name = "planning/overview/design_development.html"
    context_object_name = "work_packages"

    def get_queryset(self):
        project = self.get_project()
        return WorkPackage.objects.filter(project=project).prefetch_related(
            "design_categories__files",
            "design_categories__category",
            "design_subcategories__files",
            "design_subcategories__sub_category",
            "design_groups__files",
            "design_groups__group",
            "design_disciplines__files",
            "design_disciplines__discipline",
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
            BreadcrumbItem(title="Design Development Overview", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project

        cat_lookup = {
            cat.pk: cat
            for cat in project.categories.prefetch_related(
                "subcategories__groups"
            ).all()
        }
        disciplines = project.disciplines.all()

        for wp in context["work_packages"]:
            subcat_map: dict = {}
            for dsc in wp.design_subcategories.all():
                subcat_map.setdefault(dsc.sub_category_id, []).append(dsc)

            group_map: dict = {}
            for dg in wp.design_groups.all():
                group_map.setdefault(dg.group_id, []).append(dg)

            for dc in wp.design_categories.all():
                category = cat_lookup.get(dc.category_id)
                subcats_data = []
                if category:
                    for subcat in category.subcategories.all():
                        subcat_designs = subcat_map.get(subcat.pk, [])
                        groups_data = [
                            {"group": group, "designs": group_map.get(group.pk, [])}
                            for group in subcat.groups.all()
                            if group_map.get(group.pk)
                        ]
                        if subcat_designs or groups_data:
                            subcats_data.append(
                                {
                                    "subcat": subcat,
                                    "designs": subcat_designs,
                                    "groups": groups_data,
                                }
                            )
                dc.subcats = subcats_data

            disc_map: dict = {}
            for dd in wp.design_disciplines.all():
                disc_map.setdefault(dd.discipline_id, []).append(dd)

            wp.disciplines_data = [
                {"discipline": disc, "designs": disc_map[disc.pk]}
                for disc in disciplines
                if disc.pk in disc_map
            ]

        return context


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


class TenderProcessOverviewView(PlanningMixin, ListView):
    """Overview of tender process timeline across all work packages in a project."""

    model = WorkPackage
    template_name = "planning/overview/tender_process.html"
    context_object_name = "work_packages"

    def get_queryset(self):
        project = self.get_project()
        return WorkPackage.objects.filter(project=project).order_by(
            "applied_to_advert_start_date"
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
            BreadcrumbItem(title="Tender Process Overview", url=None),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
