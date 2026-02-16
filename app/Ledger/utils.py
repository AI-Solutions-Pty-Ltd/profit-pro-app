"""Utility functions for Ledger app."""

from app.Ledger.models import Ledger
from app.Project.models import Company


def get_standard_chart_of_accounts() -> list[dict]:
    """
    Get the standard chart of accounts for a generic business.

    Returns:
        List of dictionaries containing ledger information with:
        - code: 4-digit ledger code
        - name: Ledger account name
        - financial_statement: Which financial statement this belongs to
    """
    return [
        # Assets (Balance Sheet) - 1000-1999
        {
            "code": "1000",
            "name": "Cash and Cash Equivalents",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "1100",
            "name": "Accounts Receivable",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "1200",
            "name": "Inventory",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "1300",
            "name": "Prepaid Expenses",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "1400",
            "name": "Property, Plant and Equipment",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "1500",
            "name": "Accumulated Depreciation",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "1600",
            "name": "Intangible Assets",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        # Liabilities (Balance Sheet) - 2000-2999
        {
            "code": "2000",
            "name": "Accounts Payable",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "2100",
            "name": "Accrued Expenses",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "2200",
            "name": "Taxes Payable",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "2300",
            "name": "Short-term Debt",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "2400",
            "name": "Long-term Debt",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "2500",
            "name": "Deferred Revenue",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        # Equity (Balance Sheet) - 3000-3999
        {
            "code": "3000",
            "name": "Share Capital",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "3100",
            "name": "Retained Earnings",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "3200",
            "name": "Additional Paid-in Capital",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        {
            "code": "3300",
            "name": "Dividends Paid",
            "financial_statement": Ledger.FinancialStatement.BALANCE_SHEET,
        },
        # Revenue (Income Statement) - 4000-4999
        {
            "code": "4000",
            "name": "Sales Revenue",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "4100",
            "name": "Service Revenue",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "4200",
            "name": "Interest Income",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "4300",
            "name": "Other Income",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "4400",
            "name": "Sales Returns and Allowances",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "4500",
            "name": "Sales Discounts",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        # Cost of Goods Sold (Income Statement) - 5000-5999
        {
            "code": "5000",
            "name": "Cost of Goods Sold",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "5100",
            "name": "Purchase Returns",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "5200",
            "name": "Purchase Discounts",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "5300",
            "name": "Freight-in",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        # Operating Expenses (Income Statement) - 6000-6999
        {
            "code": "6000",
            "name": "Salaries and Wages",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "6100",
            "name": "Rent Expense",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "6200",
            "name": "Utilities Expense",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "6300",
            "name": "Insurance Expense",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "6400",
            "name": "Depreciation Expense",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "6500",
            "name": "Bad Debt Expense",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "6600",
            "name": "Marketing and Advertising",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "6700",
            "name": "Office Supplies",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "6800",
            "name": "Professional Fees",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "6900",
            "name": "Travel and Entertainment",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        # Other Expenses (Income Statement) - 7000-7999
        {
            "code": "7000",
            "name": "Interest Expense",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "7100",
            "name": "Tax Expense",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "7200",
            "name": "Loss on Sale of Assets",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "7300",
            "name": "Other Operating Expenses",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        # Non-operating Items (Income Statement) - 8000-8999
        {
            "code": "8000",
            "name": "Gain on Sale of Assets",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
        {
            "code": "8100",
            "name": "Extraordinary Items",
            "financial_statement": Ledger.FinancialStatement.INCOME_STATEMENT,
        },
    ]


def create_standard_chart_of_accounts(company: Company) -> list[Ledger]:
    """
    Create the standard chart of accounts for a company.

    Args:
        company: The company to create ledgers for

    Returns:
        List of created Ledger objects

    Raises:
        IntegrityError: If any ledger code already exists for the company
    """
    ledgers = []
    chart_of_accounts = get_standard_chart_of_accounts()

    for account_data in chart_of_accounts:
        ledger = Ledger.objects.create(
            company=company,
            code=account_data["code"],
            name=account_data["name"],
            financial_statement=account_data["financial_statement"],
        )
        ledgers.append(ledger)

    return ledgers
