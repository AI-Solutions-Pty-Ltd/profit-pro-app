# ruff: noqa: E402
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.local")
django.setup()

from app.BillOfQuantities.tasks import compile_pdf_for_certificate
from app.BillOfQuantities.tests.factories import (
    LineItemFactory,
    PaymentCertificateFactory,
)
from app.Project.tests.factories import ProjectFactory


def run():
    print("Creating test project and certificate...")
    project = ProjectFactory.create()
    cert = PaymentCertificateFactory.create(project=project)

    # Create standard line items
    LineItemFactory.create(project=project, addendum=False, special_item=False)
    # Create special items
    LineItemFactory.create(project=project, addendum=False, special_item=True)
    # Create addendum items
    LineItemFactory.create(project=project, addendum=True)

    print("Compiling abridged PDF...")
    try:
        pdf = compile_pdf_for_certificate(
            cert,
            include_front=True,
            include_summary=True,
            include_detailed=True,
            is_abridged=True,
        )
        print("Success! PDF size:", len(pdf.read()))
    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    run()
