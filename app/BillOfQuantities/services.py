"""Services for Bill of Quantities app."""

import pandas as pd
from django.db import transaction
from app.BillOfQuantities.models import Bill, LineItem, Package, Structure
from app.BillOfQuantities.forms import LineItemExcelUploadForm

def clean_pd_data(value):
    """Clean pandas data: handle NaN, nan, and empty strings."""
    if pd.isna(value) or str(value).lower() == "nan":
        return ""
    return str(value).strip()

def import_boq_from_excel(project, excel_file):
    """
    Process Excel file and create structures, bills, and line items for a project.
    
    Args:
        project: The Project instance
        excel_file: A file-like object or path to the Excel file
        
    Returns:
        tuple: (success_count, errors_list)
    """
    try:
        # Check number of sheets in Excel file
        excel_file_obj = pd.ExcelFile(excel_file)
        sheet_names = excel_file_obj.sheet_names

        if len(sheet_names) > 1:
            return 0, [f"Excel file must contain only one sheet. Found {len(sheet_names)} sheets."]

        # Read the single sheet
        df = pd.read_excel(excel_file_obj, sheet_name=0)
    except Exception as e:
        return 0, [f"Error reading Excel file: {str(e)}"]

    # Validate required columns
    columns = [
        "Structure", "Bill No.", "Package", "Item No.", "Pay Ref",
        "Description", "Unit", "Contract Quantity", "Contract Rate", "Contract Amount"
    ]
    for column in columns:
        if column not in df.columns:
            return 0, [f"Excel file must contain a '{column}' column."]

    errors = []
    valid_forms = []

    for row_index, row in df.iterrows():
        display_row = int(str(row_index)) + 1
        try:
            structure_name = clean_pd_data(row["Structure"])
            bill_name = clean_pd_data(row["Bill No."])
            package_name = clean_pd_data(row["Package"])
            item_number = clean_pd_data(row["Item No."])
            payment_reference = clean_pd_data(row["Pay Ref"])
            description = clean_pd_data(row["Description"])
            unit_measurement = clean_pd_data(row["Unit"])
            budgeted_quantity = clean_pd_data(row["Contract Quantity"])
            unit_price = clean_pd_data(row["Contract Rate"])
            total_price = clean_pd_data(row["Contract Amount"])

            if str(budgeted_quantity).lower().strip() == "rate only":
                budgeted_quantity = 0
                unit_price = 0
                total_price = 0

            data = {
                "project": project,
                "structure": structure_name,
                "bill": bill_name,
                "package": package_name,
                "row_index": row_index,
                "item_number": item_number,
                "payment_reference": payment_reference,
                "description": description,
                "unit_measurement": unit_measurement,
                "budgeted_quantity": round(float(budgeted_quantity), 2) if budgeted_quantity else 0,
                "unit_price": round(float(unit_price), 2) if unit_price else 0.0,
                "total_price": round(float(total_price), 2) if total_price else 0.0,
            }
            if not data["package"]:
                del data["package"]

            line_item_form = LineItemExcelUploadForm(data=data)
            if line_item_form.is_valid():
                valid_forms.append(line_item_form)
            else:
                row_errors = []
                for field, field_errors in line_item_form.errors.items():
                    for error in field_errors:
                        row_errors.append(f"{field}: {error}")
                errors.append(f"Row {display_row}: {'; '.join(row_errors)}")

        except (ValueError, TypeError) as e:
            errors.append(f"Row {display_row}: Data conversion error - {str(e)}")

    if errors:
        return 0, errors

    # No errors, erase previous data and save in transaction
    with transaction.atomic():
        Structure.objects.filter(project=project).delete()
        Bill.objects.filter(structure__project=project).delete()
        Package.objects.filter(bill__structure__project=project).delete()
        LineItem.objects.filter(structure__project=project).delete()

        created_count = 0
        for idx, line_item_form in enumerate(valid_forms):
            line_item_form.save(row_index=idx)
            created_count += 1
            
    return created_count, []
