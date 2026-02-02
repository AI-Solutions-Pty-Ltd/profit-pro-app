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
    # Handle relative URLs
    if src_attr.startswith("/media/"):
        # Convert to full filesystem path
        src_attr = src_attr[1:]  # Remove leading slash
        full_path = os.path.join(settings.MEDIA_ROOT, src_attr.replace("media/", ""))

        # Check if file exists
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                img_data = f.read()
            return f"data:image/jpeg;base64,{b64encode(img_data).decode()}"

    # Handle data URLs (already base64 encoded)
    elif src_attr.startswith("data:image"):
        return src_attr

    # Handle static files or other cases
    elif src_attr.startswith("/static/"):
        # For static files, you might want to implement similar logic
        # For now, return empty to avoid errors
        return ""

    # Default: return empty string to avoid errors
    return ""


def generate_pdf(html_content) -> ContentFile:
    pdf_file = BytesIO()
    pisa.CreatePDF(html_content, dest=pdf_file, link_callback=link_callback)
    pdf_file.seek(0)
    return ContentFile(pdf_file.getvalue())  # in memory pdf
