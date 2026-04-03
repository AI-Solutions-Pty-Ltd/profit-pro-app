"""
Pure calculation functions for the Project Resource Estimator.

This module contains all business logic calculations decoupled from any
data source (database, Excel, etc.). Each function accepts plain Python
values (Decimal, dict, list) and returns computed results.

Specifications use a generic 'components' list so calculations work for
any material type — Concrete (cement+sand+stone), Masonry (bricks+mortar),
Plastering (cement+sand), or any custom mix.

Usage:
    from app.Estimator.calculations import calculate_rate_per_unit, calculate_boq_summary

    # Concrete specification
    rate = calculate_rate_per_unit(components=[
        {'name': 'Cement', 'qty_per_unit': Decimal('7.5'), 'market_rate': Decimal('85.00')},
        {'name': 'Sand',   'qty_per_unit': Decimal('0.5'), 'market_rate': Decimal('350.00')},
        {'name': 'Stone',  'qty_per_unit': Decimal('0.8'), 'market_rate': Decimal('420.00')},
    ])

    # Masonry specification — different ingredients, same function
    rate = calculate_rate_per_unit(components=[
        {'name': 'Bricks', 'qty_per_unit': Decimal('55'),   'market_rate': Decimal('12.00')},
        {'name': 'Mortar', 'qty_per_unit': Decimal('0.03'),  'market_rate': Decimal('1800.00')},
    ])
"""

from decimal import Decimal


def calculate_rate_per_unit(components):
    """
    Calculate the blended rate per unit from material components.

    Works for any specification type — concrete, masonry, plastering, etc.
    Each component contributes (qty_per_unit * market_rate) to the total.

    Args:
        components: list of dicts, each with:
            - name (str, optional): component name (e.g. 'Cement', 'Bricks')
            - qty_per_unit (Decimal or None): quantity of material per unit
            - market_rate (Decimal or None): market rate per unit of material

    Returns:
        Decimal: total rate per unit
    """
    total = Decimal("0")
    for comp in components:
        qty = comp.get("qty_per_unit")
        rate = comp.get("market_rate")
        if qty and rate:
            total += Decimal(str(qty)) * Decimal(str(rate))
    return total


def calculate_total_quantity(boq_quantity, qty_per_unit):
    """
    Calculate total material quantity needed for a specification.

    Args:
        boq_quantity (Decimal or None): total BoQ volume
        qty_per_unit (Decimal or None): material quantity per unit

    Returns:
        Decimal: total quantity needed
    """
    if boq_quantity is None or qty_per_unit is None:
        return Decimal("0")
    return Decimal(str(boq_quantity)) * Decimal(str(qty_per_unit))


def calculate_contract_amount(contract_quantity, contract_rate):
    """
    Calculate contract amount = quantity * rate.

    Args:
        contract_quantity (Decimal or None): contracted quantity
        contract_rate (Decimal or None): contracted rate

    Returns:
        Decimal or None: contract amount, or None if inputs are missing
    """
    if contract_quantity and contract_rate:
        return Decimal(str(contract_quantity)) * Decimal(str(contract_rate))
    return None


def calculate_materials_rate(rate_override=None, specification_rate=None):
    """
    Determine the effective materials rate for a BoQ item.
    Uses override if provided, otherwise falls back to specification rate.

    Args:
        rate_override (Decimal or None): manually overridden rate
        specification_rate (Decimal or None): rate from linked specification

    Returns:
        Decimal or None: effective materials rate
    """
    if rate_override is not None:
        return Decimal(str(rate_override))
    if specification_rate is not None:
        return Decimal(str(specification_rate))
    return None


def calculate_progress_amount(materials_rate, progress_quantity):
    """
    Calculate progress amount = materials_rate * progress_quantity.

    Args:
        materials_rate (Decimal or None): effective rate per unit
        progress_quantity (Decimal or None): progress quantity

    Returns:
        Decimal or None: progress amount, or None if inputs are missing
    """
    if materials_rate is not None and progress_quantity:
        return Decimal(str(materials_rate)) * Decimal(str(progress_quantity))
    return None


def calculate_forecast_amount(materials_rate, forecast_quantity):
    """
    Calculate forecast amount = materials_rate * forecast_quantity.

    Args:
        materials_rate (Decimal or None): effective rate per unit
        forecast_quantity (Decimal or None): forecast quantity

    Returns:
        Decimal or None: forecast amount, or None if inputs are missing
    """
    if materials_rate is not None and forecast_quantity:
        return Decimal(str(materials_rate)) * Decimal(str(forecast_quantity))
    return None


