"""Chart of accounts data for use in utils and migrations."""

# Standard chart of accounts organized by financial statement type
STANDARD_CHART_OF_ACCOUNTS = [
    # Assets (Balance Sheet) - 1000-1999
    ("1000", "Cash and Cash Equivalents", "Balance Sheet"),
    ("1100", "Accounts Receivable", "Balance Sheet"),
    ("1200", "Inventory", "Balance Sheet"),
    ("1300", "Prepaid Expenses", "Balance Sheet"),
    ("1400", "Property, Plant and Equipment", "Balance Sheet"),
    ("1500", "Accumulated Depreciation", "Balance Sheet"),
    ("1600", "Intangible Assets", "Balance Sheet"),
    # Liabilities (Balance Sheet) - 2000-2999
    ("2000", "Accounts Payable", "Balance Sheet"),
    ("2100", "Accrued Expenses", "Balance Sheet"),
    ("2200", "Taxes Payable", "Balance Sheet"),
    ("2300", "Short-term Debt", "Balance Sheet"),
    ("2400", "Long-term Debt", "Balance Sheet"),
    ("2500", "Deferred Revenue", "Balance Sheet"),
    # Equity (Balance Sheet) - 3000-3999
    ("3000", "Share Capital", "Balance Sheet"),
    ("3100", "Retained Earnings", "Balance Sheet"),
    ("3200", "Additional Paid-in Capital", "Balance Sheet"),
    ("3300", "Dividends Paid", "Balance Sheet"),
    # Revenue (Income Statement) - 4000-4999
    ("4000", "Sales Revenue", "Income Statement"),
    ("4100", "Service Revenue", "Income Statement"),
    ("4200", "Interest Income", "Income Statement"),
    ("4300", "Other Income", "Income Statement"),
    ("4400", "Sales Returns and Allowances", "Income Statement"),
    ("4500", "Sales Discounts", "Income Statement"),
    # Cost of Goods Sold (Income Statement) - 5000-5999
    ("5000", "Cost of Goods Sold", "Income Statement"),
    ("5100", "Purchase Returns", "Income Statement"),
    ("5200", "Purchase Discounts", "Income Statement"),
    ("5300", "Freight-in", "Income Statement"),
    # Operating Expenses (Income Statement) - 6000-6999
    ("6000", "Salaries and Wages", "Income Statement"),
    ("6100", "Rent Expense", "Income Statement"),
    ("6200", "Utilities Expense", "Income Statement"),
    ("6300", "Insurance Expense", "Income Statement"),
    ("6400", "Depreciation Expense", "Income Statement"),
    ("6500", "Bad Debt Expense", "Income Statement"),
    ("6600", "Marketing and Advertising", "Income Statement"),
    ("6700", "Office Supplies", "Income Statement"),
    ("6800", "Professional Fees", "Income Statement"),
    ("6900", "Travel and Entertainment", "Income Statement"),
    # Other Expenses (Income Statement) - 7000-7999
    ("7000", "Interest Expense", "Income Statement"),
    ("7100", "Tax Expense", "Income Statement"),
    ("7200", "Loss on Sale of Assets", "Income Statement"),
    ("7300", "Gain on Sale of Assets", "Income Statement"),
    # Non-operating Income and Expenses (Income Statement) - 8000-8999
    ("8000", "Non-operating Interest Income", "Income Statement"),
    ("8100", "Loss on Disposal of Assets", "Income Statement"),
    ("8200", "Other Non-operating Income", "Income Statement"),
    ("8300", "Other Non-operating Expenses", "Income Statement"),
    # Suspense Account (Balance Sheet) - 9999
    ("9999", "Suspense Account", "Balance Sheet"),
]

# Financial statement types that should exist
FINANCIAL_STATEMENT_TYPES = [
    "Balance Sheet",
    "Income Statement",
]

# Organized chart of accounts by statement type
CHART_BY_STATEMENT = {
    "Balance Sheet": [
        ("1000", "Cash and Cash Equivalents"),
        ("1100", "Accounts Receivable"),
        ("1200", "Inventory"),
        ("1300", "Prepaid Expenses"),
        ("1400", "Property, Plant and Equipment"),
        ("1500", "Accumulated Depreciation"),
        ("1600", "Intangible Assets"),
        ("2000", "Accounts Payable"),
        ("2100", "Accrued Expenses"),
        ("2200", "Taxes Payable"),
        ("2300", "Short-term Debt"),
        ("2400", "Long-term Debt"),
        ("2500", "Deferred Revenue"),
        ("3000", "Share Capital"),
        ("3100", "Retained Earnings"),
        ("3200", "Additional Paid-in Capital"),
        ("3300", "Dividends Paid"),
        ("9999", "Suspense Account"),
    ],
    "Income Statement": [
        ("4000", "Sales Revenue"),
        ("4100", "Service Revenue"),
        ("4200", "Interest Income"),
        ("4300", "Other Income"),
        ("4400", "Sales Returns and Allowances"),
        ("4500", "Sales Discounts"),
        ("5000", "Cost of Goods Sold"),
        ("5100", "Purchase Returns"),
        ("5200", "Purchase Discounts"),
        ("5300", "Freight-in"),
        ("6000", "Salaries and Wages"),
        ("6100", "Rent Expense"),
        ("6200", "Utilities Expense"),
        ("6300", "Insurance Expense"),
        ("6400", "Depreciation Expense"),
        ("6500", "Bad Debt Expense"),
        ("6600", "Marketing and Advertising"),
        ("6700", "Office Supplies"),
        ("6800", "Professional Fees"),
        ("6900", "Travel and Entertainment"),
        ("7000", "Interest Expense"),
        ("7100", "Tax Expense"),
        ("7200", "Loss on Sale of Assets"),
        ("7300", "Other Operating Expenses"),
        ("8000", "Gain on Sale of Assets"),
        ("8100", "Non-operating Interest Income"),
        ("8200", "Loss on Disposal of Assets"),
        ("8300", "Other Non-operating Income"),
        ("8400", "Other Non-operating Expenses"),
    ],
}
