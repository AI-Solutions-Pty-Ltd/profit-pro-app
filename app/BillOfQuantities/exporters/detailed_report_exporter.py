from decimal import Decimal

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from app.BillOfQuantities.models import LineItem
from app.BillOfQuantities.tasks import group_line_items_by_hierarchy


def export_detailed_report_to_xlsx(payment_certificate, is_abridged=False):
    """
    Export the detailed report for a payment certificate to XLSX format.
    Mirrors the layout of '03_MediaCentre_Detailed (1).xlsx'.
    """
    wb = openpyxl.Workbook()

    # We will create a sheet for each structure (section)
    if is_abridged:
        all_line_items = LineItem.abridged_payment_certificate(payment_certificate)
        line_items = all_line_items.filter(addendum=False, special_item=False)
    else:
        line_items = LineItem.construct_payment_certificate(payment_certificate)

    grouped_data = group_line_items_by_hierarchy(line_items)

    # Styles
    font_bold = Font(bold=True)
    font_bold_white = Font(bold=True, color="FFFFFFFF")
    font_italic_gray = Font(italic=True, color="FF666666")
    font_subtitle = Font(italic=True, color="FF666666")
    font_header = Font(bold=True, size=11)
    font_title = Font(bold=True, size=14)
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_wrap = Alignment(horizontal="left", vertical="top", wrap_text=True)

    border_bottom = Border(bottom=Side(style='thin'))
    border_bottom_thick = Border(bottom=Side(style='medium'))
    border_bottom_light = Border(bottom=Side(style='thin', color='FFE5E5E5'))

    fill_bill_header = PatternFill(start_color="FF333333", end_color="FF333333", fill_type="solid")
    fill_package_header = PatternFill(start_color="FFF2F2F2", end_color="FFF2F2F2", fill_type="solid")
    fill_section_footer = PatternFill(start_color="FFD19B3D", end_color="FFD19B3D", fill_type="solid")
    fill_zebra_even = PatternFill(start_color="FFFFFFFF", end_color="FFFFFFFF", fill_type="solid")
    fill_zebra_odd = PatternFill(start_color="FFF9F9F9", end_color="FFF9F9F9", fill_type="solid")
    fill_column_headers = PatternFill(start_color="FF111111", end_color="FF111111", fill_type="solid")

    if not grouped_data:
        ws = wb.active
        ws.title = "No Data"
        ws.append(["No data available for this report."])
        return wb

    # Remove the default sheet created by openpyxl
    default_sheet = wb.active

    for structure_idx, structure_data in enumerate(grouped_data, 1):
        structure = structure_data["structure"]
        sheet_name = structure.name[:31]  # Excel sheet names max 31 chars

        # If it's the first sheet being added, we can rename the default or just create new and delete default later
        ws = wb.create_sheet(title=sheet_name)

        cert_num = str(payment_certificate.certificate_number).zfill(2)
        cert_date = payment_certificate.created_at.strftime("%d %b %Y")
        project_name = payment_certificate.project.name

        # Row 1: Header
        ws.cell(row=1, column=1, value="[ LOGO ]").font = font_bold
        title_cell = ws.cell(row=1, column=2, value=f"SECTION {structure_idx} — {structure.name.upper()}")
        title_cell.font = font_title
        title_cell.alignment = align_center
        ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=8)
        
        cert_cell = ws.cell(row=1, column=9, value=f"Cert No. {cert_num}\n{cert_date}")
        cert_cell.alignment = Alignment(wrap_text=True, horizontal="right", vertical="center")
        cert_cell.font = font_bold
        ws.merge_cells(start_row=1, start_column=9, end_row=1, end_column=10)
        ws.cell(row=1, column=9).fill = fill_package_header
        ws.cell(row=1, column=10).fill = fill_package_header
        ws.row_dimensions[1].height = 60

        # Row 2: Subtitle
        sub_cell = ws.cell(row=2, column=1, value=f"{project_name} - Payment Certificate No. {cert_num} - {cert_date}")
        sub_cell.font = font_subtitle
        sub_cell.alignment = align_center
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=10)
        for col in range(1, 11):
            ws.cell(row=2, column=col).fill = fill_package_header

        # Row 3: Empty

        # Row 4: Column Headers
        ws.row_dimensions[4].height = 30
        headers = ['ITEM', 'PAY REF', 'DESCRIPTION', 'UNIT', 'TENDER QTY', 'RATE (R)', 'TENDER AMT (R)', 'CUMUL. CERT (R)', 'CERT (R)', 'AMOUNT DUE (R)']
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_idx, value=header)
            cell.font = font_bold_white
            cell.fill = fill_column_headers
            cell.alignment = align_center

        current_row = 5

        # Data Rows
        for bill_idx, bill_data in enumerate(structure_data["bills"], 1):
            bill = bill_data["bill"]

            # Bill Header
            ws.row_dimensions[current_row].height = 25
            ws.cell(row=current_row, column=1, value=f"BILL NO. {bill_idx} — {bill.name.upper()}")
            ws.cell(row=current_row, column=8, value=bill_data["cumulative"]).alignment = align_right
            ws.cell(row=current_row, column=9, value=bill_data["current"]).alignment = align_right
            ws.cell(row=current_row, column=10, value=bill_data["current"]).alignment = align_right
            for col in range(1, 11):
                cell = ws.cell(row=current_row, column=col)
                cell.fill = fill_bill_header
                cell.font = font_bold_white
            current_row += 1

            for package_data in bill_data["packages"]:
                package = package_data["package"]
                if package and package.name:
                    # Package Header
                    ws.row_dimensions[current_row].height = 20
                    ws.cell(row=current_row, column=1, value=f"{package.name}")
                    for col in range(1, 11):
                        cell = ws.cell(row=current_row, column=col)
                        cell.font = font_subtitle
                    current_row += 1

                item_row_count = 0
                for item in package_data["line_items"]:
                    ws.row_dimensions[current_row].height = 20
                    ws.cell(row=current_row, column=1, value=item.item_number or "").alignment = align_center
                    ws.cell(row=current_row, column=2, value="") # Pay Ref, usually empty or mapped to something else
                    ws.cell(row=current_row, column=3, value=item.description or "").alignment = align_wrap
                    ws.cell(row=current_row, column=4, value=item.unit_measurement or "").alignment = align_center
                    ws.cell(row=current_row, column=5, value=item.budgeted_quantity).alignment = align_right
                    ws.cell(row=current_row, column=6, value=item.unit_price).alignment = align_right
                    ws.cell(row=current_row, column=7, value=item.total_price).alignment = align_right
                    ws.cell(row=current_row, column=8, value=item.total_claimed).alignment = align_right
                    ws.cell(row=current_row, column=9, value=item.current_claim).alignment = align_right
                    ws.cell(row=current_row, column=10, value=item.current_claim).alignment = align_right

                    fill_to_use = fill_zebra_even if item_row_count % 2 == 0 else fill_zebra_odd
                    for col in range(1, 11):
                        cell = ws.cell(row=current_row, column=col)
                        cell.fill = fill_to_use
                        cell.border = border_bottom_light

                    current_row += 1
                    item_row_count += 1

            # Bill Footer
            ws.row_dimensions[current_row].height = 20
            ws.cell(row=current_row, column=1, value=f"Carried to Summary — Bill No. {bill_idx}")
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=7)
            ws.cell(row=current_row, column=1).alignment = align_right
            
            ws.cell(row=current_row, column=8, value=bill_data["cumulative"]).alignment = align_right
            ws.cell(row=current_row, column=9, value=bill_data["current"]).alignment = align_right
            ws.cell(row=current_row, column=10, value=bill_data["current"]).alignment = align_right
            
            for col in range(1, 11):
                cell = ws.cell(row=current_row, column=col)
                cell.font = font_bold
                cell.border = border_bottom_thick
            current_row += 1

        # Structure Footer
        ws.cell(row=current_row, column=1, value=f"SECTION {structure_idx} TOTAL — {structure.name.upper()}")
        ws.cell(row=current_row, column=8, value=structure_data["cumulative"]).alignment = align_right
        ws.cell(row=current_row, column=9, value=structure_data["current"]).alignment = align_right
        ws.cell(row=current_row, column=10, value=structure_data["current"]).alignment = align_right
        for col in range(1, 11):
            cell = ws.cell(row=current_row, column=col)
            cell.fill = fill_section_footer
            cell.font = font_bold_white
        current_row += 2

        # Final Footer
        company = "Profit Pro" # Or get from settings/project
        footer_text = f"{company}  |  Payment Certificate No. {cert_num}  |  {cert_date}"
        ws.cell(row=current_row, column=1, value=footer_text)
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=10)

        # Set Column Widths
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 65
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 15
        ws.column_dimensions['G'].width = 15
        ws.column_dimensions['H'].width = 15
        ws.column_dimensions['I'].width = 15
        ws.column_dimensions['J'].width = 15

        # Format numbers
        for row in ws.iter_rows(min_row=5, max_row=current_row):
            for cell in row[4:]: # columns E to J (idx 4 to 9)
                if isinstance(cell.value, (int, float, Decimal)):
                    cell.number_format = '#,##0.00'

    # Remove the default sheet if we added custom sheets
    if len(wb.sheetnames) > 1 and "Sheet" in wb.sheetnames:
        wb.remove(wb["Sheet"])

    return wb
