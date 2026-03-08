from django.conf import settings

from app.Notices.models import Notice
from app.Project.models import Role


def custom_context_processor(request):
    # Define your context variables here
    roles_dict = {role[0]: role[1] for role in Role.choices}

    # Count notices and dummy attention items for badge
    notice_count = Notice.objects.count() + 5  # 5 dummy attention items

    return {
        "SITE_NAME": settings.SITE_NAME,
        "ROLES": roles_dict,
        "NOTICE_COUNT": notice_count,
    }
