import threading
from collections import defaultdict
from typing import Literal

from django.core.files.base import ContentFile
from django.template.loader import get_template, render_to_string

from app.BillOfQuantities.models import LineItem, PaymentCertificate
from app.core.Utilities.django_email_service import django_email_service
from app.core.Utilities.generate_pdf import generate_pdf
from app.Project.models import Project


def group_line_items_by_hierarchy(line_items):
    """
    Group line items by structure -> bill -> package hierarchy.

    This is much more efficient than doing comparisons in the template.

    Returns:
        list: Grouped structure with format:
        [
            {
                'structure': structure_obj,
                'bills': [
                    {
                        'bill': bill_obj,
                        'packages': [
                            {
                                'package': package_obj,
                                'line_items': [line_item1, line_item2, ...]
                            }
                        ]
                    }
                ]
            }
        ]
    """
    # Use nested default dicts for efficient grouping
    hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for line_item in line_items:
        structure = line_item.structure
        bill = line_item.bill
        package = line_item.package
        hierarchy[structure][bill][package].append(line_item)

    # Convert to list format for template iteration
    grouped = []
    for structure, bills in hierarchy.items():
        structure_data = {"structure": structure, "bills": []}
        for bill, packages in bills.items():
            bill_data = {"bill": bill, "packages": []}
            for package, items in packages.items():
                package_data = {"package": package, "line_items": items}
                bill_data["packages"].append(package_data)
            structure_data["bills"].append(bill_data)
        grouped.append(structure_data)

    return grouped


def generate_payment_certificate_pdf(payment_certificate) -> ContentFile:
    """Generate payment certificate PDF in memory.

    Args:
        payment_certificate: PaymentCertificate instance to generate PDF for

    Returns:
        ContentFile: In-memory PDF file
    """
    template = get_template("pdf_templates/payment_certificate.html")
    project = payment_certificate.project
    line_items = LineItem.construct_payment_certificate(payment_certificate)

    context = {
        "payment_certificate": payment_certificate,
        "project": project,
        "grouped_line_items": group_line_items_by_hierarchy(line_items),
        "is_abridged": False,
    }
    html = template.render(context)
    pdf_content = generate_pdf(html)

    return pdf_content


def generate_abridged_payment_certificate_pdf(payment_certificate) -> ContentFile:
    """Generate abridged payment certificate PDF in memory."""
    template = get_template("pdf_templates/payment_certificate.html")
    project = payment_certificate.project
    line_items = LineItem.abridged_payment_certificate(payment_certificate)

    context = {
        "payment_certificate": payment_certificate,
        "project": project,
        "grouped_line_items": group_line_items_by_hierarchy(line_items),
        "is_abridged": True,
    }
    html = template.render(context)
    pdf_content = generate_pdf(html)

    return pdf_content


def generate_and_save_pdf(
    payment_certificate_id: int, pdf_type: Literal["full", "abridged"] = "full"
):
    """
    Internal function to generate and save PDF in a separate thread.

    Args:
        payment_certificate_id: ID of the PaymentCertificate
        pdf_type: Either 'full' or 'abridged'
    """
    import logging

    from app.BillOfQuantities.models import PaymentCertificate

    logger = logging.getLogger(__name__)

    try:
        # Re-fetch the payment certificate in this thread
        payment_certificate = PaymentCertificate.objects.get(id=payment_certificate_id)

        logger.info(
            f"Starting {pdf_type} PDF generation for certificate {payment_certificate.certificate_number}"
        )

        update_fields = []

        if pdf_type == "full":
            # Generate full PDF
            pdf = generate_payment_certificate_pdf(payment_certificate)
            pdf.name = (
                f"payment_certificate_{payment_certificate.certificate_number}.pdf"
            )
            pdf.type = "application/pdf"  # type: ignore
            payment_certificate.pdf = pdf
            payment_certificate.pdf_generating = False
            update_fields.append("pdf")
            update_fields.append("pdf_generating")
            logger.info(
                f"Full PDF generated successfully for certificate {payment_certificate.certificate_number}"
            )
        else:
            # Generate abridged PDF
            pdf = generate_abridged_payment_certificate_pdf(payment_certificate)
            pdf.name = f"payment_certificate_{payment_certificate.certificate_number}_abridged.pdf"
            pdf.type = "application/pdf"  # type: ignore
            payment_certificate.abridged_pdf = pdf
            payment_certificate.abridged_pdf_generating = False
            update_fields.append("abridged_pdf")
            update_fields.append("abridged_pdf_generating")
            logger.info(
                f"Abridged PDF generated successfully for certificate {payment_certificate.certificate_number}"
            )

        payment_certificate.save(update_fields=update_fields)

    except Exception as e:
        # On error, reset the generating flag
        logger.error(f"Error generating {pdf_type} PDF: {e}", exc_info=True)
        try:
            payment_certificate = PaymentCertificate.objects.get(
                id=payment_certificate_id
            )
            if pdf_type == "full":
                payment_certificate.pdf_generating = False
            else:
                payment_certificate.abridged_pdf_generating = False
            payment_certificate.save()
            logger.info(f"Reset {pdf_type} generating flag after error")
        except Exception as save_error:
            logger.error(f"Failed to reset generating flag: {save_error}")


