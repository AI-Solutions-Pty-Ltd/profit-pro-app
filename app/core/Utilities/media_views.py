# views.py
from django.http import Http404, HttpResponseForbidden
from django.conf import settings
from django.views.static import serve
import os

from Account.models import Account


def protected_media_view(request, path):
    """
    View to serve protected media files with custom permission logic
    """

    directories = path.split("/")

    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404("File not found")

    if not directories:
        return HttpResponseForbidden("You do not have permission to access this file")

    # no auth directories - publicly accessible
    if directories[0] in ["products", "categories"]:
        return serve(request, path, document_root=settings.MEDIA_ROOT)

    # auth directories - require authenticated user
    if not request.user.is_authenticated:
        return HttpResponseForbidden("You do not have permission to access this file")

    user: Account = request.user
    
    # Staff and superusers have access to all files
    if user.is_staff or user.is_superuser:
        return serve(request, path, document_root=settings.MEDIA_ROOT)

    # Reports directory - only staff and superusers
    if directories[0] == "reports":
        if not (user.is_staff or user.is_superuser):
            return HttpResponseForbidden(
                "You do not have permission to access this file"
            )

    # Parents directory - users can only access their own files
    if directories[0] == "parents":
        try:
            parent_id = int(directories[1])
        except (ValueError, IndexError):
            return HttpResponseForbidden(
                "You do not have permission to access this file"
            )
        if user.id != parent_id:
            return HttpResponseForbidden(
                "You do not have permission to access this file"
            )

    # If all checks pass, serve the file
    return serve(request, path, document_root=settings.MEDIA_ROOT)
