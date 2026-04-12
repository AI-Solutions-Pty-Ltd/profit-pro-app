from .reports_views import ProductivityLogsView


class ProgressTrackingView(ProductivityLogsView):
    """View to display the data from the analysis view, with daily breakdowns."""

    template_name = "production_progress/log/progress_tracking.html"
