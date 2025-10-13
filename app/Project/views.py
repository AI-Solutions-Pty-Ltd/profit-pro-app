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
        """Filter projects by current user and prefetch structures."""
        return Project.objects.filter(
            account=self.request.user, deleted=False
        ).prefetch_related("structures")

    def get_context_data(self, **kwargs):
        """Add structures to context."""
        from django.db.models import Sum

        context = super().get_context_data(**kwargs)
        line_items = self.object.line_items.all()
        # Calculate total
        total = line_items.aggregate(total=Sum("total_price"))["total"] or 0
        context["line_items_total"] = total

        return context


class ProjectWBSDetailView(LoginRequiredMixin, DetailView):
    """Display project WBS/BOQ detailed view."""

    model = Project
    template_name = "project/project_detail_wbs.html"
    context_object_name = "project"

    def get_queryset(self):
        """Filter projects by current user."""
        return Project.objects.filter(account=self.request.user, deleted=False)

    def get_context_data(self, **kwargs):
        """Add line items total to context."""
        from django.db.models import Sum

        context = super().get_context_data(**kwargs)
        project = self.get_object()

        # Calculate total of all line items
        line_items_total = (
            project.line_items.aggregate(total=Sum("total_price"))["total"] or 0
        )
        context["line_items_total"] = line_items_total

        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """Create a new project."""

    model = Project
    form_class = ProjectForm
    template_name = "project/project_form.html"

    def form_valid(self, form):
        """Set the account to the current user before saving."""
        form.instance.account = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to the project list."""
        return reverse_lazy("project:project-detail", kwargs={"pk": self.object.pk})


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing project."""

    model = Project
    form_class = ProjectForm
    template_name = "project/project_form.html"

    def get_queryset(self):
        """Filter projects by current user."""
        return Project.objects.filter(account=self.request.user, deleted=False)

    def get_success_url(self):
        """Redirect to the project list."""
        return reverse_lazy("project:project-detail", kwargs={"pk": self.object.pk})


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a project."""

    model = Project
    template_name = "project/project_confirm_delete.html"
    success_url = reverse_lazy("project:project-list")

    def get_queryset(self):
        """Filter projects by current user."""
        return Project.objects.filter(account=self.request.user, deleted=False)
