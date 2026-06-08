import threading
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Literal

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import get_template, render_to_string
from pypdf import PdfReader, PdfWriter

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


def get_valuation_summary_data(payment_certificate):
    """
    Get aggregated data for the Valuation Summary page (Valterra/RPM layout).
    Groups line items by structure (section) -> bill and calculates totals.
    """
    line_items = LineItem.construct_payment_certificate(payment_certificate)

    structures_data = {}
    for item in line_items:
        if not item.is_work:
            continue
        struct_id = item.structure_id
        bill_id = item.bill_id
        if not struct_id or not bill_id:
            continue

        if struct_id not in structures_data:
            structures_data[struct_id] = {
                "name": item.structure.name,
                "budget": Decimal("0.00"),
                "cumulative": Decimal("0.00"),
                "previous": Decimal("0.00"),
                "current": Decimal("0.00"),
                "bills": {},
            }

        struct = structures_data[struct_id]
        if bill_id not in struct["bills"]:
            struct["bills"][bill_id] = {
                "name": item.bill.name,
                "budget": Decimal("0.00"),
                "cumulative": Decimal("0.00"),
                "previous": Decimal("0.00"),
                "current": Decimal("0.00"),
            }

        bill = struct["bills"][bill_id]

        budget_val = Decimal(str(item.total_price or "0.00"))
        cum_val = Decimal(str(item.total_claimed or "0.00"))
        prev_val = Decimal(str(item.previous_claimed or "0.00"))
        curr_val = Decimal(str(item.current_claim or "0.00"))

        bill["budget"] += budget_val
        bill["cumulative"] += cum_val
        bill["previous"] += prev_val
        bill["current"] += curr_val

        struct["budget"] += budget_val
        struct["cumulative"] += cum_val
        struct["previous"] += prev_val
        struct["current"] += curr_val

    # Convert to list structure sorted by name
    grouped_sections = []
    sorted_structs = sorted(structures_data.values(), key=lambda s: s["name"])

    total_budget = Decimal("0.00")
    total_cumulative = Decimal("0.00")
    total_previous = Decimal("0.00")
    total_current = Decimal("0.00")

    for s_data in sorted_structs:
        sorted_bills = sorted(s_data["bills"].values(), key=lambda b: b["name"])
        s_data["bills"] = sorted_bills
        grouped_sections.append(s_data)

        total_budget += s_data["budget"]
        total_cumulative += s_data["cumulative"]
        total_previous += s_data["previous"]
        total_current += s_data["current"]

    return {
        "grouped_sections": grouped_sections,
        "total_budget": total_budget,
        "total_cumulative": total_cumulative,
        "total_previous": total_previous,
        "total_current": total_current,
    }


