from django.urls import reverse_lazy

from .reports_views import ProductivityLogsView


class ProgressTrackingView(ProductivityLogsView):
    """View to display the data from the analysis view, with daily breakdowns."""

    template_name = "production_progress/tracking/progress_tracking.html"

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {
                "title": "Production Dashboard",
                "url": reverse_lazy(
                    "project:production-dashboard", kwargs={"project_pk": project_pk}
                ),
            },
            {"title": "Progress Tracking", "url": None},
        ]
