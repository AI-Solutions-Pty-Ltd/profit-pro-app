"""API views for AJAX requests."""

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views import View

from app.BillOfQuantities.models import Bill, Package
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.Project.models.project_roles import Role


class GetBillsByStructureView(UserHasProjectRoleGenericMixin, View):
    """Get bills filtered by structure."""

    roles = [Role.USER, Role.CONTRACT_BOQ]
    project_slug = "project_pk"

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to handle permission failures as JSON."""
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied:
            return JsonResponse({"error": "Permission denied"}, status=403)

    def get(self, request, project_pk):
        """Return bills for a given structure."""
        project = self.get_project()

        structure_id = request.GET.get("structure_id")
        if not structure_id:
            return JsonResponse({"error": "Structure ID is required"}, status=400)
        bills = Bill.objects.filter(
            structure_id=structure_id, structure__project=project
        ).values("id", "name")

        return JsonResponse({"bills": list(bills)})


class GetPackagesByBillView(UserHasProjectRoleGenericMixin, View):
    """Get packages filtered by bill."""

    roles = [Role.USER, Role.CONTRACT_BOQ]
    project_slug = "project_pk"

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to handle permission failures as JSON."""
        try:
            return super().dispatch(request, *args, **kwargs)
        except PermissionDenied:
            return JsonResponse({"error": "Permission denied"}, status=403)

    def get(self, request, project_pk):
        """Return packages for a given bill."""
        project = self.get_project()

        bill_id = request.GET.get("bill_id")
        if not bill_id:
            return JsonResponse({"error": "Bill ID is required"}, status=400)

        packages = Package.objects.filter(
            bill_id=bill_id, bill__structure__project=project
        ).values("id", "name")

        return JsonResponse({"packages": list(packages)})
