import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.local")
django.setup()

from app.BillOfQuantities.exporters.cover_page_exporter import export_cover_page_to_xlsx
from app.BillOfQuantities.tests.factories import PaymentCertificateFactory
from app.Project.tests.factories import ProjectFactory


def run_test():
    project = ProjectFactory.create()
    cert = PaymentCertificateFactory.create(project=project)
    wb = export_cover_page_to_xlsx(cert)
    ws = wb.active

    # Check that CONTRACT VALUE SUMMARY (row 11) has border
    cell = ws.cell(row=11, column=1)
    assert cell.border.top.style is not None, "Border top style is missing"
    assert cell.border.left.style is not None, "Border left style is missing"

    # Check value row (row 13)
    val_cell = ws.cell(row=13, column=6)
    assert val_cell.border.right.style is not None, "Border right style is missing"
    print("Test Passed: Formatting applied correctly!")


if __name__ == "__main__":
    run_test()
