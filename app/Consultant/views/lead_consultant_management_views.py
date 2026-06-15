"""Views for managing Consultant Companies (Lead and regular)."""

import json

from django.contrib import messages
from django.db.models import QuerySet
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from app.Account.models import Account
from app.Consultant.views.mixins import LeadConsultantMixin
from app.core.Utilities.mixins import BreadcrumbItem
from app.Project.company.company_forms import ConsultantCompanyForm
from app.Project.models import Company


class LeadConsultantListView(LeadConsultantMixin, ListView):
    """List all lead and regular consultant companies."""

    model = Company
    template_name = "lead_consultant/lead_consultant_list.html"
    context_object_name = "lead_consultants"

    def get_queryset(self) -> QuerySet[Company]:
        user: Account = self.request.user  # type: ignore
        projects = user.get_projects
        from django.db.models import Q

        queryset = Company.objects.filter(
            Q(consultant_projects__in=projects) | Q(users=user),
            type__in=[Company.Type.LEAD_CONSULTANT, Company.Type.CONSULTANT],
        )

        project = self.get_project()
        if project:
            # Exclude consultants that are already assigned to the project
            queryset = queryset.exclude(pk__in=project.consultants.all())

        return queryset.distinct().order_by("name")

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-setup", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(title="Consultants", url=None),
        ]


class LeadConsultantCreateView(LeadConsultantMixin, CreateView):
    """Create a new consultant company."""

    model = Company
    form_class = ConsultantCompanyForm
    template_name = "lead_consultant/lead_consultant_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-setup", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Consultants",
                url=reverse(
                    "client:lead-consultant-management:lead-consultant-list",
                    kwargs={"project_pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(title="Add Consultant", url=None),
        ]

    def form_valid(self, form):
        form.instance.type = Company.Type.LEAD_CONSULTANT
        messages.success(self.request, "Consultant company created successfully.")
        response = super().form_valid(form)
        project = self.get_project()
        project.consultants.add(self.object)
        self.object.users.add(self.request.user)
        self.object.consultants.add(self.request.user)
        return response

    def get_success_url(self):
        return reverse_lazy(
            "client:lead-consultant-management:lead-consultant-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class LeadConsultantUpdateView(LeadConsultantMixin, UpdateView):
    """Update a consultant company."""

    model = Company
    form_class = ConsultantCompanyForm
    template_name = "lead_consultant/lead_consultant_form.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-setup",
                    kwargs={"pk": self.get_project().pk},
                ),
            ),
            BreadcrumbItem(
                title="Consultants",
                url=reverse(
                    "client:lead-consultant-management:lead-consultant-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title=f"Edit {self.object.name}", url=None),
        ]

    def form_valid(self, form):
        messages.success(self.request, "Consultant company updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "client:lead-consultant-management:lead-consultant-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class LeadConsultantDeleteView(LeadConsultantMixin, DeleteView):
    """Delete a consultant company."""

    model = Company
    template_name = "lead_consultant/lead_consultant_confirm_delete.html"

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        return [
            BreadcrumbItem(
                title=self.get_project().name,
                url=reverse(
                    "project:project-setup", kwargs={"pk": self.get_project().pk}
                ),
            ),
            BreadcrumbItem(
                title="Consultants",
                url=reverse(
                    "client:lead-consultant-management:lead-consultant-list",
                    kwargs={"project_pk": self.kwargs["project_pk"]},
                ),
            ),
            BreadcrumbItem(title=f"Delete {self.get_object().name}", url=None),
        ]

    def delete(self, request, *args, **kwargs):
        consultant = self.get_object()
        messages.success(
            request,
            f"Consultant company '{consultant.name}' deleted successfully.",
        )
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            "client:lead-consultant-management:lead-consultant-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )


class RevealLeadConsultantFieldView(LeadConsultantMixin, View):
    """Reveal a sensitive consultant company field securely to authorized project administrators."""

    def handle_no_permission(self):
        """Return 403 Forbidden since this is a secure JSON AJAX endpoint."""
        return JsonResponse(
            {"status": "error", "message": "Permission denied"}, status=403
        )

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body)
            field_name = body.get("field_name")
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON"}, status=400
            )

        sensitive_fields = {
            "registration_number",
            "tax_number",
            "vat_number",
            "bank_account_number",
            "bank_branch_code",
            "bank_swift_code",
        }

        if field_name not in sensitive_fields:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Invalid or non-sensitive field requested",
                },
                status=400,
            )

        try:
            consultant = Company.objects.get(
                pk=self.kwargs["company_pk"],
                type__in=[Company.Type.LEAD_CONSULTANT, Company.Type.CONSULTANT],
            )
        except Company.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Consultant company not found"},
                status=404,
            )

        val = getattr(consultant, field_name, "")
        return JsonResponse({"status": "success", "value": val})
