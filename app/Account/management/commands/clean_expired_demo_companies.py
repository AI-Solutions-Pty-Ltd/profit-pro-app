"""Management command to clean demo companies of expired demo accounts."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from app.Account.models import Account
from app.Account.subscription_config import Subscription
from app.Project.models import Company


class Command(BaseCommand):
    """Purges demo companies for users whose demo tier has expired."""

    help = "Finds all expired demo accounts and deletes their scoped demo companies"

    def handle(self, *args, **options):
        # Find all expired demo tier users
        expired_users = Account.objects.filter(
            subscription=Subscription.DEMO_TIER,
            subscription_expires_at__lt=timezone.now(),
        )

        self.stdout.write(
            self.style.WARNING(
                f"Found {expired_users.count()} expired demo accounts. "
                "Proceeding to clean demo companies..."
            )
        )

        total_deleted = 0
        for user in expired_users:
            deleted_count = Company.clean_demo_companies(user)
            if deleted_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Cleaned {deleted_count} demo companies for expired user: {user.email}"
                    )
                )
                total_deleted += deleted_count

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully completed cleanup. Total companies deleted: {total_deleted}"
            )
        )
