"""Account model signals"""

from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from app.Account.models import Account


@receiver(post_save, sender=Account)
def assign_default_group(sender, instance, created, **kwargs):
    """
    Assign default 'contractor' group to newly created users if they have no groups.

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
