import glob
import os
import subprocess
import sys

from django.conf import settings


def get_apps():
    shared_apps = settings.SHARED_APPS
    # strip 'app.' from the string
    shared_apps = [app.replace("app.", "") for app in shared_apps]
    return shared_apps


def find_all_migration_files():
    """Find all python files (excl init files) in the migrations directory of each app."""
    files = []
    for app in get_apps():
        migration_files = glob.glob(f"app/{app}/migrations/*.py")
        # Filter out __init__.py files
        migration_files = [f for f in migration_files if not f.endswith("__init__.py")]
        files.extend(migration_files)
    return files


def clear_migration_table():
    apps = get_apps()
    for app in apps:
        subprocess.run(
            [sys.executable, "manage.py", "migrate", "--fake", app, "zero"],
            check=True,
        )


def remove_local_migration_files():
    files = find_all_migration_files()
    for file in files:
        os.remove(file)


def make_migrations():
    subprocess.run([sys.executable, "manage.py", "makemigrations"], check=True)


def fake_initial():
    subprocess.run(
        [sys.executable, "manage.py", "migrate", "--fake-initial"], check=True
    )


def full_reset_migration_files_and_migration_table():
    clear_migration_table()
    remove_local_migration_files()
    make_migrations()
    fake_initial()


def reset_migrations_table():
    clear_migration_table()
    fake_initial()
