"""API views for AJAX requests."""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from app.BillOfQuantities.models import Bill, Package
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Project


class GetBillsByStructureView(UserHasGroupGenericMixin, View):
    """Get bills filtered by structure."""

    permissions = ["contractor"]

    def get(self, request, project_pk):
        """Return bills for a given structure."""
        # Verify user has access to this project
        project = get_object_or_404(Project, pk=project_pk, users=request.user)

        # Verify user is in contractor group
        if not request.user.groups.filter(name="contractor").exists():
            return JsonResponse({"error": "Permission denied"}, status=403)

        structure_id = request.GET.get("structure_id")
        if not structure_id:
            return JsonResponse({"error": "Structure ID is required"}, status=400)
        bills = Bill.objects.filter(
            structure_id=structure_id, structure__project=project
        ).values("id", "name")

        return JsonResponse({"bills": list(bills)})


class GetPackagesByBillView(UserHasGroupGenericMixin, View):
    """Get packages filtered by bill."""

    permissions = ["contractor"]

    def get(self, request, project_pk):
        """Return packages for a given bill."""
        # Verify user has access to this project
        project = get_object_or_404(Project, pk=project_pk, users=request.user)

        # Verify user is in contractor group
        if not request.user.groups.filter(name="contractor").exists():
            return JsonResponse({"error": "Permission denied"}, status=403)

        bill_id = request.GET.get("bill_id")
        if not bill_id:
            return JsonResponse({"error": "Bill ID is required"}, status=400)

        packages = Package.objects.filter(
            bill_id=bill_id, bill__structure__project=project
        ).values("id", "name")

        return JsonResponse({"packages": list(packages)})