def calculate_boq_summary(items):
    """
    Calculate aggregate totals from a list of BoQ items.

    Args:
        items: list of dicts, each with:
            - contract_quantity (Decimal or None)
            - contract_rate (Decimal or None)
            - progress_quantity (Decimal or None)
            - forecast_quantity (Decimal or None)
            - rate_override (Decimal or None)
            - specification_rate (Decimal or None): rate from linked spec

    Returns:
        dict with:
            - total_contract_amount (Decimal)
            - total_progress_amount (Decimal)
            - total_forecast_amount (Decimal)
            - item_count (int)
    """
    total_contract = Decimal("0")
    total_progress = Decimal("0")
    total_forecast = Decimal("0")
    total_materials_rate = Decimal("0")
    total_labour_rate = Decimal("0")

    for item in items:
        contract_amt = calculate_contract_amount(
            item.get("contract_quantity"),
            item.get("contract_rate"),
        )
        if contract_amt:
            total_contract += contract_amt

        materials_rate = calculate_materials_rate(
            item.get("rate_override"),
            item.get("specification_rate"),
        )

        if materials_rate is not None:
            total_materials_rate += materials_rate

        labour_rate = item.get("labour_rate")
        if labour_rate is not None:
            total_labour_rate += Decimal(str(labour_rate))

        # Baseline new price = materials + labour
        baseline_price = (materials_rate or Decimal("0")) + (
            labour_rate or Decimal("0")
        )
        effective_rate = baseline_price if baseline_price > 0 else None

        progress_amt = calculate_progress_amount(
            effective_rate,
            item.get("progress_quantity"),
        )
        if progress_amt:
            total_progress += progress_amt

        forecast_amt = calculate_forecast_amount(
            effective_rate,
            item.get("forecast_quantity"),
        )
        if forecast_amt:
            total_forecast += forecast_amt

    return {
        "total_contract_amount": total_contract,
        "total_materials_rate": total_materials_rate,
        "total_labour_rate": total_labour_rate,
        "total_progress_amount": total_progress,
        "total_forecast_amount": total_forecast,
        "item_count": len(items),
    }


def calculate_variance(amount_a, amount_b):
    """
    Calculate variance between two amounts.

    Args:
        amount_a (Decimal or None): base amount
        amount_b (Decimal or None): comparison amount

    Returns:
        tuple: (variance_amount, variance_pct) where
            variance_amount = amount_b - amount_a
            variance_pct = (variance / amount_a) * 100, or None if amount_a is zero/None
    """
    if amount_a is None or amount_b is None:
        return (None, None)
    a = Decimal(str(amount_a))
    b = Decimal(str(amount_b))
    variance = b - a
    if a != 0:
        pct = (variance / a) * Decimal("100")
    else:
        pct = None
    return (variance, pct)


def calculate_pct_of_total(item_amount, grand_total):
    """
    Calculate an item's percentage of the grand total.

    Args:
        item_amount (Decimal or None): individual amount
        grand_total (Decimal or None): sum of all amounts

    Returns:
        Decimal or None: percentage, or None if grand_total is zero/None
    """
    if not grand_total or grand_total == 0 or item_amount is None:
        return None
    return (Decimal(str(item_amount)) / Decimal(str(grand_total))) * Decimal("100")


def calculate_specification_summary(specifications):
    """
    Calculate aggregate material totals across all specifications.

    Works with any specification type — each spec carries its own
    'components' list, so Concrete, Masonry, Plastering etc. are all
    handled uniformly.

    Args:
        specifications: list of dicts, each with:
            - spec_type (str): e.g. 'Concrete', 'Masonry'
            - name (str): specification name
            - boq_quantity (Decimal)
            - components: list of dicts, each with:
                - name (str): component name (e.g. 'Cement', 'Bricks')
                - qty_per_unit (Decimal): quantity per unit
                - market_rate (Decimal): market rate
                - unit (str, optional): unit of measure

    Returns:
        dict with:
            - component_totals: dict keyed by component name → total quantity
            - specs: list of enriched spec dicts with rate_per_unit and
              component totals added
    """
    component_totals = {}
    enriched_specs = []

    for spec in specifications:
        boq_qty = spec.get("boq_quantity", Decimal("0"))
        components = spec.get("components", [])

        rate = calculate_rate_per_unit(components)

        enriched_components = []
        for comp in components:
            comp_name = comp.get("name", "")
            qty_per_unit = comp.get("qty_per_unit", Decimal("0"))
            total_qty = calculate_total_quantity(boq_qty, qty_per_unit)

            # Accumulate into global totals by component name
            if comp_name in component_totals:
                component_totals[comp_name] += total_qty
            else:
                component_totals[comp_name] = total_qty

            enriched_components.append(
                {
                    **comp,
                    "total_quantity": total_qty,
                }
            )

        enriched = dict(spec)
        enriched.update(
            {
                "rate_per_unit": rate,
                "components": enriched_components,
            }
        )
        enriched_specs.append(enriched)

    return {
        "component_totals": component_totals,
        "specs": enriched_specs,
    }
