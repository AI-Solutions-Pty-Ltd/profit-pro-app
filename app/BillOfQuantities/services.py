"""Services for Bill of Quantities app."""

from decimal import Decimal

import pandas as pd
from django.db import transaction

from app.BillOfQuantities.forms import LineItemExcelUploadForm
from app.BillOfQuantities.models import Bill, LineItem, Package, Structure


def clean_pd_data(value):
    """Clean pandas data: handle NaN, nan, and empty strings."""
    if pd.isna(value) or str(value).lower() == "nan":
        return ""
    return str(value).strip()


def import_boq_from_excel(project, excel_file):
    """Process Excel file and create structures, bills, and line items for a project.

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
            # Tolerantly check if we have multiple sheets but one of them is the target 'Setup Template'
            if "Setup Template" in sheet_names:
                df = pd.read_excel(excel_file_obj, sheet_name="Setup Template")
            else:
                return 0, [
                    f"Excel file must contain only one sheet or a sheet named 'Setup Template'. Found {len(sheet_names)} sheets: {', '.join(sheet_names)}."
                ]
        else:
            # Read the single sheet
            df = pd.read_excel(excel_file_obj, sheet_name=0)
    except Exception as e:
        return 0, [f"Error reading Excel file: {str(e)}"]

    # Define standard column key mappings
    standard_columns = {
        "structure": "Structure",
        "bill_no": "Bill No.",
        "package": "Package",
        "item_no": "Item No.",
        "pay_ref": "Pay Ref",
        "description": "Description",
        "unit": "Unit",
        "contract_quantity": "Contract Quantity",
        "contract_rate": "Contract Rate",
        "contract_amount": "Contract Amount",
    }

    # Normalize DataFrame column names to allow flexible headers
    original_columns = list(df.columns)
    mapped_columns = {}

    def normalize_header(h):
        if not isinstance(h, str):
            return str(h)
        normalized = (
            h.strip().lower().replace(".", "_").replace(" ", "_").replace("-", "_")
        )
        while "__" in normalized:
            normalized = normalized.replace("__", "_")
        return normalized.strip("_")

    for col in original_columns:
        norm_col = normalize_header(col)
        # Match against our standard keys normalized
        for std_key, std_name in standard_columns.items():
            if norm_col == std_key or norm_col == normalize_header(std_name):
                mapped_columns[col] = std_key
                break

    # Rename matching columns in DataFrame
    df = df.rename(columns=mapped_columns)

    # Validate required columns
    required_keys = [
        "structure",
        "bill_no",
        "item_no",
        "description",
        "unit",
        "contract_quantity",
        "contract_rate",
        "contract_amount",
    ]

    # Missing optional columns like package or pay_ref will be injected automatically
    optional_keys = ["package", "pay_ref"]
    for opt_key in optional_keys:
        if opt_key not in df.columns:
            df[opt_key] = ""

    errors = []
    for req_key in required_keys:
        if req_key not in df.columns:
            std_label = standard_columns[req_key]
            errors.append(f"Excel file must contain a '{std_label}' column.")

    if errors:
        return 0, errors

    valid_forms = []

    for row_index, row in df.iterrows():
        display_row = (
            int(str(row_index)) + 2
        )  # Row 1 is header, data starts at Row 2 in Excel
        try:
            structure_name = clean_pd_data(row["structure"])
            bill_name = clean_pd_data(row["bill_no"])
            package_name = clean_pd_data(row["package"])
            item_number = clean_pd_data(row["item_no"])
            payment_reference = clean_pd_data(row["pay_ref"])
            description = clean_pd_data(row["description"])
            unit_measurement = clean_pd_data(row["unit"])
            budgeted_quantity = clean_pd_data(row["contract_quantity"])
            unit_price = clean_pd_data(row["contract_rate"])
            total_price = clean_pd_data(row["contract_amount"])

            # Clean "rate only" or empty values
            is_rate_only = str(budgeted_quantity).lower().strip() == "rate only"

            if is_rate_only:
                qty_val = 0.0
                rate_val = 0.0
                amount_val = 0.0
            else:
                try:
                    qty_val = (
                        round(float(budgeted_quantity), 2) if budgeted_quantity else 0.0
                    )
                except (ValueError, TypeError):
                    errors.append(
                        f"Row {display_row}: Invalid Contract Quantity '{budgeted_quantity}'."
                    )
                    continue

                try:
                    rate_val = round(float(unit_price), 2) if unit_price else 0.0
                except (ValueError, TypeError):
                    errors.append(
                        f"Row {display_row}: Invalid Contract Rate '{unit_price}'."
                    )
                    continue

                try:
                    amount_val = round(float(total_price), 2) if total_price else 0.0
                except (ValueError, TypeError):
                    errors.append(
                        f"Row {display_row}: Invalid Contract Amount '{total_price}'."
                    )
                    continue

            # Check calculation mismatches using Decimal for absolute precision
            if not is_rate_only and (qty_val != 0 or rate_val != 0 or amount_val != 0):
                qty_dec = Decimal(str(qty_val))
                rate_dec = Decimal(str(rate_val))
                amount_dec = Decimal(str(amount_val))
                expected_amount = round(qty_dec * rate_dec, 2)

                # Allow a small tolerance of $0.05 for rounding variations
                if abs(expected_amount - amount_dec) > Decimal("0.05"):
                    errors.append(
                        f"Row {display_row}: Calculation mismatch. Contract Amount ({amount_val:.2f}) "
                        f"does not match Contract Quantity ({qty_val:.2f}) * Contract Rate ({rate_val:.2f}) = {float(expected_amount):.2f}."
                    )
                    continue

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
                "budgeted_quantity": qty_val,
                "unit_price": rate_val,
                "total_price": amount_val,
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
