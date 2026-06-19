"""Tests for PaymentCertificate exporters and layout downloads."""

from decimal import Decimal

import pytest
from django.urls import reverse

from app.Account.tests.factories import AccountFactory
from app.BillOfQuantities.tasks import (
    compile_pdf_for_certificate,
    get_report_filename,
    get_valuation_summary_data,
)
from app.BillOfQuantities.tests.factories import (
    ActualTransactionFactory,
    BillFactory,
    LineItemFactory,
    PackageFactory,
    PaymentCertificateFactory,
    StructureFactory,
)
from app.Project.tests.factories import ProjectFactory, SignatoriesFactory


@pytest.mark.django_db
class TestExporters:
    """Test cases for PaymentCertificate Excel exporter and PDF compiler."""

    def test_get_valuation_summary_data(self):
        """Test aggregation of valuation summary data."""
        project = ProjectFactory.create()
        cert = PaymentCertificateFactory.create(project=project)

        # Create a structure, bill and package belonging to project
        structure = StructureFactory.create(project=project)
        bill = BillFactory.create(structure=structure)
        package = PackageFactory.create(bill=bill)

        line_item = LineItemFactory.create(
            project=project,
            structure=structure,
            bill=bill,
            package=package,
            is_work=True,
            unit_price=Decimal("100.00"),
            budgeted_quantity=Decimal("5.00"),
            total_price=Decimal("500.00"),
        )

        # Add actual transaction to certify some work
        ActualTransactionFactory.create(
            payment_certificate=cert,
            line_item=line_item,
            quantity=Decimal("2.00"),
            total_price=Decimal("200.00"),
            claimed=True,
            approved=True,
        )

        data = get_valuation_summary_data(cert)

        assert len(data["grouped_sections"]) > 0
        assert data["total_budget"] == Decimal("500.00")
        assert data["total_cumulative"] == Decimal("200.00")

        # Since it's the first certificate, previous should be 0, current should be 200
        assert data["total_previous"] == Decimal("0.00")
        assert data["total_current"] == Decimal("200.00")

    def test_compile_pdf_for_certificate(self):
        """Test PDF compiler."""
        project = ProjectFactory.create()
        cert = PaymentCertificateFactory.create(project=project)
        LineItemFactory.create(project=project)

        pdf_file = compile_pdf_for_certificate(cert)
        assert pdf_file is not None
        assert pdf_file.size > 0

    def test_compile_pdf_custom_sections(self):
        """Test PDF compiler with custom section inclusions."""
        project = ProjectFactory.create()
        cert = PaymentCertificateFactory.create(project=project)
        LineItemFactory.create(project=project)

        # Download only front and detailed (no summary)
        pdf_file = compile_pdf_for_certificate(
            cert, include_front=True, include_summary=False, include_detailed=True
        )
        assert pdf_file is not None
        assert pdf_file.size > 0

    def test_compile_pdf_abridged(self):
        """Test compiling abridged PDF."""
        project = ProjectFactory.create()
        cert = PaymentCertificateFactory.create(project=project)
        # Create standard line items
        LineItemFactory.create(project=project, addendum=False, special_item=False)
        # Create special items
        LineItemFactory.create(project=project, addendum=False, special_item=True)
        # Create addendum items
        LineItemFactory.create(project=project, addendum=True)

        pdf_file = compile_pdf_for_certificate(
            cert,
            include_front=True,
            include_summary=True,
            include_detailed=True,
            is_abridged=True,
        )
        assert pdf_file is not None
        assert pdf_file.size > 0

    def test_compile_pdf_logo_fallbacks_standard_layout(self):
        """Test that standard layout PDF compiles successfully with logo fallbacks (project -> contractor -> client)."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from app.Project.models import Company

        # 1. Project logo
        project1 = ProjectFactory.create()
        project1.logo = SimpleUploadedFile(
            "logo.png",
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )
        project1.save()
        cert1 = PaymentCertificateFactory.create(project=project1)
        pdf_file1 = compile_pdf_for_certificate(cert1)
        assert pdf_file1 is not None

        # 2. Contractor logo
        project2 = ProjectFactory.create(logo=None)
        contractor = Company.objects.create(
            type=Company.Type.CONTRACTOR, name="Contractor Inc"
        )
        contractor.logo = SimpleUploadedFile(
            "contractor_logo.png",
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )
        contractor.save()
        project2.contractor = contractor
        project2.save()
        cert2 = PaymentCertificateFactory.create(project=project2)
        pdf_file2 = compile_pdf_for_certificate(cert2)
        assert pdf_file2 is not None

        # 3. Client logo
        project3 = ProjectFactory.create(logo=None)
        client = Company.objects.create(type=Company.Type.CLIENT, name="Client Ltd")
        client.logo = SimpleUploadedFile(
            "client_logo.png",
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )
        client.save()
        project3.client = client
        project3.save()
        cert3 = PaymentCertificateFactory.create(project=project3)
        pdf_file3 = compile_pdf_for_certificate(cert3)
        assert pdf_file3 is not None

    def test_compile_pdf_with_custom_columns(self):
        """Test PDF compiler with custom column configuration."""
        from django.template.loader import render_to_string

        project = ProjectFactory.create()
        cert = PaymentCertificateFactory.create(project=project)

        # Configure custom columns: only keep description and amount due, reordered
        column_config = {
            "columns": [
                {"id": "description", "label": "DESC_CUSTOM", "enabled": True},
                {"id": "current_claim", "label": "DUE_CUSTOM", "enabled": True},
                {"id": "unit_price", "label": "Rate", "enabled": False},
                {"id": "total_price", "label": "TOTAL_CUSTOM", "enabled": False},
            ]
        }
        project.column_config = column_config
        project.save()

        # Get active columns
        columns = [
            col for col in project.get_column_config() if col.get("enabled", True)
        ]

        # Render standard line items table with columns in context
        context = {
            "payment_certificate": cert,
            "project": project,
            "line_items": [],
            "columns": columns,
        }
        html = render_to_string("pdf_templates/line_items_table.html", context)

        assert "DESC_CUSTOM" in html
        assert "DUE_CUSTOM" in html
        assert "Rate" not in html
        assert "TOTAL_CUSTOM" not in html

        # Also compile PDF and assert it executes without errors
        pdf_file = compile_pdf_for_certificate(cert)
        assert pdf_file is not None
        assert pdf_file.size > 0

    def test_compile_pdf_with_signatories(self):
        """Test compiling PDF when the project has allocated signatories."""
        project = ProjectFactory.create()
        cert = PaymentCertificateFactory.create(project=project)
        LineItemFactory.create(project=project)

        # Create allocated signatories for the project
        SignatoriesFactory.create(project=project, role="Project Manager")
        SignatoriesFactory.create(project=project, role="Quantity Surveyor")

        pdf_file = compile_pdf_for_certificate(cert)
        assert pdf_file is not None
        assert pdf_file.size > 0

    def test_compile_pdf_without_signatories(self):
        """Test compiling PDF when the project has no allocated signatories."""
        project = ProjectFactory.create()
        cert = PaymentCertificateFactory.create(project=project)
        LineItemFactory.create(project=project)

        # Ensure no signatories are allocated
        assert project.signatories.count() == 0

        pdf_file = compile_pdf_for_certificate(cert)
        assert pdf_file is not None
        assert pdf_file.size > 0

    def test_report_naming_format(self):
        """Test that get_report_filename constructs correct filenames."""
        from datetime import datetime

        from app.Project.tests.factories import ProjectFactory

        project = ProjectFactory.create(name="Test Project")
        cert = PaymentCertificateFactory.create(project=project)

        date_val = cert.assessment_date or cert.approved_on or datetime.now()
        if hasattr(date_val, "date"):
            date_val = date_val.date()
        expected_date = date_val.strftime("%Y-%m-%d")

        # Case 1: Full report
        filename = get_report_filename(
            cert,
            include_front=True,
            include_summary=True,
            include_detailed=True,
            is_abridged=False,
        )
        assert filename == f"cover-summary-detailed_full_{expected_date}.pdf"

        # Case 2: Abridged report
        filename = get_report_filename(
            cert,
            include_front=True,
            include_summary=True,
            include_detailed=True,
            is_abridged=True,
        )
        assert filename == f"cover-summary-detailed_abridged_{expected_date}.pdf"

        # Case 3: Combined/custom sections
        filename = get_report_filename(
            cert,
            include_front=True,
            include_summary=False,
            include_detailed=True,
            is_abridged=False,
        )
        assert filename == f"cover-detailed_combined_{expected_date}.pdf"

        # Case 4: Single section
        filename = get_report_filename(
            cert,
            include_front=False,
            include_summary=True,
            include_detailed=False,
            is_abridged=False,
        )
        assert filename == f"summary_combined_{expected_date}.pdf"

    def test_special_items_exporters(self):
        """Test exporters (PDF, Excel) with standard, addendum, and special items."""
        from app.BillOfQuantities.exporters.cover_page_exporter import (
            export_cover_page_to_xlsx,
        )
        from app.BillOfQuantities.exporters.detailed_report_exporter import (
            export_detailed_report_to_xlsx,
        )
        from app.BillOfQuantities.tests.factories import ActualTransactionFactory

        project = ProjectFactory.create(vat=True)
        cert = PaymentCertificateFactory.create(project=project, certificate_number=2)

        # Previous certificate to test previous calculations
        prev_cert = PaymentCertificateFactory.create(
            project=project, certificate_number=1, status="APPROVED"
        )

        structure = StructureFactory.create(project=project)
        bill = BillFactory.create(structure=structure)
        package = PackageFactory.create(bill=bill)

        # 1. Standard Line Item
        std_item = LineItemFactory.create(
            project=project,
            structure=structure,
            bill=bill,
            package=package,
            is_work=True,
            unit_price=Decimal("100.00"),
            budgeted_quantity=Decimal("10.00"),
            total_price=Decimal("1000.00"),
            special_item=False,
            addendum=False,
        )

        # 2. Addendum Line Item
        add_item = LineItemFactory.create(
            project=project,
            structure=structure,
            bill=bill,
            package=package,
            is_work=True,
            unit_price=Decimal("150.00"),
            budgeted_quantity=Decimal("5.00"),
            total_price=Decimal("750.00"),
            special_item=False,
            addendum=True,
        )

        # 3. Special Line Item
        spec_item = LineItemFactory.create(
            project=project,
            structure=None,
            bill=None,
            package=None,
            is_work=True,
            unit_price=Decimal("200.00"),
            budgeted_quantity=Decimal("1.00"),
            total_price=Decimal("200.00"),
            special_item=True,
            addendum=False,
            description="Contractual Special Item A",
        )

        # Transactions for prev_cert
        ActualTransactionFactory.create(
            payment_certificate=prev_cert,
            line_item=std_item,
            quantity=Decimal("3.00"),
            total_price=Decimal("300.00"),
            claimed=True,
            approved=True,
        )
        ActualTransactionFactory.create(
            payment_certificate=prev_cert,
            line_item=spec_item,
            quantity=Decimal("0.50"),
            total_price=Decimal("100.00"),
            claimed=True,
            approved=True,
        )

        # Transactions for current cert
        ActualTransactionFactory.create(
            payment_certificate=cert,
            line_item=std_item,
            quantity=Decimal("2.00"),
            total_price=Decimal("200.00"),
            claimed=True,
            approved=True,
        )
        ActualTransactionFactory.create(
            payment_certificate=cert,
            line_item=add_item,
            quantity=Decimal("1.00"),
            total_price=Decimal("150.00"),
            claimed=True,
            approved=True,
        )
        ActualTransactionFactory.create(
            payment_certificate=cert,
            line_item=spec_item,
            quantity=Decimal("0.25"),
            total_price=Decimal("50.00"),
            claimed=True,
            approved=True,
        )

        # Test model property aggregations
        assert cert.special_items_budget_total == Decimal("200.00")
        assert cert.special_items_progressive_previous == Decimal("100.00")
        assert cert.special_items_current_claim_total == Decimal("50.00")
        assert cert.special_items_progressive_to_date == Decimal("150.00")

        # Compile PDF report
        pdf_file = compile_pdf_for_certificate(
            cert,
            include_front=True,
            include_summary=True,
            include_detailed=True,
            is_abridged=False,
        )
        assert pdf_file is not None
        assert pdf_file.size > 0

        # Export detailed report to Excel
        wb_detail = export_detailed_report_to_xlsx(cert, is_abridged=False)
        assert "Special Items" in wb_detail.sheetnames
        ws_special = wb_detail["Special Items"]

        # Verify unified table rows and columns on Special Items sheet
        assert ws_special.cell(row=5, column=1).value == "ADDENDUM LINE ITEMS"
        assert ws_special.cell(row=6, column=1).value == add_item.description
        assert ws_special.cell(row=6, column=3).value == Decimal(
            "150.00"
        )  # Current claim
        assert ws_special.cell(row=8, column=1).value == "SPECIAL LINE ITEMS"
        assert ws_special.cell(row=9, column=1).value == "Contractual Special Item A"
        assert ws_special.cell(row=9, column=2).value == Decimal("100.00")  # Previous
        assert ws_special.cell(row=9, column=3).value == Decimal("50.00")  # Current
        assert ws_special.cell(row=9, column=4).value == Decimal("150.00")  # Total

        # Export summary report to Excel
        from app.BillOfQuantities.exporters.summary_report_exporter import (
            export_summary_report_to_xlsx,
        )

        wb_summary = export_summary_report_to_xlsx(cert, is_abridged=False)
        assert "Summary - Full" in wb_summary.sheetnames
        ws_sum = wb_summary["Summary - Full"]

        grand_total_row = None
        for r in range(5, ws_sum.max_row + 1):
            if ws_sum.cell(row=r, column=2).value == "GRAND TOTAL":
                grand_total_row = r
                break
        assert grand_total_row is not None
        # Grand total current claim should be contract (200) + addendum (150) + special (50) = 400.00
        assert ws_sum.cell(row=grand_total_row, column=6).value == Decimal("400.00")

        # Export cover page to Excel
        wb_cover = export_cover_page_to_xlsx(cert)
        assert "Cover Page" in wb_cover.sheetnames


@pytest.mark.django_db
class TestDownloadViews:
    """Test cases for download views including custom choices and Excel downloads."""

    def test_download_pdf_view_custom_sections(self, client):
        """Test that PDF download view with custom sections returns valid PDF response."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        cert = PaymentCertificateFactory.create(project=project)
        LineItemFactory.create(project=project)

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-download-pdf",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )

        # Test custom request with selected options
        response = client.get(url, {"front": "on", "summary": "on", "detailed": "on"})
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert "Content-Disposition" in response
        assert "cover-summary-detailed_full_" in response["Content-Disposition"]

    def test_download_abridged_pdf_view_custom_sections(self, client):
        """Test that abridged PDF download view with custom sections returns valid PDF response."""
        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        cert = PaymentCertificateFactory.create(project=project)
        LineItemFactory.create(project=project)

        client.force_login(user)
        url = reverse(
            "bill_of_quantities:payment-certificate-download-abridged-pdf",
            kwargs={"project_pk": project.pk, "pk": cert.pk},
        )

        # Test custom request with selected options
        response = client.get(url, {"front": "on", "summary": "on", "detailed": "on"})
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert "Content-Disposition" in response
        assert "cover-summary-detailed_abridged_" in response["Content-Disposition"]
