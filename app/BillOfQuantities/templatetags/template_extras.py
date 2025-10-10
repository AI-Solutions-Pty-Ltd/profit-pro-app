from django import template

register = template.Library()


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)


@register.filter
def acc(value):
    return "-" if value == 0 else value


@register.simple_tag
def define(val=None):
    return val


@register.filter()
def varadd(val1, val2):
    return val1 + val2


@register.filter(name="ifusername")
def ifusername(queryset, value):
    for group in queryset.groups.all():
        if group.name == value:
            return True
    return False


@register.filter(name="ifinlist")
def ifinlist(value, compare_list):
    return True if value in compare_list else False


@register.filter(name="notinlist")
def notinlist(value, compare_list):
    return False if value in compare_list else True
