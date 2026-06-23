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

    def test_cover_page_custom_config(self):
        """Test that cover page config custom titles, headers, and disabled fields are respected in Excel and PDF/HTML context."""
        from app.BillOfQuantities.exporters.cover_page_exporter import (
            export_cover_page_to_xlsx,
        )

        project = ProjectFactory.create(name="Alpha Project")

        # 1. Verify standard fallbacks (default config)
        cert_default = PaymentCertificateFactory.create(
            project=project, certificate_number=1
        )

        # Render default Excel
        wb_default = export_cover_page_to_xlsx(cert_default)
        ws_default = wb_default["Cover Page"]

        # Verify default title is in the merged cell
        assert ws_default.cell(row=1, column=3).value == "PAYMENT CERTIFICATE"

        # Find default labels
        found_contract_name = False
        found_description = False
        found_original_value = False
        found_sub_total = False

        for r in range(5, ws_default.max_row + 1):
            val_col1 = ws_default.cell(row=r, column=1).value
            if val_col1 == "Contract":
                found_contract_name = True
            elif val_col1 == "Description":
                found_description = True
            elif val_col1 == "Original Contract Value":
                found_original_value = True
            elif val_col1 == "Sub Total (Excl. VAT)":
                found_sub_total = True

        assert found_contract_name is True
        assert found_description is True
        assert found_original_value is True
        assert found_sub_total is True

        # Compile PDF with default config and check it runs
        pdf_file_default = compile_pdf_for_certificate(cert_default)
        assert pdf_file_default is not None
        assert pdf_file_default.size > 0

        # 2. Verify customized config
        custom_config = {
            "title": "SUPERPAYMENT REPORT",
            "sections": {
                "section_a": {
                    "title": "SUPER SECTION A",
                    "fields": [
                        {
                            "id": "contract_name",
                            "label": "Super Project Name",
                            "enabled": True,
                        },
                        {
                            "id": "contract_number",
                            "label": "Contract Identifier",
                            "enabled": False,
                        },
                        {
                            "id": "contract_clause",
                            "label": "Clause Info",
                            "enabled": True,
                        },
                        {"id": "description", "label": "Brief Desc", "enabled": False},
                        {"id": "client", "label": "Super Client", "enabled": True},
                        {"id": "status", "label": "Assessment Status", "enabled": True},
                        {"id": "assessment_date", "label": "Val Date", "enabled": True},
                        {
                            "id": "certificate_date",
                            "label": "Cert Date",
                            "enabled": True,
                        },
                    ],
                },
                "section_b": {
                    "title": "SUPER SECTION B",
                    "fields": [
                        {
                            "id": "original_value",
                            "label": "Super Orig Val",
                            "enabled": True,
                        },
                        {
                            "id": "amendments_value",
                            "label": "Super Amends",
                            "enabled": False,
                        },
                        {"id": "sub_total", "label": "Super Subtotal", "enabled": True},
                        {"id": "vat", "label": "Super VAT", "enabled": True},
                        {"id": "total_value", "label": "Super Total", "enabled": True},
                    ],
                },
                "section_c": {
                    "title": "SUPER SECTION C",
                    "fields": [
                        {
                            "id": "work_progressive_previous",
                            "label": "Super Prev Progressive",
                            "enabled": True,
                        },
                        {
                            "id": "contract_current_claim_total",
                            "label": "Super Current Contract",
                            "enabled": False,
                        },
                        {
                            "id": "addendum_current_claim_total",
                            "label": "Super Current Addendum",
                            "enabled": True,
                        },
                        {
                            "id": "work_progressive_to_date",
                            "label": "Super Prog To Date",
                            "enabled": True,
                        },
                        {
                            "id": "special_items",
                            "label": "Super Special Items",
                            "enabled": True,
                        },
                        {
                            "id": "progressive_to_date",
                            "label": "Super Progressive Sum",
                            "enabled": True,
                        },
                        {
                            "id": "progressive_previous",
                            "label": "Super Prev Progressive Sum",
                            "enabled": True,
                        },
                        {
                            "id": "current_claim_total",
                            "label": "Super Current Certified",
                            "enabled": True,
                        },
                        {
                            "id": "vat_now",
                            "label": "Super Current VAT",
                            "enabled": True,
                        },
                        {
                            "id": "total_certified",
                            "label": "Super Grand Total",
                            "enabled": True,
                        },
                    ],
                },
            },
        }

        project.cover_page_config = custom_config
        project.save()

        cert_custom = PaymentCertificateFactory.create(
            project=project, certificate_number=2
        )

        # Render customized Excel
        wb_custom = export_cover_page_to_xlsx(cert_custom)
        ws_custom = wb_custom["Cover Page"]

        # Verify custom title
        assert ws_custom.cell(row=1, column=3).value == "SUPERPAYMENT REPORT"

        # Verify custom Section B Title
        sec_b_title_found = False
        sec_c_title_found = False

        # Find custom labels and check exclusions
        found_custom_contract_name = False
        found_custom_contract_num = False
        found_custom_description = False
        found_custom_original_value = False
        found_custom_amendments = False
        found_custom_prev_work = False
        found_custom_current_contract = False

        for r in range(1, ws_custom.max_row + 1):
            val_col1 = ws_custom.cell(row=r, column=1).value
            if val_col1 == "SUPER SECTION B":
                sec_b_title_found = True
            elif val_col1 == "SUPER SECTION C — CERTIFICATE NO. 02":
                sec_c_title_found = True
            elif val_col1 == "Super Project Name":
                found_custom_contract_name = True
            elif val_col1 == "Contract Identifier":
                found_custom_contract_num = True
            elif val_col1 == "Brief Desc":
                found_custom_description = True
            elif val_col1 == "Super Orig Val":
                found_custom_original_value = True
            elif val_col1 == "Super Amends":
                found_custom_amendments = True
            elif val_col1 == "Super Prev Progressive":
                found_custom_prev_work = True
            elif val_col1 == "Super Current Contract":
                found_custom_current_contract = True

        assert sec_b_title_found is True
        assert sec_c_title_found is True
        assert found_custom_contract_name is True
        assert found_custom_contract_num is False
        assert found_custom_description is False
        assert found_custom_original_value is True
        assert found_custom_amendments is False
        assert found_custom_prev_work is True
        assert found_custom_current_contract is False

        # Compile PDF with custom config and check it runs without issues
        pdf_file_custom = compile_pdf_for_certificate(cert_custom)
        assert pdf_file_custom is not None
        assert pdf_file_custom.size > 0

    def test_cover_page_custom_ordering(self):
        """Test that cover page config custom section ordering and field ordering are respected in Excel and PDF outputs."""
        from app.BillOfQuantities.exporters.cover_page_exporter import (
            export_cover_page_to_xlsx,
        )

        project = ProjectFactory.create(name="Custom Ordered Project")

        # Configure custom ordering: Section C first, then A, then B
        custom_config = {
            "title": "ORDERED REPORT",
            "section_order": ["section_c", "section_a", "section_b"],
            "sections": {
                "section_a": {
                    "title": "ORDERED A",
                    "fields": [
                        # Put assessment_date before contract_name
                        {
                            "id": "assessment_date",
                            "label": "Custom Val Date",
                            "enabled": True,
                        },
                        {
                            "id": "contract_name",
                            "label": "Custom Project Name",
                            "enabled": True,
                        },
                    ],
                },
                "section_b": {
                    "title": "ORDERED B",
                    "fields": [
                        {
                            "id": "sub_total",
                            "label": "Custom Subtotal",
                            "enabled": True,
                        },
                        {
                            "id": "original_value",
                            "label": "Custom Orig Val",
                            "enabled": True,
                        },
                    ],
                },
                "section_c": {
                    "title": "ORDERED C",
                    "fields": [
                        {
                            "id": "current_claim_total",
                            "label": "Custom Net Claim",
                            "enabled": True,
                        },
                        {
                            "id": "total_certified",
                            "label": "Custom Grand Total",
                            "enabled": True,
                        },
                    ],
                },
            },
        }

        project.cover_page_config = custom_config
        project.save()

        cert = PaymentCertificateFactory.create(project=project, certificate_number=3)

        # Export to Excel
        wb = export_cover_page_to_xlsx(cert)
        ws = wb["Cover Page"]

        # Track row indices where the section titles and custom fields appear in the output
        row_indices = {}

        for r in range(1, ws.max_row + 1):
            val_col1 = ws.cell(row=r, column=1).value
            if not val_col1:
                continue
            if "ORDERED B" in val_col1:
                row_indices["section_b_title"] = r
            elif "ORDERED C" in val_col1:
                row_indices["section_c_title"] = r
            elif "Custom Val Date" in val_col1:
                row_indices["assessment_date"] = r
            elif "Custom Project Name" in val_col1:
                row_indices["contract_name"] = r
            elif "Custom Subtotal" in val_col1:
                row_indices["sub_total"] = r
            elif "Custom Orig Val" in val_col1:
                row_indices["original_value"] = r
            elif "Custom Net Claim" in val_col1:
                row_indices["current_claim_total"] = r
            elif "Custom Grand Total" in val_col1:
                row_indices["total_certified"] = r

        # Assert Section order: C first, then A, then B
        assert row_indices["section_c_title"] < row_indices["assessment_date"]
        assert row_indices["contract_name"] < row_indices["section_b_title"]

        # Assert Section A field order: assessment_date before contract_name
        assert row_indices["assessment_date"] < row_indices["contract_name"]

        # Assert Section B field order: sub_total before original_value
        assert row_indices["sub_total"] < row_indices["original_value"]

        # Assert Section C field order: current_claim_total before total_certified
        assert row_indices["current_claim_total"] < row_indices["total_certified"]

        # Compile PDF with custom ordered config and check it runs without issues
        pdf_file = compile_pdf_for_certificate(cert)
        assert pdf_file is not None
        assert pdf_file.size > 0

    def test_bill_natural_sorting(self):
        """Test that get_valuation_summary_data groups and sorts bills naturally by bill_number."""
        project = ProjectFactory.create()
        cert = PaymentCertificateFactory.create(project=project)
        structure = StructureFactory.create(project=project)

        # Create bills with numbers: Bill 10, Bill 2, Bill 1
        bill_10 = BillFactory.create(
            structure=structure, name="Bill B", bill_number="Bill 10"
        )
        bill_2 = BillFactory.create(
            structure=structure, name="Bill A", bill_number="Bill 2"
        )
        bill_1 = BillFactory.create(
            structure=structure, name="Bill C", bill_number="Bill 1"
        )

        pkg_10 = PackageFactory.create(bill=bill_10)
        pkg_2 = PackageFactory.create(bill=bill_2)
        pkg_1 = PackageFactory.create(bill=bill_1)

        for pkg in [pkg_10, pkg_2, pkg_1]:
            LineItemFactory.create(
                project=project,
                structure=structure,
                bill=pkg.bill,
                package=pkg,
                is_work=True,
                total_price=Decimal("100.00"),
            )

        data = get_valuation_summary_data(cert)
        bills = data["grouped_sections"][0]["bills"]

        # Natural sorting order by bill_number: Bill 1, Bill 2, Bill 10
        assert bills[0]["bill_number"] == "Bill 1"
        assert bills[1]["bill_number"] == "Bill 2"
        assert bills[2]["bill_number"] == "Bill 10"

    def test_bill_natural_sorting_by_name(self):
        """Test that get_valuation_summary_data groups and sorts bills naturally by name when bill_number is empty."""
        project = ProjectFactory.create()
        cert = PaymentCertificateFactory.create(project=project)
        structure = StructureFactory.create(project=project)

        # Create bills with no bill_number but names like "Bill No. 10: ...", "Bill No. 2: ...", "Bill No. 1: ..."
        bill_10 = BillFactory.create(
            structure=structure,
            name="Bill No. 10: Structural Steelwork",
            bill_number="",
        )
        bill_2 = BillFactory.create(
            structure=structure,
            name="Bill No. 2: Concrete (Structural)",
            bill_number="",
        )
        bill_1 = BillFactory.create(
            structure=structure, name="Bill No. 1: Earthworks", bill_number=""
        )

        pkg_10 = PackageFactory.create(bill=bill_10)
        pkg_2 = PackageFactory.create(bill=bill_2)
        pkg_1 = PackageFactory.create(bill=bill_1)

        for pkg in [pkg_10, pkg_2, pkg_1]:
            LineItemFactory.create(
                project=project,
                structure=structure,
                bill=pkg.bill,
                package=pkg,
                is_work=True,
                total_price=Decimal("100.00"),
            )

        data = get_valuation_summary_data(cert)
        bills = data["grouped_sections"][0]["bills"]

        # Natural sorting order by name: Bill No. 1, Bill No. 2, Bill No. 10
        assert bills[0]["name"] == "Bill No. 1: Earthworks"
        assert bills[1]["name"] == "Bill No. 2: Concrete (Structural)"
        assert bills[2]["name"] == "Bill No. 10: Structural Steelwork"

    def test_structure_natural_sorting_by_name(self):
        """Test that get_valuation_summary_data groups and sorts structures naturally by name."""
        project = ProjectFactory.create()
        cert = PaymentCertificateFactory.create(project=project)

        # Create structures with names: SECTION 10: ..., SECTION 2: ..., SECTION 1: ...
        struct_10 = StructureFactory.create(
            project=project, name="SECTION 10: Structural"
        )
        struct_2 = StructureFactory.create(
            project=project, name="SECTION 2: Media Centre"
        )
        struct_1 = StructureFactory.create(
            project=project, name="SECTION 1: Preliminaries"
        )

        for struct in [struct_10, struct_2, struct_1]:
            bill = BillFactory.create(structure=struct)
            pkg = PackageFactory.create(bill=bill)
            LineItemFactory.create(
                project=project,
                structure=struct,
                bill=bill,
                package=pkg,
                is_work=True,
                total_price=Decimal("100.00"),
            )

        data = get_valuation_summary_data(cert)
        sections = data["grouped_sections"]

        # Natural sorting order by structure name: SECTION 1, SECTION 2, SECTION 10
        assert sections[0]["name"] == "SECTION 1: Preliminaries"
        assert sections[1]["name"] == "SECTION 2: Media Centre"
        assert sections[2]["name"] == "SECTION 10: Structural"


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
        response = client.get(
            url, {"front": "on", "summary": "on", "detailed": "on", "force": "on"}
        )
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
        response = client.get(
            url, {"front": "on", "summary": "on", "detailed": "on", "force": "on"}
        )
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert "Content-Disposition" in response
        assert "cover-summary-detailed_abridged_" in response["Content-Disposition"]


