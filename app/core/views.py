"""Core views for the application."""

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import BaseUserCreationForm
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView

User = get_user_model()


class HomeView(TemplateView):
    """Home page view for the application."""

    template_name = "core/home.html"

    def get(self, request, *args, **kwargs):
        """Redirect consultants to dashboard, show home page for others."""
        if (
            request.user.is_authenticated
            and request.user.groups.filter(name="consultant").exists()  # type: ignore[attr-defined]
        ):
            return redirect("project:project-dashboard")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": f"Welcome to {settings.SITE_NAME or 'Profit Pro'}",
                "features": [
                    {
                        "title": "Smart Analytics",
                        "description": "Get insights into your business performance with advanced analytics.",
                        "icon": "",
                    },
                    {
                        "title": "Easy Management",
                        "description": "Manage your business operations with our intuitive interface.",
                        "icon": "",
                    },
                    {
                        "title": "Secure & reliable",
                        "description": "Your data is safe with enterprise-grade security.",
                        "icon": "",
                    },
                ],
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
                "features": [
                    {
                        "title": "Advanced Analytics Dashboard",
                        "description": "Real-time insights into your business metrics with customizable dashboards and detailed reporting.",
                        "icon": "",
                        "details": [
                            "Custom KPI tracking",
                            "Real-time data updates",
                            "Export to multiple formats",
                            "Historical trend analysis",
                        ],
                    },
                    {
                        "title": "Smart Inventory Management",
                        "description": "Keep track of your stock levels, set reorder points, and get automated alerts when running low.",
                        "icon": "",
                        "details": [
                            "Real-time stock tracking",
                            "Automated reorder alerts",
                            "Supplier management",
                            "Barcode scanning support",
                        ],
                    },
                    {
                        "title": "Customer Relationship Management",
                        "description": "Build stronger customer relationships with integrated CRM tools and communication tracking.",
                        "icon": "",
                        "details": [
                            "Customer profiles",
                            "Purchase history tracking",
                            "Communication logs",
                            "Loyalty program integration",
                        ],
                    },
                    {
                        "title": "Financial Reporting",
                        "description": "Generate comprehensive financial reports including profit & loss, balance sheets, and cash flow statements.",
                        "icon": "",
                        "details": [
                            "Automated P&L reports",
                            "Tax-ready reports",
                            "Cash flow forecasting",
                            "Multi-currency support",
                        ],
                    },
                    {
                        "title": "Mobile Access",
                        "description": "Access your business data anywhere with our responsive web application optimized for mobile devices.",
                        "icon": "",
                        "details": [
                            "Responsive design",
                            "Touch-friendly interface",
                            "Offline capability",
                            "Push notifications",
                        ],
                    },
                    {
                        "title": "Team Collaboration",
                        "description": "Work together seamlessly with role-based access control and team activity tracking.",
                        "icon": "",
                        "details": [
                            "Role-based permissions",
                            "Activity logs",
                            "Team messaging",
                            "Task assignment",
                        ],
                    },
                ],
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


class RegisterView(CreateView):
    """Registration page view for new users."""

    class RegisterForm(BaseUserCreationForm):
        username = None
        email = forms.EmailField()

        class Meta:
            model = User
            fields = ["email", "password1", "password2"]

        def clean_email(self):
            email = self.cleaned_data["email"]
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("This email is already in use.")
            return email

    template_name = "auth/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": f"Register - {settings.SITE_NAME or 'Profit Pro'}",
                "next": self.request.GET.get("next", "home"),
            }
        )
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, form.instance)
        messages.success(self.request, "Registration successful.")
        return response


class FinalAccountView(TemplateView):
    """Final account page view."""

    template_name = "core/final_account.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": f"Final Account - {settings.SITE_NAME or 'Profit Pro'}",
            }
        )
        return context


class ImpactView(TemplateView):
    """Impact page view."""

    template_name = "core/impact.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": f"Impact - {settings.SITE_NAME or 'Profit Pro'}",
            }
        )
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
