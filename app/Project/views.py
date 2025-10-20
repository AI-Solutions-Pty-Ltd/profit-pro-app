"""Views for Project app."""

from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.forms import ProjectForm
from app.Project.models import Project


class ProjectMixin(UserHasGroupGenericMixin):
    permissions = ["contractor"]

    def get_queryset(self):
        return Project.objects.filter(
            account=self.request.user, deleted=False
        ).order_by("-created_at")

    def get_object(self):
        project = super().get_object()
        if project.account != self.request.user:
            raise Http404("You do not have permission to view this project.")
        return project


class ProjectListView(ProjectMixin, ListView):
    """List all projects for the current user."""

    model = Project
    template_name = "project/project_list.html"
    context_object_name = "projects"
    paginate_by = 10

    def get_queryset(self):
        """Filter projects by current user and search query."""
        queryset = super().get_queryset()

        # Search filter
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset


class ProjectDetailView(ProjectMixin, DetailView):
    """Display a single project."""

    model = Project
    template_name = "project/project_detail.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        """Add structures to context."""
        from django.db.models import Sum

        context = super().get_context_data(**kwargs)
        line_items = self.object.line_items.all()
        # Calculate total
        total = line_items.aggregate(total=Sum("total_price"))["total"] or 0
        context["line_items_total"] = total

        return context


class ProjectWBSDetailView(ProjectMixin, DetailView):
    """Display project WBS/BOQ detailed view."""

    model = Project
    template_name = "project/project_detail_wbs.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        """Add line items total and filter options to context."""
        from django.db.models import Sum

        from app.BillOfQuantities.models import Bill, Package, Structure

        context = super().get_context_data(**kwargs)
        project = self.get_object()

        # Get unique structures, bills, packages for dropdowns
        structures = Structure.objects.filter(project=project).distinct()
        bills = Bill.objects.filter(structure__project=project).distinct()
        packages = Package.objects.filter(bill__structure__project=project).distinct()

        # Get filter parameters
        structure_id = self.request.GET.get("structure")
        bill_id = self.request.GET.get("bill")
        package_id = self.request.GET.get("package")
        description = self.request.GET.get("description")

        # Filter line items
        line_items = project.line_items.all()
        if structure_id:
            bills = bills.filter(structure__id=structure_id)
            line_items = line_items.filter(structure_id=structure_id)
        if bill_id:
            packages = packages.filter(bill__id=bill_id)
            line_items = line_items.filter(bill_id=bill_id)
        if package_id:
            line_items = line_items.filter(package_id=package_id)
        if description:
            line_items = line_items.filter(description__icontains=description)

        # Calculate total of filtered line items
        line_items_total = line_items.aggregate(total=Sum("total_price"))["total"] or 0

        context["filtered_line_items"] = line_items
        context["line_items_total"] = line_items_total
        context["structures"] = structures
        context["bills"] = bills
        context["packages"] = packages

        return context


class ProjectCreateView(UserHasGroupGenericMixin, CreateView):
    """Create a new project."""

    model = Project
    form_class = ProjectForm
    template_name = "project/project_form.html"
    permissions = ["contractor"]

    def form_valid(self, form):
        """Set the account to the current user before saving."""
        form.instance.account = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to the project list."""
        return reverse_lazy("project:project-detail", kwargs={"pk": self.object.pk})


class ProjectUpdateView(ProjectMixin, UpdateView):
    """Update an existing project."""

    model = Project
    form_class = ProjectForm
    template_name = "project/project_form.html"

    def get_success_url(self):
        """Redirect to the project list."""
        return reverse_lazy("project:project-detail", kwargs={"pk": self.object.pk})


class ProjectDeleteView(ProjectMixin, DeleteView):
    """Delete a project."""

    model = Project
    template_name = "project/project_confirm_delete.html"
    success_url = reverse_lazy("project:project-list")
