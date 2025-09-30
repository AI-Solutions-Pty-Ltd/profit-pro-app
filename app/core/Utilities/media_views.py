# views.py
import os

from django.conf import settings
from django.http import Http404, HttpResponseForbidden
from django.views.static import serve
from rest_framework.authtoken.models import Token

from Account.models import Account


def protected_media_view(request, path):
    """
    View to serve protected media files with custom permission logic
    """

    directories = path.split("/")
    token = request.GET.get("token")

    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404("File not found")

    if not directories:
        return HttpResponseForbidden("You do not have permission to access this file")

    # no auth directories
    if directories[0] in ["products", "categories"]:
        return serve(request, path, document_root=settings.MEDIA_ROOT)

    # auth directories
    try:
        token = Token.objects.get(key=token)
    except Token.DoesNotExist:
        return HttpResponseForbidden("You do not have permission to access this file")

    user: Account = token.user
    if user.is_staff or user.is_superuser:
        return serve(request, path, document_root=settings.MEDIA_ROOT)

    if directories[0] == "reports":
        if not user.is_staff or user.is_superuser:
            return HttpResponseForbidden(
                "You do not have permission to access this file"
            )

    if directories[0] == "parents":
        try:
            parent_id = int(directories[1])
        except ValueError:
            return HttpResponseForbidden(
                "You do not have permission to access this file"
            )
        if user.id != parent_id:
            return HttpResponseForbidden(
                "You do not have permission to access this file"
            )

    # If all checks pass, serve the file
    return serve(request, path, document_root=settings.MEDIA_ROOT)
