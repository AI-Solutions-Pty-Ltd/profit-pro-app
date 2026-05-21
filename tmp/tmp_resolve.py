import os
import sys
import django

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.local")
django.setup()

from django.urls import resolve, Resolver404

try:
    match = resolve("/users/account/demo-expired/")
    print(f"Match: {match}")
    print(f"View name: {match.view_name}")
    print(f"Namespace: {match.namespace}")
    print(f"Namespaces: {match.namespaces}")
    full_name = f"{match.namespace}:{match.view_name}" if match.namespace else match.view_name
    print(f"Full constructed name: {full_name}")
except Resolver404 as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Other Error: {e}")
