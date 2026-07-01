"""Mixins for Consultant views."""

from django.db.models import Q, QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404

from app.Account.models import Account
from app.BillOfQuantities.models import PaymentCertificate
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.permissions import (
    UserHasGroupGenericMixin,
    UserHasProjectRoleGenericMixin,
)
from app.Project.models import Company, Project, Role


class ConsultantMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    permissions = ["consultant"]

    def get_clients(self):
        companies = Company.objects.filter(type=Company.Type.CLIENT)
        if not self.request.user.is_superuser:  # type: ignore
            from app.Account.subscription_config import Subscription
            if (
                self.request.user.subscription == Subscription.DEMO_TIER
                and self.request.user.is_subscription_expired
            ):
                return Company.objects.none()
            companies = companies.filter(created_by=self.request.user)
        return companies

    def get_queryset(self):
        return self.get_clients()


class ClientMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for client views."""

    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_queryset(self) -> QuerySet[Company]:
        qs = Company.objects.filter(type=Company.Type.CLIENT)
        if not self.request.user.is_superuser:
            qs = qs.filter(created_by=self.request.user)
        return qs.order_by("name")

    def get_object(self) -> Company:
        return get_object_or_404(
            self.get_queryset(), id=self.kwargs["pk"]
        )

    def get_client(self, slug="pk") -> Company:
        return get_object_or_404(
            self.get_queryset(), id=self.kwargs[slug]
        )


class ContractorMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for contractor views."""

    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_queryset(self) -> QuerySet[Company]:
        return Company.objects.filter(type=Company.Type.CONTRACTOR).order_by("name")

    def get_object(self) -> Company:
        return get_object_or_404(
            Company, id=self.kwargs["pk"], type=Company.Type.CONTRACTOR
        )

    def get_contractor(self, slug="pk") -> Company:
        return get_object_or_404(
            Company, id=self.kwargs[slug], type=Company.Type.CONTRACTOR
        )


class PaymentCertMixin(UserHasGroupGenericMixin, BreadcrumbMixin):
    permissions = ["consultant"]

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_project()
        self.client = self.get_client()
        return super().dispatch(request, *args, **kwargs)

    def get_project(self) -> Project:
        if not hasattr(self, "project"):
            self.project = get_object_or_404(
                Project,
                pk=self.kwargs["project_pk"],
            )

        if not self.project.client:
            raise Http404("Client not found")
        user: Account = self.request.user  # type: ignore
        if user.is_superuser:
            return self.project
        # Allow active DEMO_TIER users to bypass consultant check for demo projects or projects they are explicitly associated with
        if getattr(user, "has_demo_permission", False):
            if (
                getattr(self.project, "is_demo", False)
                or getattr(self.project, "name", "") == "demo 123"
                or self.project.users.filter(pk=user.pk).exists()
                or self.project.project_roles.filter(user=user).exists()
            ):
                return self.project
        if user not in self.project.client.consultants.all():
            raise Http404("User is not a consultant for this client")
        return self.project

    def get_client(self) -> Company:
        if not hasattr(self, "client"):
            self.client = self.project.client
        return self.client

    def get_queryset(self):
        project = self.get_project()
        return (
            PaymentCertificate.objects.filter(project=project)
            .order_by("-created_at")
            .select_related("project")
            .prefetch_related(
                "actual_transactions__line_item__structure",
                "actual_transactions__line_item__bill",
                "actual_transactions__line_item__package",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["client"] = self.client
        return context


class LeadConsultantMixin(UserHasProjectRoleGenericMixin, BreadcrumbMixin):
    """Mixin for lead consultant views."""

    roles = [Role.ADMIN]
    project_slug = "project_pk"

    def get_queryset(self) -> QuerySet[Company]:
        return Company.objects.filter(
            type__in=[Company.Type.LEAD_CONSULTANT, Company.Type.CONSULTANT]
        ).order_by("name")

    def get_object(self) -> Company:
        return get_object_or_404(
            Company,
            id=self.kwargs["pk"],
            type__in=[Company.Type.LEAD_CONSULTANT, Company.Type.CONSULTANT],
        )

    def get_lead_consultant(self, slug="pk") -> Company:
        return get_object_or_404(
            Company,
            id=self.kwargs[slug],
            type__in=[Company.Type.LEAD_CONSULTANT, Company.Type.CONSULTANT],
        )
