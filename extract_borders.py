import openpyxl

wb = openpyxl.load_workbook("01_Front.xlsx")
ws = wb.active


def print_borders(row, col, desc):
    c = ws.cell(row=row, column=col)
    b = c.border
    top = b.top.style if b and b.top else "None"
    bottom = b.bottom.style if b and b.bottom else "None"
    left = b.left.style if b and b.left else "None"
    right = b.right.style if b and b.right else "None"
    print(
        f"Row {row} Col {col} ({desc}) - Borders: Top={top}, Bottom={bottom}, Left={left}, Right={right}"
    )


print_borders(11, 1, "CONTRACT VALUE SUMMARY Header")
print_borders(12, 1, "Description Header")
print_borders(13, 1, "Original Contract Value")
print_borders(17, 1, "Total Contract Value")
print_borders(30, 1, "TOTAL AMOUNT NOW CERTIFIED")
print_borders(34, 1, "AUTHORISATION Header")
print_borders(36, 1, "Project Manager")
