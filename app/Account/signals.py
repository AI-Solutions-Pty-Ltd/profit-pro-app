"""Account model signals"""

from datetime import timedelta

from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from app.Account.models import Account
from app.Account.subscription_config import Subscription


@receiver(post_save, sender=Account)
def assign_default_group(sender, instance, created, **kwargs):
    """
    Assign default 'contractor' group and set demo expiry for newly created users.

    Args:
        sender: The model class (Account)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    if created:
        # Check if user has any groups
        if not instance.groups.exists():
            # Get or create the contractor group
            contractor_group, _ = Group.objects.get_or_create(name="contractor")
            # Add user to the contractor group
            instance.groups.add(contractor_group)

        # Set demo expiry if on demo tier
        if instance.subscription == Subscription.DEMO_TIER and not instance.subscription_expires_at:
            instance.subscription_expires_at = timezone.now() + timedelta(days=7)
            instance.save(update_fields=["subscription_expires_at"])
