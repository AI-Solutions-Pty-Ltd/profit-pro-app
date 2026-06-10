import datetime
from decimal import Decimal

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

def export_cover_page_to_xlsx(payment_certificate):
    """
    Export the cover page report for a payment certificate to XLSX format.
    Mirrors the layout of '01_Front.xlsx'.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cover Page"

    project = payment_certificate.project
    cert_num = str(payment_certificate.certificate_number).zfill(2)
    cert_date = payment_certificate.approved_on.strftime("%d %b %Y") if payment_certificate.approved_on else datetime.datetime.now().strftime("%d %b %Y")
    
    # Styles
    font_bold = Font(bold=True)
    font_bold_white = Font(bold=True, color="FFFFFFFF")
    font_title = Font(bold=True, size=14)
    font_header = Font(bold=True, size=11)
    
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    
    border_bottom_thick = Border(bottom=Side(style='medium'))
    border_all = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    fill_header = PatternFill(start_color="FF333333", end_color="FF333333", fill_type="solid")
    fill_section = PatternFill(start_color="FFF2F2F2", end_color="FFF2F2F2", fill_type="solid")

    # Column widths
    ws.column_dimensions['A'].width = 45
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 25

    # Header Row 1
    ws.cell(row=1, column=1, value="[ LOGO ]").font = font_bold
    
    title_cell = ws.cell(row=1, column=3, value="PAYMENT CERTIFICATE")
    title_cell.font = font_title
    title_cell.alignment = align_center
    ws.merge_cells(start_row=1, start_column=3, end_row=1, end_column=5)
    
    cert_cell = ws.cell(row=1, column=6, value=f"Cert No. {cert_num}\n{cert_date}")
    cert_cell.alignment = Alignment(wrap_text=True, horizontal="right", vertical="center")
    cert_cell.font = font_bold

    # Project Name Row 2
    ws.cell(row=2, column=1, value=f"{project.name}").font = font_bold
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=6)

    # Info Rows
    ws.cell(row=5, column=1, value="Certificate No.").font = font_bold
    ws.cell(row=5, column=2, value=cert_num)

    ws.cell(row=6, column=1, value="Assessment Date").font = font_bold
    ws.cell(row=6, column=2, value=cert_date)

    ws.cell(row=7, column=1, value="Date of Certificate").font = font_bold
    ws.cell(row=7, column=2, value=cert_date)

    ws.cell(row=8, column=1, value="Contract No.").font = font_bold
    ws.cell(row=8, column=2, value=project.contract_number or "")

    # Contract Value Summary Header
    ws.cell(row=11, column=1, value="CONTRACT VALUE SUMMARY").font = font_bold
    for col in range(1, 7):
        ws.cell(row=11, column=col).fill = fill_section
    ws.merge_cells(start_row=11, start_column=1, end_row=11, end_column=6)

    # Contract Summary Column Headers
    ws.cell(row=12, column=1, value="Description").font = font_bold
    ws.cell(row=12, column=6, value="Value (R)").font = font_bold
    ws.cell(row=12, column=6).alignment = align_right

    current_row = 13
    
    # Values
    orig_val = project.original_contract_value or Decimal('0.00')
    amends_val = project.addendum_contract_value or Decimal('0.00')
    sub_total_contract = orig_val + amends_val
    vat_val_contract = sub_total_contract * Decimal('0.15') if project.vat else Decimal('0.00')
    total_contract = sub_total_contract + vat_val_contract

    contract_rows = [
        ("Original Contract Value", orig_val),
        ("Total Contract Amendments To Date", amends_val),
        ("Sub Total", sub_total_contract),
        ("VAT at 15%" if project.vat else "No VAT", vat_val_contract),
        ("Total Contract Value (incl. VAT)", total_contract),
    ]

    for desc, val in contract_rows:
        ws.cell(row=current_row, column=1, value=desc)
        cell_val = ws.cell(row=current_row, column=6, value=val)
        cell_val.number_format = '#,##0.00'
        if "Total" in desc or "Sub Total" in desc:
            ws.cell(row=current_row, column=1).font = font_bold
            cell_val.font = font_bold
        current_row += 1

    current_row += 1

    # Payment Due Summary Header
    ws.cell(row=current_row, column=1, value=f"PAYMENT DUE — CERTIFICATE NO. {cert_num}").font = font_bold
    for col in range(1, 7):
        ws.cell(row=current_row, column=col).fill = fill_section
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=6)
    current_row += 1

    # Payment Summary Column Headers
    ws.cell(row=current_row, column=1, value="Description").font = font_bold
    ws.cell(row=current_row, column=6, value="Amount (R)").font = font_bold
    ws.cell(row=current_row, column=6).alignment = align_right
    current_row += 1

    # Using standard cumulative values from model
    work_done_cum = payment_certificate.work_progressive_to_date or Decimal('0.00')
    comp_events = payment_certificate.contract_current_claim_total or Decimal('0.00')
    material = getattr(payment_certificate, 'material_on_site_to_date', Decimal('0.00')) # if exists
    total_work_done = work_done_cum + comp_events + material
    retention = getattr(payment_certificate, 'retention_to_date', Decimal('0.00')) # if exists
    sub_total_1 = total_work_done - retention
    prev_amount_due = payment_certificate.progressive_previous or Decimal('0.00')
    sub_total_2 = payment_certificate.current_claim_total or Decimal('0.00') # NET AMOUNT NOW CERTIFIED
    vat_val_payment = sub_total_2 * Decimal('0.15') if project.vat else Decimal('0.00')
    total_certified = sub_total_2 + vat_val_payment

    payment_rows = [
        ("Value of Work Done (Cumulative)", work_done_cum),
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

    for desc, val in payment_rows:
        ws.cell(row=current_row, column=1, value=desc)
        cell_val = ws.cell(row=current_row, column=6, value=val)
        cell_val.number_format = '#,##0.00'
        if "Total" in desc or "Sub Total" in desc or "TOTAL" in desc:
            ws.cell(row=current_row, column=1).font = font_bold
            cell_val.font = font_bold
        current_row += 1

    current_row += 2

    # Authorisation Section
    ws.cell(row=current_row, column=1, value="AUTHORISATION").font = font_bold
    current_row += 1

    auth_rows = [
        ("Project Manager", ""),
        ("Quantity Surveyor", ""),
        ("Section Manager", ""),
        ("Senior Manager", ""),
    ]

    for title, name in auth_rows:
        ws.cell(row=current_row, column=1, value=title).font = font_bold
        ws.cell(row=current_row, column=2, value=name)
        ws.cell(row=current_row, column=4, value="Signature: ___________________")
        ws.cell(row=current_row, column=6, value="Date: __________")
        current_row += 1

    current_row += 2
    
    # Footer
    company = "Profit Pro" # Or get from settings
    ws.cell(row=current_row, column=1, value=company).font = font_bold

    return wb
