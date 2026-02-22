"""Utility functions for Ledger app."""

from app.Ledger.chart_data import (
    CHART_BY_STATEMENT,
    FINANCIAL_STATEMENT_TYPES,
    STANDARD_CHART_OF_ACCOUNTS,
)
from app.Ledger.models import FinancialStatement, Ledger
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
        {
            "code": code,
            "name": name,
            "financial_statement": statement_name,
        }
        for code, name, statement_name in STANDARD_CHART_OF_ACCOUNTS
    ]


def get_chart_by_statement_type(statement_name: str) -> list[dict]:
    """
    Get chart of accounts filtered by financial statement type.

    Args:
        statement_name: Name of the financial statement (e.g., "Balance Sheet", "Income Statement")

    Returns:
        List of dictionaries containing ledger information for the specified statement type
    """
    if statement_name not in CHART_BY_STATEMENT:
        return []

    return [
        {
            "code": code,
            "name": name,
            "financial_statement": statement_name,
        }
        for code, name in CHART_BY_STATEMENT[statement_name]
    ]


def get_financial_statement_types() -> list[str]:
    """
    Get all available financial statement types.

    Returns:
        List of financial statement type names
    """
    return FINANCIAL_STATEMENT_TYPES.copy()


def create_standard_chart_for_company(company: Company) -> list[Ledger]:
    """
    Create the standard chart of accounts for a company.

    Args:
        company: The company to create ledgers for

    Returns:
        List of created Ledger objects
    """
    created_ledgers = []

    # Get or create financial statements
    financial_statements = {}
    for statement_name in FINANCIAL_STATEMENT_TYPES:
        fs, _ = FinancialStatement.objects.get_or_create(name=statement_name)
        financial_statements[statement_name] = fs

    # Create ledgers for each account
    for code, name, statement_name in STANDARD_CHART_OF_ACCOUNTS:
        ledger = Ledger.objects.create(
            company=company,
            financial_statement=financial_statements[statement_name],
            code=code,
            name=name,
        )
        created_ledgers.append(ledger)

    return created_ledgers


def get_suspense_account(company: Company) -> Ledger:
    """
    Get or create the suspense account for a company.

    Args:
        company: The company to get the suspense account for

    Returns:
        The suspense account Ledger object
    """
    balance_sheet_fs, _ = FinancialStatement.objects.get_or_create(name="Balance Sheet")

    suspense_account, _ = Ledger.objects.get_or_create(
        company=company,
        code="9999",
        defaults={
            "name": "Suspense Account",
            "financial_statement": balance_sheet_fs,
        },
    )

    return suspense_account