@pytest.mark.django_db
class TestCoverPageExporterNegation:
    """Test that the cover page Excel exporter correctly negates values for fields with 'less' indicators."""

    def test_exporter_negates_less_fields(self):
        """Verify export_cover_page_to_xlsx negates fields with 'less' in their label."""
        from decimal import Decimal
        from unittest.mock import PropertyMock, patch

        from app.BillOfQuantities.exporters.cover_page_exporter import (
            export_cover_page_to_xlsx,
        )

        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)
        cert = PaymentCertificateFactory.create(project=project)

        with patch(
            "app.BillOfQuantities.models.payment_certificate_models.PaymentCertificate.progressive_previous",
            new_callable=PropertyMock,
        ) as mock_prev:
            mock_prev.return_value = Decimal("900000.00")

            wb = export_cover_page_to_xlsx(cert)
            ws = wb["Cover Page"]

            # Search for row with label containing 'LESS: Previous Amount Due' and check value in column 7
            found_row_val = None
            for r in range(1, ws.max_row + 1):
                cell_label = ws.cell(row=r, column=1).value
                if cell_label and "less" in str(cell_label).lower():
                    found_row_val = ws.cell(row=r, column=7).value
                    break

            assert found_row_val is not None
            # Should be negated
            assert found_row_val == Decimal("-900000.00")


