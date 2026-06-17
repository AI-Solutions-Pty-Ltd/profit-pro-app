"""Core views for the application."""

from typing import TYPE_CHECKING, Any, cast

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, HttpResponse
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


class HelpCenterView(LoginRequiredMixin, TemplateView):
    """View for interactive user onboarding guides and navigation hub."""

    template_name = "core/help_center.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Programmatic module metadata
        help_modules_data: list[dict[str, Any]] = [
            {
                "id": "projects",
                "title": "Project Management",
                "category": "projects",
                "description": "Create and manage construction projects, track WBS stages, and allocate key team members.",
                "icon": "building-office-2",
                "url_name": "project:project-list",
                "required_subscription": "BASIC",
                "checklist": [
                    "Navigate to Project List & click 'Add Project'",
                    "Fill in project coordinates, town, and client info",
                    "Launch the Project Setup screen to allocate roles",
                ],
            },
            {
                "id": "boq",
                "title": "Bill of Quantities (BOQ)",
                "category": "boq",
                "description": "Upload BOQ templates, configure trade rates, track client forecasts, contractual correspondence, and payment claims.",
                "icon": "document-text",
                "url_name": "bill_of_quantities:dashboard",
                "required_subscription": "BASIC",
                "checklist": [
                    "Download the standard Excel BOQ Setup Template",
                    "Upload the populated BOQ CSV template to the WBS uploader",
                    "Set up payment certificate cycles and track contractual letters",
                ],
            },
            {
                "id": "site_management",
                "title": "Site Management",
                "category": "site",
                "description": "Log daily diaries, register site weather conditions, manage subcontractor site logs, and assign site-specific tasks.",
                "icon": "clipboard-document-check",
                "url_name": "site_management:dashboard",
                "required_subscription": "BASIC",
                "checklist": [
                    "Create a daily diary entry for labor attendance",
                    "Log weather reports directly from the project site",
                    "Assign weekly tasks to subcontractors and track progress",
                ],
            },
            {
                "id": "business_dashboard",
                "title": "Business & Enterprise Controls",
                "category": "business",
                "description": "Access multi-company controls, business portfolios, and high-level client financial performance charts.",
                "icon": "building-office",
                "url_name": "project:company-dashboard",
                "required_subscription": "BUSINESS_MANAGEMENT",
                "checklist": [
                    "Configure master tenant accounts for your organization",
                    "Set up enterprise billing rules and currency settings",
                    "Review high-level aggregated cashflow charts across all projects",
                ],
            },
        ]

        evaluated_modules = []
        is_demo = getattr(user, "subscription", None) == "DEMO_TIER" or getattr(
            user, "has_demo_permission", False
        )
        is_superuser = user.is_superuser

        for module in help_modules_data:
            mod = module.copy()
            req_sub = module["required_subscription"]

            if is_superuser:
                mod["status"] = "Active"
                mod["has_access"] = True
            elif req_sub == "BUSINESS_MANAGEMENT":
                if is_demo:
                    mod["status"] = "Demo Available"
                    mod["has_access"] = True
                elif getattr(user, "subscription", None) == "BUSINESS_MANAGEMENT":
                    mod["status"] = "Active"
                    mod["has_access"] = True
                else:
                    mod["status"] = "Locked"
                    mod["has_access"] = False
            else:
                mod["status"] = "Active"
                mod["has_access"] = True

            evaluated_modules.append(mod)

        context.update(
            {
                "page_title": "Help Center & Onboarding Guides",
                "help_modules": evaluated_modules,
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


def favicon_view(request):
    """Serve favicon.ico directly from the static directory to prevent 404s when static files are not collected."""
    import os

    favicon_path = os.path.join(
        settings.BASE_DIR, "app", "core", "static", "favicon.ico"
    )
    if os.path.exists(favicon_path):
        return FileResponse(open(favicon_path, "rb"), content_type="image/x-icon")
    return HttpResponse(status=204)


def serve_media(request, path):
    """
    Secure media serving view.
    Only allows authenticated users to access sensitive folders,
    and validates project access for project-specific files.
    """
    from django.conf import settings
    from django.http import Http404
    from django.views.static import serve
    from django.contrib.auth.views import redirect_to_login

    sensitive_prefixes = (
        "project_documents/",
        "project_drawings/",
        "payment_certificates/",
        "contract_correspondences/",
        "entity_management/",
    )

    if any(path.startswith(prefix) for prefix in sensitive_prefixes):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        # Check project membership where applicable
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] in (
            "project_documents",
            "project_drawings",
            "contract_correspondences",
        ):
            try:
                project_id = int(parts[1])
                from app.Project.models import Project, Role

                project = Project.objects.filter(pk=project_id, deleted=False).first()
                if project:
                    roles = list(dict(Role.choices).keys())
                    if not request.user.has_project_role(project, roles):
                        raise Http404("You do not have permission to access this file.")
                else:
                    raise Http404("Project not found.")
            except ValueError:
                pass

    response = serve(request, path, document_root=settings.MEDIA_ROOT)

    # Intercept downloads of BOQ documents to force correct download filename format
    parts = path.split("/")
    if (
        len(parts) >= 3
        and parts[0] == "project_documents"
        and parts[2] == "BILL_OF_QUANTITIES"
    ):
        try:
            project_id = int(parts[1])
            from app.Project.models import Project, ProjectDocument

            project = Project.objects.filter(pk=project_id, deleted=False).first()
            if project:
                import os
                from django.utils import timezone

                # Try to find the document to use its creation timestamp, fallback to current time
                doc = ProjectDocument.objects.filter(project=project, file=path).first()
                if doc:
                    date_str = doc.created_at.strftime("%Y-%m-%d_%H-%M-%S")
                else:
                    date_str = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")

                ext = os.path.splitext(parts[-1])[1]
                safe_project_name = "".join(
                    c for c in project.name if c.isalnum() or c in (" ", "-", "_")
                ).strip()
                filename = f"{safe_project_name} -project-setup -{date_str}{ext}"
                response["Content-Disposition"] = f'attachment; filename="{filename}"'
        except Exception:
            pass

    return response

