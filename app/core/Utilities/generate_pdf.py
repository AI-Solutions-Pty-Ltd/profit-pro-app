from io import BytesIO

from django.core.files.base import ContentFile
from xhtml2pdf import pisa


def generate_pdf(html_content) -> ContentFile:
    pdf_file = BytesIO()
    pisa.CreatePDF(html_content, dest=pdf_file)
    pdf_file.seek(0)
    return ContentFile(pdf_file.getvalue())  # in memory pdf