def generate_pdf_async(
    payment_certificate_id: int,
    pdf_type: Literal["full", "abridged", "both"] | None = None,
) -> None:
    """
    Start PDF generation in a background thread.

    Args:
        payment_certificate_id: ID of the PaymentCertificate
        pdf_type: Which PDF to generate - 'full', 'abridged', 'both', or None (auto-detect)
    """
    import logging

    from app.BillOfQuantities.models import PaymentCertificate

    logger = logging.getLogger(__name__)

    # Mark as generating
    payment_certificate = PaymentCertificate.objects.get(id=payment_certificate_id)
    generate_pdf = False
    generate_abridged_pdf = False

    if pdf_type == "both":
        # Force regeneration of both PDFs
        generate_pdf = True
        generate_abridged_pdf = True
    elif pdf_type == "full":
        # Only generate full PDF
        generate_pdf = True
    elif pdf_type == "abridged":
        # Only generate abridged PDF
        generate_abridged_pdf = True
    else:
        # Auto-detect: Only generate if missing and not already generating
        if not payment_certificate.pdf and not payment_certificate.pdf_generating:
            generate_pdf = True
        if (
            not payment_certificate.abridged_pdf
            and not payment_certificate.abridged_pdf_generating
        ):
            generate_abridged_pdf = True

    # Set flags before starting threads
    if generate_pdf:
        payment_certificate.pdf_generating = True
    if generate_abridged_pdf:
        payment_certificate.abridged_pdf_generating = True

    payment_certificate.save()

    if generate_pdf:
        logger.info(
            f"Starting full PDF generation thread for certificate {payment_certificate.certificate_number}"
        )
        # Start generation in background thread
        thread = threading.Thread(
            target=generate_and_save_pdf,
            args=(payment_certificate_id, "full"),
            daemon=True,
        )
        thread.start()
    if generate_abridged_pdf:
        logger.info(
            f"Starting abridged PDF generation thread for certificate {payment_certificate.certificate_number}"
        )
        # Start generation in background thread
        thread = threading.Thread(
            target=generate_and_save_pdf,
            args=(payment_certificate_id, "abridged"),
            daemon=True,
        )
        thread.start()


def send_payment_certificate_to_signatories(payment_certificate_id: int):
    # Get all signatories
    payment_certificate = PaymentCertificate.objects.get(id=payment_certificate_id)
    project: Project = payment_certificate.project
    signatories = project.signatories.all()
    if not signatories.exists():
        raise Exception("No signatories found for this project.")

    # Send email to each signatory
    to_emails = []
    for signatory in signatories:
        to_emails.append(signatory.email)

    # Render email template
    context = {
        "payment_certificate": payment_certificate,
    }
    html_message = render_to_string(
        "payment_certificate/email_payment_certificate.html", context
    )

    # Create email with attachment
    subject = (
        f"{payment_certificate.project.name} - "
        f"Payment Certificate #{payment_certificate.certificate_number} for signatories"
    )

    files = [
        payment_certificate.pdf,
        payment_certificate.abridged_pdf,
    ]

    return django_email_service(
        to=to_emails,
        subject=subject,
        html_body=html_message,
        attachments=files,
    )
