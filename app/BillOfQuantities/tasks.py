from collections import defaultdict

from django.core.files.base import ContentFile
from django.template.loader import get_template

from app.BillOfQuantities.models import LineItem
from app.core.Utilities.generate_pdf import generate_pdf


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
    # Use nested defaultdicts for efficient grouping
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