def compile_pdf_for_certificate(
    payment_certificate,
    include_front: bool = True,
    include_summary: bool = True,
    include_detailed: bool = True,
    is_abridged: bool = False,
    layout: str | None = None,
) -> ContentFile:
    """
    Compile a payment certificate PDF with optional layout and sections.
    """
    project = payment_certificate.project
    if not layout:
        layout = getattr(project, "certificate_layout", "standard") or "standard"
    layout = layout.lower()

    # Context initialization
    all_columns = project.get_column_config()
    active_columns = [col for col in all_columns if col.get("enabled", True)]

    context = {
        "payment_certificate": payment_certificate,
        "project": project,
        "now": datetime.now(),
        "vat_rate": settings.VAT_RATE,
        "is_abridged": is_abridged,
        "columns": active_columns,
    }

    # Gather data based on abridged flag
    if is_abridged:
        all_line_items = LineItem.abridged_payment_certificate(payment_certificate)
        line_items = all_line_items.filter(addendum=False, special_item=False)
        special_items = all_line_items.filter(addendum=False, special_item=True)
        addendum_items = all_line_items.filter(addendum=True)
        context.update(
            {
                "grouped_line_items": group_line_items_by_hierarchy(line_items),
                "addendum_items": group_line_items_by_hierarchy(addendum_items),
                "special_items": special_items,
            }
        )
    else:
        line_items = LineItem.construct_payment_certificate(payment_certificate)
        context.update(
            {
                "grouped_line_items": group_line_items_by_hierarchy(line_items),
            }
        )

    # Add summary data if summary is requested and layout is valterra_rpm
    if include_summary and layout == "valterra_rpm":
        summary_data = get_valuation_summary_data(payment_certificate)
        context.update(summary_data)

    # Compile the individual PDFs
    merger = PdfWriter()
    pdf_parts = []

    if layout == "valterra_rpm":
        if include_front:
            front_tpl = get_template("pdf_templates/valterra_rpm/1-front-page.html")
            pdf_parts.append(generate_pdf(front_tpl.render(context)))
        if include_summary:
            sum_tpl = get_template("pdf_templates/valterra_rpm/2-summary.html")
            pdf_parts.append(generate_pdf(sum_tpl.render(context)))
        if include_detailed:
            det_tpl = get_template("pdf_templates/valterra_rpm/3-detailed.html")
            pdf_parts.append(generate_pdf(det_tpl.render(context)))
    else:
        # Standard Layout
        if include_front:
            front_tpl = get_template("pdf_templates/1-front-page.html")
            pdf_parts.append(generate_pdf(front_tpl.render(context)))
        # Standard layout has no separate summary page, but if detailed is checked we render 2-line-items
        if include_detailed:
            det_tpl = get_template("pdf_templates/2-line-items.html")
            pdf_parts.append(generate_pdf(det_tpl.render(context)))

    # Merge PDFs using pypdf
    for pdf_content in pdf_parts:
        pdf_reader = PdfReader(BytesIO(pdf_content.read()))
        for page in pdf_reader.pages:
            merger.add_page(page)

    # Write merged PDF to BytesIO
    merged_output = BytesIO()
    merger.write(merged_output)
    merged_output.seek(0)

    return ContentFile(merged_output.getvalue())


def generate_payment_certificate_pdf(context) -> ContentFile:
    """Generate payment certificate PDF in memory (for backwards compatibility)."""
    payment_certificate = context.get("payment_certificate")
    if payment_certificate:
        layout = getattr(payment_certificate.project, "certificate_layout", "standard")
        is_abridged = context.get("is_abridged", False)
        return compile_pdf_for_certificate(
            payment_certificate,
            include_front=True,
            include_summary=True,
            include_detailed=True,
            is_abridged=is_abridged,
            layout=layout,
        )

    # Fallback to standard logic if no payment_certificate is in context
    context["now"] = datetime.now()
    context["vat_rate"] = settings.VAT_RATE
    front_page_template = get_template("pdf_templates/1-front-page.html")
    line_items_template = get_template("pdf_templates/2-line-items.html")

    front_page_pdf = generate_pdf(front_page_template.render(context))
    line_items_pdf = generate_pdf(line_items_template.render(context))

    merger = PdfWriter()
    for pdf_content in [front_page_pdf, line_items_pdf]:
        pdf_reader = PdfReader(BytesIO(pdf_content.read()))
        for page in pdf_reader.pages:
            merger.add_page(page)

    merged_output = BytesIO()
    merger.write(merged_output)
    merged_output.seek(0)
    return ContentFile(merged_output.getvalue())


def generate_full_payment_certificate_pdf(payment_certificate) -> ContentFile:
    return compile_pdf_for_certificate(
        payment_certificate,
        include_front=True,
        include_summary=True,
        include_detailed=True,
        is_abridged=False,
    )


def generate_abridged_payment_certificate_pdf(payment_certificate) -> ContentFile:
    """Generate abridged payment certificate PDF in memory."""
    return compile_pdf_for_certificate(
        payment_certificate,
        include_front=True,
        include_summary=True,
        include_detailed=True,
        is_abridged=True,
    )


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
            pdf = generate_full_payment_certificate_pdf(payment_certificate)
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
                f"Full PDF generated successfully for certificate {payment_certificate.certificate_number}. Progressive to date: {payment_certificate.progressive_to_date}"
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
        if signatory.user:
            to_emails.append(signatory.user.email)

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
