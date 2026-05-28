from django.conf import settings
from django.middleware.csrf import get_token

from app.Notices.models import Notice
from app.Project.models import Role


def custom_context_processor(request):
    # Define your context variables here
    roles_dict = {role[0]: role[1] for role in Role.choices}

    # Count notices and dummy attention items for badge
    notice_count = Notice.objects.count() + 5  # 5 dummy attention items

    # Get CSRF token for easy access in templates
    csrf_token = get_token(request)

    show_demo_welcome_popup = False
    user = request.user
    if user.is_authenticated:
        view_name = request.resolver_match.view_name if request.resolver_match else None
        excluded_views = [
            "project:project-create",
            "users:account:user_detail",
            "users:account:user_edit",
        ]
        if view_name not in excluded_views:
            from typing import cast

            from app.Account.models import Account

            account = cast(Account, user)
            show_demo_welcome_popup = bool(
                account.has_demo_permission
                and not account.get_projects.filter(is_demo=False).exists()
            )

    return {
        "SITE_NAME": settings.SITE_NAME,
        "ROLES": roles_dict,
        "NOTICE_COUNT": notice_count,
        "CSRF_TOKEN": csrf_token,
        "show_demo_welcome_popup": show_demo_welcome_popup,
    }
