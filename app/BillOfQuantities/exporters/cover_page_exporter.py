import datetime
from decimal import Decimal

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


def export_cover_page_to_xlsx(payment_certificate, wb=None):
    """
    Export the cover page report for a payment certificate to XLSX format.
    Mirrors the precise styling, colors, and layout of '01_Front.xlsx'.
    """
    if wb is None:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Cover Page"
    else:
        ws = wb.create_sheet(title="Cover Page")

    project = payment_certificate.project
    cert_num = str(payment_certificate.certificate_number).zfill(2)
    cert_date = (
        payment_certificate.approved_on.strftime("%d %b %Y")
        if payment_certificate.approved_on
        else datetime.datetime.now().strftime("%d %b %Y")
    )

    # Precise Colors and Styles
    c_black = "FF111111"
    c_grey_text = "FF717171"
    c_white = "FFFFFFFF"

    font_bold = Font(bold=True, color=c_black)
    font_normal = Font(bold=False, color=c_black)
    font_title = Font(bold=True, size=14, color=c_black)
    font_white_bold = Font(bold=True, color=c_white)
    font_less = Font(color=c_grey_text, italic=True)
    font_italic_small = Font(italic=True, size=9, color=c_grey_text)

    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")

    fill_light_grey = PatternFill(
        start_color="FFF2F2F2", end_color="FFF2F2F2", fill_type="solid"
    )
    fill_white = PatternFill(
        start_color="FFFFFFFF", end_color="FFFFFFFF", fill_type="solid"
    )
    fill_dark_blue = PatternFill(
        start_color="FF1B3A6B", end_color="FF1B3A6B", fill_type="solid"
    )
    fill_gold = PatternFill(
        start_color="FFC8963E", end_color="FFC8963E", fill_type="solid"
    )
    fill_separator = PatternFill(
        start_color="FF003300", end_color="FF003300", fill_type="solid"
    )  # Dark green/black line

    border_thin_top_bottom = Border(top=Side(style="thin"), bottom=Side(style="thin"))
    border_thin_bottom = Border(bottom=Side(style="thin"))

    # Column widths
    ws.column_dimensions["A"].width = 45
    ws.column_dimensions["B"].width = 25
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 15
    ws.column_dimensions["E"].width = 15
    ws.column_dimensions["F"].width = 15
    ws.column_dimensions["G"].width = 25

    # Row Heights
    ws.row_dimensions[1].height = 55.5
    ws.row_dimensions[2].height = 13.5
    ws.row_dimensions[3].height = 3.0
    ws.row_dimensions[4].height = 6.0
    ws.row_dimensions[10].height = 6.0

    # Initialize all cells to white fill to avoid default gridlines
    for row in range(1, 45):
        for col in range(1, 8):
            ws.cell(row=row, column=col).fill = fill_white
            ws.cell(row=row, column=col).font = font_normal

    # Row 1: Logo & Title
    ws.cell(row=1, column=1, value="[ LOGO ]").font = font_bold
    ws.cell(row=1, column=1).alignment = align_center

    title_cell = ws.cell(row=1, column=3, value="PAYMENT CERTIFICATE")
    title_cell.font = font_title
    title_cell.alignment = align_center
    ws.merge_cells(start_row=1, start_column=3, end_row=1, end_column=6)

    cert_cell = ws.cell(row=1, column=7, value=f"Cert No. {cert_num}\n{cert_date}")
    cert_cell.alignment = Alignment(
        wrap_text=True, horizontal="right", vertical="center"
    )
    cert_cell.font = Font(color=c_grey_text)

    # Row 1 Borders
    for col in range(1, 8):
        ws.cell(row=1, column=col).border = border_thin_top_bottom
        ws.cell(row=1, column=col).fill = fill_light_grey

    # Row 2: Project Info
    project_info = f"{project.name} - Contract No. {project.contract_number or ''}"
    ws.cell(row=2, column=1, value=project_info).font = Font(
        italic=True, color=c_grey_text
    )
    ws.cell(row=2, column=1).alignment = align_center
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=7)

    # Row 2 Borders
    for col in range(1, 8):
        ws.cell(row=2, column=col).border = border_thin_bottom
        ws.cell(row=2, column=col).fill = fill_light_grey

    # Row 3: Thick separator line
    for col in range(1, 8):
        ws.cell(row=3, column=col).fill = fill_separator

    # Info Rows (5 to 9)
    info_rows = [
        ("Certificate No.", cert_num),
        ("Assessment Date", cert_date),
        ("Date of Certificate", cert_date),
        ("Contract No.", project.contract_number or ""),
        (
            "Retention Free Amount",
            f"R {getattr(project, 'retention_free_amount', Decimal('0.00')):,}",
        ),
    ]

    for idx, (label, val) in enumerate(info_rows, start=5):
        ws.row_dimensions[idx].height = 18.0
        ws.cell(row=idx, column=1, value=label).font = Font(color=c_grey_text)
        ws.cell(row=idx, column=1).alignment = align_right
        ws.cell(row=idx, column=2, value=val).font = font_bold

    # Contract Value Summary Header
    ws.row_dimensions[11].height = 18.0
    ws.cell(row=11, column=1, value="CONTRACT VALUE SUMMARY").font = font_bold
    for col in range(1, 8):
        ws.cell(row=11, column=col).fill = fill_light_grey
        ws.cell(row=11, column=col).border = border_thin_top_bottom
    ws.merge_cells(start_row=11, start_column=1, end_row=11, end_column=7)

    # Contract Summary Column Headers
    ws.row_dimensions[12].height = 15.75
    ws.cell(row=12, column=1, value="Description").font = Font(color=c_grey_text)
    ws.cell(row=12, column=7, value="Value (R)").font = Font(color=c_grey_text)
    ws.cell(row=12, column=7).alignment = align_right

    current_row = 13

    orig_val = project.original_contract_value or Decimal("0.00")
    amends_val = project.addendum_contract_value or Decimal("0.00")
    sub_total_contract = orig_val + amends_val
    vat_val_contract = (
        sub_total_contract * Decimal("0.15") if project.vat else Decimal("0.00")
    )
    total_contract = sub_total_contract + vat_val_contract

    contract_rows = [
        ("Original Contract Value", orig_val),
        ("Total Contract Amendments To Date", amends_val),
        ("Sub Total", sub_total_contract),
        ("VAT at 15%" if project.vat else "No VAT", vat_val_contract),
        ("Total Contract Value (incl. VAT)", total_contract),
    ]

    for i, (desc, val) in enumerate(contract_rows):
        ws.row_dimensions[current_row].height = 16.5
        ws.cell(row=current_row, column=1, value=desc)
        cell_val = ws.cell(row=current_row, column=7, value=val)
        cell_val.number_format = "#,##0.00"

        # Highlight total row
        if "Total Contract Value" in desc:
            for col in range(1, 8):
                ws.cell(row=current_row, column=col).fill = fill_dark_blue
            ws.cell(row=current_row, column=1).font = font_white_bold
            cell_val.font = font_white_bold
        else:
            if "Total" in desc or "Sub Total" in desc:
                ws.cell(row=current_row, column=1).font = font_bold
                cell_val.font = font_bold
            # Alternate row fills
            if i % 2 != 0:
                for col in range(1, 8):
                    ws.cell(row=current_row, column=col).fill = fill_light_grey
        current_row += 1

    current_row += 1

    # Payment Due Summary Header
    ws.row_dimensions[current_row].height = 18.0
    ws.cell(
        row=current_row, column=1, value=f"PAYMENT DUE — CERTIFICATE NO. {cert_num}"
    ).font = font_bold
    for col in range(1, 8):
        ws.cell(row=current_row, column=col).fill = fill_light_grey
        ws.cell(row=current_row, column=col).border = border_thin_top_bottom
    ws.merge_cells(
        start_row=current_row, start_column=1, end_row=current_row, end_column=7
    )
    current_row += 1

    # Payment Summary Column Headers
    ws.row_dimensions[current_row].height = 15.75
    ws.cell(row=current_row, column=1, value="Description").font = Font(
        color=c_grey_text
    )
    ws.cell(row=current_row, column=7, value="Amount (R)").font = Font(
        color=c_grey_text
    )
    ws.cell(row=current_row, column=7).alignment = align_right
    current_row += 1

    work_done_cum = payment_certificate.work_progressive_to_date or Decimal("0.00")
    comp_events = payment_certificate.contract_current_claim_total or Decimal("0.00")
    material = getattr(
        payment_certificate, "material_on_site_to_date", Decimal("0.00")
    )  # if exists
    total_work_done = work_done_cum + comp_events + material
    retention = getattr(
        payment_certificate, "retention_to_date", Decimal("0.00")
    )  # if exists
    sub_total_1 = total_work_done - retention
    prev_amount_due = payment_certificate.progressive_previous or Decimal("0.00")
    sub_total_2 = payment_certificate.current_claim_total or Decimal("0.00")
    vat_val_payment = sub_total_2 * Decimal("0.15") if project.vat else Decimal("0.00")
    total_certified = sub_total_2 + vat_val_payment

    payment_rows = [
        (f"Value of Work Done (Cumulative — Cert No. {cert_num})", work_done_cum),
        ("Plus: Compensation Events", comp_events),
        ("Plus: Material On Site", material),
        ("Total Value of Work Done", total_work_done),
        ("Less: Retention", retention),
        ("Sub Total", sub_total_1),
        ("Less: Previous Amount Due", prev_amount_due),
        ("Sub Total", sub_total_2),
        ("Plus: V.A.T. at 15%" if project.vat else "No VAT", vat_val_payment),
        ("TOTAL AMOUNT NOW CERTIFIED (incl. VAT)", total_certified),
    ]

    for i, (desc, val) in enumerate(payment_rows):
        ws.row_dimensions[current_row].height = 16.5
        ws.cell(row=current_row, column=1, value=desc)
        cell_val = ws.cell(row=current_row, column=7, value=val)
        cell_val.number_format = "#,##0.00"

        # Highlight total row
        if "TOTAL AMOUNT" in desc:
            for col in range(1, 8):
                ws.cell(row=current_row, column=col).fill = fill_gold
            ws.cell(row=current_row, column=1).font = font_white_bold
            cell_val.font = font_white_bold
        else:
            if "Total" in desc or "Sub Total" in desc:
                ws.cell(row=current_row, column=1).font = font_bold
                cell_val.font = font_bold
            if "Less:" in desc:
                ws.cell(row=current_row, column=1).font = font_less
            # Alternate row fills
            if i % 2 != 0:
                for col in range(1, 8):
                    ws.cell(row=current_row, column=col).fill = fill_light_grey
        current_row += 1

    # Retention Note
    ret_amount = getattr(payment_certificate, "retention_to_date", Decimal("0.00"))
    note = f"Note: 5% Retention not deducted — handled by Valterra GSS. Retention: R {ret_amount:,}"
    ws.cell(row=current_row, column=1, value=note).font = font_italic_small
    ws.merge_cells(
        start_row=current_row, start_column=1, end_row=current_row, end_column=7
    )
    current_row += 2

    # Authorisation Section
    ws.row_dimensions[current_row].height = 18.0
    ws.cell(row=current_row, column=1, value="AUTHORISATION").font = font_bold
    for col in range(1, 8):
        ws.cell(row=current_row, column=col).fill = fill_light_grey
        ws.cell(row=current_row, column=col).border = border_thin_top_bottom
    ws.merge_cells(
        start_row=current_row, start_column=1, end_row=current_row, end_column=7
    )
    current_row += 1

    auth_rows = [
        ("Project Manager", ""),
        ("Quantity Surveyor", ""),
        ("Section Manager – Project Governance", ""),
        ("Senior Manager PMU", ""),
    ]

    for title, name in auth_rows:
        ws.row_dimensions[current_row].height = 18.0
        ws.cell(row=current_row, column=1, value=title).font = font_bold

        ws.cell(row=current_row, column=2, value=name)
        ws.cell(row=current_row, column=2).fill = fill_light_grey
        ws.merge_cells(
            start_row=current_row, start_column=2, end_row=current_row, end_column=3
        )

        ws.cell(row=current_row, column=4, value="Signature: ______________________")
        ws.cell(row=current_row, column=4).fill = fill_light_grey
        ws.cell(row=current_row, column=4).font = Font(color=c_grey_text)
        ws.merge_cells(
            start_row=current_row, start_column=4, end_row=current_row, end_column=5
        )

        ws.cell(row=current_row, column=7, value="Date: _______________")
        ws.cell(row=current_row, column=7).fill = fill_light_grey
        ws.cell(row=current_row, column=7).font = Font(color=c_grey_text)
        current_row += 1

    current_row += 1

    # Footer
    footer_text = f"Profit Pro | {project.name} | Payment Certificate No. {cert_num} | {cert_date}"
    ws.cell(row=current_row, column=1, value=footer_text).font = font_italic_small
    ws.cell(row=current_row, column=1).alignment = align_center
    ws.merge_cells(
        start_row=current_row, start_column=1, end_row=current_row, end_column=7
    )

    return wb