@pytest.mark.django_db
class TestCoverPageExporterLedgerFields:
    """Test that the cover page Excel exporter correctly resolves and outputs custom ledger fields."""

    def test_cover_page_export_custom_ledger_fields(self):
        """Test that exported Excel cover page contains the custom ledger fields and values."""
        from decimal import Decimal
        from app.BillOfQuantities.tests.factories import (
            AdvancePaymentFactory,
            RetentionFactory,
            PaymentCertificateFactory,
        )
        from app.Project.tests.factories import ProjectFactory
        from app.BillOfQuantities.exporters.cover_page_exporter import export_cover_page_to_xlsx

        user = AccountFactory.create()
        project = ProjectFactory.create(users=user)

        # Create transactions for current and previous certificate
        prev_cert = PaymentCertificateFactory.create(
            project=project, certificate_number=1, status="APPROVED"
        )
        cert = PaymentCertificateFactory.create(project=project, certificate_number=2)

        # Advance Payment (Current: 1000, Prev: 2000)
        AdvancePaymentFactory.create(
            project=project,
            payment_certificate=cert,
            amount=Decimal("1000.00"),
            transaction_type="DEBIT"
        )
        AdvancePaymentFactory.create(
            project=project,
            payment_certificate=prev_cert,
            amount=Decimal("2000.00"),
            transaction_type="DEBIT"
        )

        wb = export_cover_page_to_xlsx(cert)
        ws = wb["Cover Page"]

        # Check sheet cells for values
        found_ap_row = None
        for r in range(1, 45):
            val = ws.cell(row=r, column=1).value
            if val and "advance" in str(val).lower():
                found_ap_row = r
                break

        assert found_ap_row is not None
        # Raw value at column 7 should be 3000.00
        assert ws.cell(row=found_ap_row, column=7).value == Decimal("3000.00")

