from typing import TypedDict

from django.views.generic import View


class BreadcrumbItem(TypedDict):
    """TypedDict for breadcrumb items with required 'title' and 'url' keys."""

    title: str
    url: str | None


class BreadcrumbMixin(View):
    """
    Mixin to add breadcrumbs to view context.

    Usage in views:
    class ProjectDetailView(BreadcrumbMixin, DetailView):
        def get_breadcrumbs(self):
            project = self.get_object()
            return [
                {'title': 'Projects', 'url': 'project:portfolio-list'},
                {'title': 'Project Details', 'url': 'project:project-management'},
                {'title': project.name, 'url': None}
            ]
    """

    def get_context_data(self: "BreadcrumbMixin", **kwargs):
        context = super().get_context_data(**kwargs)  # type: ignore
        context["breadcrumbs"] = self.get_breadcrumbs()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        """
        Override this method in your view to define breadcrumbs.
        Should return a list of BreadcrumbItem dicts with 'title' and 'url' keys.
        Current page should have url=None.
        """
        return []
