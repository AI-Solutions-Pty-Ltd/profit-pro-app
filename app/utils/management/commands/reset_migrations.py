from django.core.management.base import BaseCommand
from utils.database import (
    full_reset_migration_files_and_migration_table,
    reset_migrations_table,
)


class Command(BaseCommand):
    help = "Reset migrations in the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--full-reset",
            action="store_true",
            help="Perform a full reset including removing migration files",
        )
        parser.add_argument(
            "--migration-table-only",
            action="store_true",
            help="Perform a reset of the migration table only",
        )

    def handle(self, *args, **options):
        if options["full_reset"]:
            self.stdout.write("Performing full migration reset...")
            full_reset_migration_files_and_migration_table()
            self.stdout.write(
                self.style.SUCCESS("Migration reset completed successfully")
            )
        elif options["migration_table_only"]:
            self.stdout.write("Resetting migration tables only...")
            reset_migrations_table()
            self.stdout.write(
                self.style.SUCCESS("Migration reset completed successfully")
            )
        else:
            self.stdout.write(
                "No action specified. Use --full-reset or --migration-table-only."
            )
