# This script will lowercase all account emails in the database
from django.core.management.base import BaseCommand

from app.Account.models import Account


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        accounts = Account.objects.all()
        for account in accounts:
            account.email = account.email.lower()
            account.save()
        self.stdout.write(
            self.style.SUCCESS("Successfully lowercased all account emails")
        )
