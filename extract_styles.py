import openpyxl

wb = openpyxl.load_workbook("01_Front.xlsx")
ws = wb.active

for row in range(1, 40):
    for col in range(1, 8):
        c = ws.cell(row=row, column=col)
        if c.value and type(c.value) == str:
            if (
                "TOTAL" in c.value.upper()
                or "SUMMARY" in c.value.upper()
                or "DUE" in c.value.upper()
            ):
                fill_color = c.fill.start_color.index if c.fill else "None"
                font_color = c.font.color.index if c.font and c.font.color else "None"
                font_bold = c.font.bold if c.font else False
                print(
                    f"Row {row} Col {col} - {c.value} - Fill: {fill_color} Font Color: {font_color} Bold: {font_bold}"
                )

        # Print background colors for rows where value might be empty but styled
        if row in [11, 14, 18, 23, 31, 35]:
            if col == 1:
                fill_color = c.fill.start_color.index if c.fill else "None"
                print(f"Row {row} sample fill: {fill_color}")
