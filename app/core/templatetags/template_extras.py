from django import template
from django.db.models import QuerySet

from app.Project.models.project_roles import ProjectRole, Role

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
def user_in_group(user, group_names):
    """Check if a user is in a group."""
    group_names = group_names.split(",")
    return user.groups.filter(name__in=group_names).exists()


@register.filter(name="projectroles")
def project_roles(user, project) -> QuerySet[ProjectRole]:
    """Get all roles that the user has for the given project."""

    if user.is_superuser:
        return ProjectRole.objects.all()

    # Get all project roles for this user in the project
    return project.project_roles.filter(user=user)


@register.filter(name="userhasrole")
def user_has_role(roles, roles_to_check):
    """Check if any of the given roles are in the list of roles."""
    if roles.filter(role=Role.ADMIN).exists():
        return True
    # If roles_to_check is a string, check single role
    roles_to_check = roles_to_check.split(",")
    return any(role in roles for role in roles_to_check)


@register.filter(name="ifinlist")
def ifinlist(value, compare_list):
    """Check if a value is in a list."""
    return True if value in compare_list else False


@register.filter(name="notinlist")
def notinlist(value, compare_list):
    """Check if a value is not in a list."""
    return False if value in compare_list else True


@register.filter(name="numsign")
def numsign(value, arg=None):
    """Return one of three values based on number sign.

    Similar to Django's |yesno filter but for number sign checking.

    Usage:
        {{ value|numsign:"positive,negative,zero" }}
        {{ value|numsign }}  # Returns "positive", "negative", or "zero"

    Args:
        value: The number to check.
        arg: Comma-separated string of three values for positive, negative, zero.

    Returns:
        The appropriate value based on the number's sign.
    """
    if arg is None:
        arg = "positive,negative,zero"

    bits = arg.split(",")
    if len(bits) < 3:
        raise ValueError("numsign filter requires at least three arguments")

    value = float(value)

    if value > 0:
        return bits[0]
    elif value < 0:
        return bits[1]
    else:
        return bits[2]


@register.filter
def get(obj, key):
    """Get a value from a dictionary by key."""
    return obj.get(key)


@register.filter
def lookup(dictionary, key):
    """Lookup a key in a dictionary, useful for template context."""
    return dictionary.get(key, [])
