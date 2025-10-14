from django import template

register = template.Library()


@register.filter
def addstr(arg1, arg2):
    """Concatenate arg1 & arg2."""
    return str(arg1) + str(arg2)


@register.filter
def acc(value):
    """Return a value if it is not zero."""
    return "-" if value == 0 else value


@register.simple_tag
def define(val=None):
    """Define a variable in a template."""
    return val


@register.filter()
def varadd(val1, val2):
    """Add two values."""
    return val1 + val2


@register.filter(name="useringroup")
def user_in_group(user, group_name):
    """Check if a user is in a group."""
    return user.groups.filter(name=group_name).exists()


@register.filter(name="ifinlist")
def ifinlist(value, compare_list):
    """Check if a value is in a list."""
    return True if value in compare_list else False


@register.filter(name="notinlist")
def notinlist(value, compare_list):
    """Check if a value is not in a list."""
    return False if value in compare_list else True
