from django import template

register = template.Library()


@register.filter
def sum_values(values):
    """Sum a list of numeric values."""
    try:
        return sum(float(v) for v in values if v is not None)
    except (TypeError, ValueError):
        return 0


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key."""
    return dictionary.get(key)
