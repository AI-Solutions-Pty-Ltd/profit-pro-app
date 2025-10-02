"""Views for Project app."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.Project.forms import ProjectForm
from app.Project.models import Project


class ProjectListView(LoginRequiredMixin, ListView):
    """List all projects for the current user."""

    model = Project
    template_name = "project/project_list.html"
    context_object_name = "projects"
    paginate_by = 10

    def get_queryset(self):
        """Filter projects by current user."""
        return Project.objects.filter(
            account=self.request.user, deleted=False
        ).order_by("-created_at")


class ProjectDetailView(LoginRequiredMixin, DetailView):
    """Display a single project."""

    model = Project
    template_name = "project/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        """Filter projects by current user."""
        return Project.objects.filter(account=self.request.user, deleted=False)


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """Create a new project."""

    model = Project
    form_class = ProjectForm
    template_name = "project/project_form.html"
    success_url = reverse_lazy("project:project-list")

    def form_valid(self, form):
        """Set the account to the current user before saving."""
        form.instance.account = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing project."""

    model = Project
    form_class = ProjectForm
    template_name = "project/project_form.html"
    success_url = reverse_lazy("project:project-list")

    def get_queryset(self):
        """Filter projects by current user."""
        return Project.objects.filter(account=self.request.user, deleted=False)


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a project."""

    model = Project
    template_name = "project/project_confirm_delete.html"
    success_url = reverse_lazy("project:project-list")

    def get_queryset(self):
        """Filter projects by current user."""
        return Project.objects.filter(account=self.request.user, deleted=False)
