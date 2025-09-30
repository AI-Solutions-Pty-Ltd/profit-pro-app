import glob
import os

from django.conf import settings


def get_apps():
    return settings.SHARED_APPS


def find_all_migration_files():
    """Find all python files (excl init files) in the migrations directory of each app."""
    files = []
    for app in get_apps():
        migration_files = glob.glob(f"{app}/migrations/*.py")
        # Filter out __init__.py files
        migration_files = [f for f in migration_files if not f.endswith("__init__.py")]
        files.extend(migration_files)
    return files


def clear_migration_table():
    apps = get_apps()
    for app in apps:
        os.system(f"python manage.py migrate --fake {app} zero")


def remove_local_migration_files():
    files = find_all_migration_files()
    for file in files:
        os.remove(file)


def make_migrations():
    os.system("python manage.py makemigrations")


def fake_initial():
    os.system("python manage.py migrate --fake-initial")


def full_reset_migration_files_and_migration_table():
    clear_migration_table()
    remove_local_migration_files()
    make_migrations()
    fake_initial()


def reset_migrations_table():
    clear_migration_table()
    fake_initial()
