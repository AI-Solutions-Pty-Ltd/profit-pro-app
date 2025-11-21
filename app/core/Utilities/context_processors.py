from django.conf import settings


def custom_context_processor(request):
    # Define your context variables here
    return {
        "SITE_NAME": settings.SITE_NAME,
    }
