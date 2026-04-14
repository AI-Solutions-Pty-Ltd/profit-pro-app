"""API views for AJAX requests."""

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views import View

from app.Account.subscription_config import Subscription
from app.BillOfQuantities.models import Bill, Package, LineItem
from app.core.Utilities.subscription_and_role_mixin import (
    SubscriptionAndRoleRequiredMixin,
)
from app.Project.models import Role


class GetBillsByStructureView(SubscriptionAndRoleRequiredMixin, View):
    """Get bills filtered by structure."""

    roles = [Role.USER, Role.CONTRACT_BOQ]
    project_slug = "project_pk"
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to handle permission failures as JSON."""
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied:
            return JsonResponse({"error": "Permission denied"}, status=403)

    def get(self, request, project_pk):
        """Return bills for a given structure."""
        project = self.get_project()
        from app.Project.production_progress.production_models import ProductionPlan

        structure_id = request.GET.get("structure_id")
        exclude_plan_id = request.GET.get("exclude_plan_id")

        if not structure_id:
            return JsonResponse({"error": "Structure ID is required"}, status=400)

        planned_bill_ids = ProductionPlan.objects.filter(
            project=project, is_archived=False, bill__isnull=False
        )
        if exclude_plan_id:
            planned_bill_ids = planned_bill_ids.exclude(pk=exclude_plan_id)
        planned_bill_ids = planned_bill_ids.values_list("bill_id", flat=True)

        bills = (
            Bill.objects.filter(structure_id=structure_id, structure__project=project)
            .exclude(id__in=planned_bill_ids)
            .values("id", "name")
        )

        return JsonResponse({"bills": list(bills)})


class GetPackagesByBillView(SubscriptionAndRoleRequiredMixin, View):
    """Get packages filtered by bill."""

    roles = [Role.USER, Role.CONTRACT_BOQ]
    project_slug = "project_pk"
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to handle permission failures as JSON."""
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied:
            return JsonResponse({"error": "Permission denied"}, status=403)

    def get(self, request, project_pk):
        """Return packages for a given bill."""
        project = self.get_project()
        from app.Project.production_progress.production_models import ProductionPlan

        bill_id = request.GET.get("bill_id")
        exclude_plan_id = request.GET.get("exclude_plan_id")

        if not bill_id:
            return JsonResponse({"error": "Bill ID is required"}, status=400)

        planned_package_ids = ProductionPlan.objects.filter(
            project=project, is_archived=False, package__isnull=False
        )
        if exclude_plan_id:
            planned_package_ids = planned_package_ids.exclude(pk=exclude_plan_id)
        planned_package_ids = planned_package_ids.values_list("package_id", flat=True)

        packages = (
            Package.objects.filter(bill_id=bill_id, bill__structure__project=project)
            .exclude(id__in=planned_package_ids)
            .values("id", "name")
        )

        return JsonResponse({"packages": list(packages)})


class GetLineItemsByPackageView(SubscriptionAndRoleRequiredMixin, View):
    """Get line items filtered by package."""

    roles = [Role.USER, Role.CONTRACT_BOQ]
    project_slug = "project_pk"
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to handle permission failures as JSON."""
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied:
            return JsonResponse({"error": "Permission denied"}, status=403)

    def get(self, request, project_pk):
        """Return line items for a given package."""
        project = self.get_project()
        from app.Project.production_progress.production_models import ProductionPlan

        package_id = request.GET.get("package_id")
        exclude_plan_id = request.GET.get("exclude_plan_id")

        if not package_id:
            return JsonResponse({"error": "Package ID is required"}, status=400)

        planned_line_item_ids = ProductionPlan.objects.filter(
            project=project, is_archived=False, line_item__isnull=False
        )
        if exclude_plan_id:
            planned_line_item_ids = planned_line_item_ids.exclude(pk=exclude_plan_id)
        planned_line_item_ids = planned_line_item_ids.values_list(
            "line_item_id", flat=True
        )

        # Only return work items (is_work=True)
        line_items = (
            LineItem.objects.filter(package_id=package_id, is_work=True, project=project)
            .exclude(id__in=planned_line_item_ids)
            .order_by("row_index")
            .values(
                "id",
                "description",
                "item_number",
                "unit_measurement",
                "budgeted_quantity",
            )
        )

        return JsonResponse({"line_items": list(line_items)})
