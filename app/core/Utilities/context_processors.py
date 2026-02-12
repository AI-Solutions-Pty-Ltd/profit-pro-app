from django.conf import settings

from app.Project.models import Role


def custom_context_processor(request):
    # Define your context variables here
    roles_dict = {role[0]: role[1] for role in Role.choices}
    return {
        "SITE_NAME": settings.SITE_NAME,
        "ROLES": roles_dict,
    }
