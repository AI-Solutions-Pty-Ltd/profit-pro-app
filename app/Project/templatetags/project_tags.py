from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows dictionary key lookup using a variable in templates."""
    if dictionary:
        return dictionary.get(key)
    return None
