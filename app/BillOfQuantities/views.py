"""Views for Structure app."""

import pandas as pd
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
)
from django.views.generic.edit import FormView

from app.BillOfQuantities.forms import StructureExcelUploadForm, StructureForm
from app.BillOfQuantities.models import Structure
from app.Project.models import Project


class StructureDetailView(LoginRequiredMixin, DetailView):
    """Display a single structure."""

    model = Structure
    template_name = "structure/structure_detail.html"
    context_object_name = "structure"

    def get_queryset(self):
        """Filter structures by the current project."""
        return Structure.objects.filter(
            project__account=self.request.user, deleted=False
        ).select_related("project")

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_object().project
        return context


class StructureCreateView(LoginRequiredMixin, CreateView):
    """Create a new structure."""

    model = Structure
    form_class = StructureForm
    template_name = "structure/structure_form.html"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        project = get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
            deleted=False,
        )
        return project

    def form_valid(self, form):
        """Set project and add success message."""
        form.instance.project = self.get_project()
        messages.success(
            self.request, f"Structure '{form.instance.name}' created successfully!"
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to project's structure list."""
        return reverse(
            "project:project-detail",
            kwargs={"pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


class StructureUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing structure."""

    model = Structure
    form_class = StructureForm
    template_name = "structure/structure_form.html"

    def form_valid(self, form):
        """Add success message."""
        messages.success(
            self.request, f"Structure '{form.instance.name}' updated successfully!"
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to project's structure list."""
        project: Project = self.object.project
        return reverse("project:project-detail", kwargs={"pk": project.pk})

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_object().project
        return context


class StructureDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a structure."""

    model = Structure
    template_name = "structure/structure_confirm_delete.html"

    def get_queryset(self):
        """Filter structures by the current project."""
        return Structure.objects.filter(
            project__account=self.request.user, deleted=False
        )

    def form_valid(self, form):
        """Add success message."""
        structure_name = self.object.name
        messages.success(
            self.request, f"Structure '{structure_name}' deleted successfully!"
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to project's structure list."""
        return reverse("project:project-detail", kwargs={"pk": self.object.project.pk})

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_object().project
        return context


class StructureExcelUploadView(LoginRequiredMixin, FormView):
    """Upload structures from Excel file."""

    form_class = StructureExcelUploadForm
    template_name = "structure/structure_excel_upload.html"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        project = get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
            deleted=False,
        )
        return project

    def get_form_kwargs(self):
        """Pass user and project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["project"] = self.get_project()
        return kwargs

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def form_valid(self, form):
        """Process Excel file and create structures."""
        excel_file = form.cleaned_data["excel_file"]
        project = self.get_project()

        try:
            # Read Excel file
            df = pd.read_excel(excel_file)

            # Validate required columns
            if "name" not in df.columns:
                messages.error(
                    self.request,
                    "Excel file must contain a 'name' column.",
                )
                return self.form_invalid(form)

            # Create structures
            created_count = 0
            skipped_count = 0
            skipped_names = []

            for _, row in df.iterrows():
                name = str(row["name"]).strip()
                if not name or name.lower() == "nan":
                    skipped_count += 1
                    continue

                description = ""
                if "description" in df.columns:
                    desc_value = row["description"]
                    if pd.notna(desc_value):
                        description = str(desc_value).strip()

                # Check if structure already exists
                if not Structure.objects.filter(
                    project=project, name=name, deleted=False
                ).exists():
                    Structure.objects.create(
                        project=project, name=name, description=description
                    )
                    created_count += 1
                else:
                    skipped_count += 1
                    skipped_names.append(name)

            # Success message
            message_parts = []
            if created_count > 0:
                message_parts.append(f"{created_count} structure(s) created")
            if skipped_count > 0:
                message_parts.append(f"{skipped_count} skipped (empty or duplicate)")
                if skipped_names:
                    message_parts.append(f"Skipped names: {', '.join(skipped_names)}")

            if created_count > 0:
                messages.success(self.request, ". ".join(message_parts) + ".")
            else:
                messages.warning(
                    self.request,
                    "No structures were created. " + message_parts[0]
                    if message_parts
                    else "No valid data found.",
                )

            return redirect(self.get_success_url())

        except Exception as e:
            messages.error(
                self.request,
                f"Error processing Excel file: {str(e)}",
            )
            return self.form_invalid(form)

    def get_success_url(self):
        """Redirect to project's structure list."""
        return reverse(
            "project:project-detail",
            kwargs={"pk": self.get_project().pk},
        )
