import os
from base64 import b64encode
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from xhtml2pdf import pisa


def link_callback(src_attr, *args):
    """
    Returns the image data for use by the pdf renderer
    """
    # Handle data URLs (already base64 encoded)
    if src_attr.startswith("data:image"):
        return src_attr

    full_path = None

    # Resolve media files
    if settings.MEDIA_URL in src_attr:
        media_path = src_attr[
            src_attr.find(settings.MEDIA_URL) + len(settings.MEDIA_URL) :
        ]
        full_path = os.path.join(settings.MEDIA_ROOT, media_path)
    elif src_attr.startswith("media/"):
        media_path = src_attr[len("media/") :]
        full_path = os.path.join(settings.MEDIA_ROOT, media_path)

    # Resolve static files
    elif settings.STATIC_URL in src_attr:
        static_path = src_attr[
            src_attr.find(settings.STATIC_URL) + len(settings.STATIC_URL) :
        ]
        for static_dir in getattr(settings, "STATICFILES_DIRS", []):
            candidate = os.path.join(static_dir, static_path)
            if os.path.exists(candidate):
                full_path = candidate
                break
        if not full_path and getattr(settings, "STATIC_ROOT", None):
            full_path = os.path.join(settings.STATIC_ROOT, static_path)
    elif src_attr.startswith("static/"):
        static_path = src_attr[len("static/") :]
        for static_dir in getattr(settings, "STATICFILES_DIRS", []):
            candidate = os.path.join(static_dir, static_path)
            if os.path.exists(candidate):
                full_path = candidate
                break
        if not full_path and getattr(settings, "STATIC_ROOT", None):
            full_path = os.path.join(settings.STATIC_ROOT, static_path)

    # Load and encode file if it exists
    if full_path and os.path.exists(full_path):
        ext = os.path.splitext(full_path)[1].lower()
        mime_type = "image/jpeg"
        if ext == ".png":
            mime_type = "image/png"
        elif ext == ".gif":
            mime_type = "image/gif"
        elif ext == ".svg":
            mime_type = "image/svg+xml"

        with open(full_path, "rb") as f:
            img_data = f.read()
        return f"data:{mime_type};base64,{b64encode(img_data).decode()}"

    # Default: return empty string to avoid errors
    return ""


def generate_pdf(html_content) -> ContentFile:
    pdf_file = BytesIO()
    pisa.CreatePDF(html_content, dest=pdf_file, link_callback=link_callback)
    pdf_file.seek(0)
    return ContentFile(pdf_file.getvalue())  # in memory pdf
