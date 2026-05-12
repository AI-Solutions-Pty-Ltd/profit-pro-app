from django import template
from django.conf import settings

from app.Estimator.calculations import format_num

register = template.Library()


@register.filter
def currency(value):
    """Format a number as currency, dropping trailing zeros (R 1,234.56 / R 1,234 / R 1.5)."""
    if value is None:
        return "-"
    formatted = format_num(value, with_commas=True)
    if not formatted:
        return "-"
    symbol = getattr(settings, "ESTIMATOR_CURRENCY_SYMBOL", "R")
    return f"{symbol} {formatted}"


@register.filter
def qty(value):
    """Format a quantity at ≤2dp with trailing zeros stripped (1,234 / 1,234.5 / 1,234.56)."""
    if value is None:
        return "-"
    return format_num(value, with_commas=True) or "-"


@register.filter
def num(value):
    """Format a number for <input value=""> — ≤2dp, no commas, trailing zeros stripped."""
    return format_num(value, with_commas=False)


@register.filter
def pct(value):
    """Format a number as a percentage (e.g., 12.3%)."""
    if value is None:
        return "-"
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return "-"


@register.filter
def apply_wastage(value, wastage_pct):
    """Apply wastage percentage to a quantity: qty * (1 + wastage_pct/100)."""
    if value is None:
        return None
    try:
        return float(value) * (1 + float(wastage_pct or 0) / 100)
    except (ValueError, TypeError):
        return value


@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
