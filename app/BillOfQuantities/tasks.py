from django.core.files.base import ContentFile
from django.template.loader import get_template

from app.core.Utilities.generate_pdf import generate_pdf
from app.BillOfQuantities.models import LineItem


def generate_payment_certificate_pdf(payment_certificate) -> ContentFile:
    """Generate payment certificate PDF in memory.

    Args:
        payment_certificate: PaymentCertificate instance to generate PDF for

    Returns:
        ContentFile: In-memory PDF file
    """
    template = get_template("pdf_templates/payment_certificate.html")
    context = {
        "payment_certificate": payment_certificate,
        "line_items": LineItem.construct_payment_certificate(payment_certificate),
    }
    html = template.render(context)
    pdf_content = generate_pdf(html)

    return pdf_content
