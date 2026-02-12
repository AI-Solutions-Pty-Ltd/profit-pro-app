"""Core views for the application."""

from typing import TYPE_CHECKING, cast

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

if TYPE_CHECKING:
    from app.Account.models import Account

User = get_user_model()


class HomeView(TemplateView):
    """Home page view for the application."""

    template_name = "core/home.html"

    def get(self, request, *args, **kwargs):
        """Redirect consultants to dashboard, show home page for others."""
        if request.user.is_authenticated:
            # Cast to Account model to access groups
            user = cast("Account", request.user)
            if (
                hasattr(user, "groups")
                and user.groups.filter(name="consultant").exists()
            ):
                return redirect("project:portfolio-dashboard")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": f"Welcome to {settings.SITE_NAME or 'Profit Pro'}",
            }
        )
        return context


class FeaturesView(TemplateView):
    """Features page view showcasing application capabilities."""

    template_name = "core/features.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": f"Features - {settings.SITE_NAME or 'Profit Pro'}",
            }
        )
        return context


class AboutView(TemplateView):
    """About page view with company information."""

    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": f"About Us - {settings.SITE_NAME or 'Profit Pro'}",
                "mission": "Empowering businesses of all sizes to achieve their full potential through intelligent, user-friendly software solutions.",
                "vision": "To become the world's most trusted business management platform, helping millions of entrepreneurs and business owners succeed.",
                "values": [
                    {
                        "title": "Customer First",
                        "description": "We put our customers at the center of everything we do, ensuring their success is our top priority.",
                        "icon": "",
                    },
                    {
                        "title": "Innovation",
                        "description": "We continuously push the boundaries of what's possible, bringing cutting-edge solutions to everyday business challenges.",
                        "icon": "",
                    },
                    {
                        "title": "Integrity",
                        "description": "We believe in transparency, honesty, and doing the right thing, even when no one is watching.",
                        "icon": "",
                    },
                    {
                        "title": "Excellence",
                        "description": "We strive for excellence in every aspect of our work, from product development to customer support.",
                        "icon": "",
                    },
                ],
                "team": [
                    {
                        "name": "Sarah Johnson",
                        "role": "CEO & Founder",
                        "bio": "15+ years of experience in business management and software development.",
                        "image": "https://via.placeholder.com/150",
                    },
                    {
                        "name": "Michael Chen",
                        "role": "CTO",
                        "bio": "Expert in scalable systems and passionate about building user-friendly technology.",
                        "image": "https://via.placeholder.com/150",
                    },
                    {
                        "name": "Emily Rodriguez",
                        "role": "Head of Customer Success",
                        "bio": "Dedicated to ensuring every customer achieves their business goals.",
                        "image": "https://via.placeholder.com/150",
                    },
                ],
            }
        )
        context["admin_email"] = settings.ADMIN_EMAIL
        return context


# Custom error handlers
def custom_404(request, exception):
    """Custom 404 error handler."""
    return render(request, "404.html", status=404)


def custom_500(request):
    """Custom 500 error handler."""
    return render(request, "500.html", status=500)


def custom_403(request, exception):
    """Custom 403 error handler."""
    return render(request, "403.html", status=403)
