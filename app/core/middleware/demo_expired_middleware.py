"""Middleware to block access for expired demo tier subscriptions."""

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

from app.Account.subscription_config import Subscription


class DemoExpiredMiddleware:
    """Redirects authenticated users with expired DEMO_TIER subscriptions to a locked page."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        # Only apply to authenticated, non-superuser, non-staff users
        if user.is_authenticated and not (user.is_superuser or user.is_staff):
            # Check if subscription is DEMO_TIER and is expired
            if user.subscription == Subscription.DEMO_TIER and user.is_subscription_expired:
                # Allow access to static, media, and browser reload assets
                path = request.path
                if (
                    path.startswith(settings.STATIC_URL)
                    or (settings.MEDIA_URL and path.startswith(settings.MEDIA_URL))
                    or path.startswith("/__reload__/")
                ):
                    return self.get_response(request)

                # Get the resolved view name if possible
                try:
                    match = resolve(request.path_info)
                    view_name = match.view_name
                except Resolver404:
                    view_name = None

                # Safe list of view names
                safe_views = {
                    "users:account:demo-expired",
                    "users:auth:logout",
                }

                if view_name not in safe_views:
                    # Detect AJAX/JSON requests
                    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
                    is_json = "application/json" in request.headers.get("accept", "")
                    if is_ajax or is_json:
                        return JsonResponse(
                            {"error": "Demo trial period has expired. Please upgrade your plan."},
                            status=403
                        )
                    # Redirect standard browser requests
                    return redirect("users:account:demo-expired")

        return self.get_response(request)
