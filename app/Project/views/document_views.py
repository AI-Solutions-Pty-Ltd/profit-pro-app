"""Views for managing Project Documents."""

from typing import Any

from django import forms
from django.contrib import messages
from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView

from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.forms import ProjectDocumentForm
from app.Project.models import Project, ProjectDocument
from app.Project.models.project_roles import Role


class DocumentMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for document views."""

    def get_roles(self):
        """Get required roles based on document category."""
        category = self.get_category()
        role_map = {
            "CONTRACT_DOCUMENTS": [Role.CONTRACT_DOCUMENTS, Role.ADMIN, Role.USER],
            "STAGE_GATE_APPROVAL": [Role.STAGE_GATE_APPROVALS, Role.ADMIN, Role.USER],
            "OTHER": [Role.OTHER_DOCUMENTS, Role.ADMIN, Role.USER],
        }
        return role_map.get(category, [Role.ADMIN, Role.USER])

    @property
    def roles(self):
        return self.get_roles()

    @property
    def project_slug(self):
        return "project_pk"

    def get_project(self) -> Project:
        """Get the project for the current view."""
        if not hasattr(self, "project"):
            self.project = get_object_or_404(
                Project,
                pk=self.kwargs["project_pk"],
                users=self.request.user,
            )
        return self.project

    def get_category(self) -> str:
        """Get the document category from URL kwargs."""
        category = self.kwargs.get("category", "")
        if category and category not in dict(ProjectDocument.Category.choices):
            raise Http404("Invalid document category.")
        return category

    def get_category_display(self) -> Any:
        """Get the human-readable category name."""
        return dict(ProjectDocument.Category.choices).get(self.get_category(), "")

    def get_queryset(self) -> QuerySet[ProjectDocument]:
        """Filter documents by project and category."""
        project = self.get_project()
        category = self.get_category()
        documents = ProjectDocument.objects.filter(
            project=project,
        ).order_by("-created_at")
        if category and category == "OTHER":
            documents = documents.exclude(
                category__in=[
                    ProjectDocument.Category.CONTRACT_DOCUMENTS,
                    ProjectDocument.Category.STAGE_GATE_APPROVAL,
                ],
            )
        return documents


class DocumentListView(DocumentMixin, ListView):
    """List all documents for a project in a specific category."""

    model = ProjectDocument
    template_name = "document/document_list.html"
    context_object_name = "documents"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": self.get_project().name,
                "url": reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            },
            {"title": self.get_category_display(), "url": None},
        ]

    def get_context_data(self, **kwargs):
        """Add project and category to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["category"] = self.get_category()
        context["category_display"] = self.get_category_display()
        return context


class DocumentCreateView(DocumentMixin, CreateView):
    """Upload a new document."""

    model = ProjectDocument
    form_class = ProjectDocumentForm
    template_name = "document/document_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": self.get_project().name,
                "url": reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            },
            {
                "title": self.get_category_display(),
                "url": reverse(
                    "project:document-list",
                    kwargs={
                        "project_pk": self.get_project().pk,
                        "category": self.get_category(),
                    },
                ),
            },
            {"title": "Upload Document", "url": None},
        ]

    def get_initial(self):
        """Set initial category value from URL."""
        initial = super().get_initial()
        category = self.get_category()
        if category != "OTHER":
            initial["category"] = category
        return initial

    def get_context_data(self, **kwargs):
        """Add project and category to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["category"] = self.get_category()
        context["category_display"] = self.get_category_display()
        # Hide category field in form if not in "OTHER" section
        if self.get_category() != "OTHER":
            context["form"].fields["category"].widget = forms.HiddenInput()
        else:
            # In OTHER view, exclude CONTRACT_DOCUMENTS and STAGE_GATE_APPROVAL
            excluded_categories = [
                ProjectDocument.Category.CONTRACT_DOCUMENTS,
                ProjectDocument.Category.STAGE_GATE_APPROVAL,
            ]
            context["form"].fields["category"].choices = [
                (value, label)
                for value, label in ProjectDocument.Category.choices
                if value not in excluded_categories
            ]
        return context

    def form_valid(self, form):
        """Set project and uploaded_by before saving."""
        form.instance.project = self.get_project()
        # Set category from URL if this is a category-specific upload
        if self.get_category() != "OTHER":
            form.instance.category = self.get_category()
        form.instance.uploaded_by = self.request.user
        messages.success(
            self.request,
            f"Document '{form.instance.title}' has been uploaded successfully.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to the document list."""
        return reverse_lazy(
            "project:document-list",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "category": self.get_category(),
            },
        )


class DocumentDeleteView(DocumentMixin, DeleteView):
    """Delete a document."""

    model = ProjectDocument
    template_name = "document/document_confirm_delete.html"

    def get_object(self: "DocumentDeleteView") -> ProjectDocument:
        """Get document and verify project ownership."""
        document = get_object_or_404(
            ProjectDocument,
            pk=self.kwargs["pk"],
            project__pk=self.kwargs["project_pk"],
            category=self.get_category(),
        )
        if self.request.user not in document.project.users:
            raise Http404("You do not have permission to delete this document.")
        return document

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        document = self.get_object()
        return [
            {"title": "Projects", "url": reverse("project:portfolio-dashboard")},
            {
                "title": self.get_project().name,
                "url": reverse(
                    "project:project-management", kwargs={"pk": self.get_project().pk}
                ),
            },
            {
                "title": self.get_category_display(),
                "url": reverse(
                    "project:document-list",
                    kwargs={
                        "project_pk": self.get_project().pk,
                        "category": self.get_category(),
                    },
                ),
            },
            {"title": f"Delete: {document.title}", "url": None},
        ]

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["category_display"] = self.get_category_display()
        return context

    def form_valid(self: "DocumentDeleteView", form):
        """Soft delete the document."""
        document = self.get_object()
        document.soft_delete()
        messages.success(
            self.request, f"Document '{document.title}' has been deleted successfully."
        )
        return redirect(str(self.get_success_url()))

    def get_success_url(self):
        """Redirect to the document list."""
        return reverse_lazy(
            "project:document-list",
            kwargs={
                "project_pk": self.kwargs["project_pk"],
                "category": self.get_category(),
            },
        )
