from django import template
from django.conf import settings

register = template.Library()


@register.filter
def currency(value):
    """Format a number as currency (R 1,234.56)."""
    if value is None:
        return '-'
    try:
        symbol = getattr(settings, 'ESTIMATOR_CURRENCY_SYMBOL', 'R')
        return f"{symbol} {float(value):,.2f}"
    except (ValueError, TypeError):
        return '-'


@register.filter
def qty(value):
    """Format a quantity with 2 decimal places."""
    if value is None:
        return '-'
    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return '-'


@register.filter
def pct(value):
    """Format a number as a percentage (e.g., 12.3%)."""
    if value is None:
        return '-'
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return '-'


@register.filter
def apply_wastage(value, wastage_pct):
    """Apply wastage percentage to a quantity: qty * (1 + wastage_pct/100)."""
    if value is None:
        return None
    try:
        return float(value) * (1 + float(wastage_pct or 0) / 100)
    except (ValueError, TypeError):
        return value
