from django.db import migrations


def set_superusers_to_administration(apps, schema_editor):
    """Set ADMINISTRATION subscription for all superusers."""
    Account = apps.get_model("Account", "Account")
    Account.objects.filter(is_superuser=True).update(subscription="ADMINISTRATION")


def noop_reverse(apps, schema_editor):
    """No-op reverse migration."""
    return


class Migration(migrations.Migration):
    dependencies = [
        ("Account", "0008_alter_account_subscription"),
    ]

    operations = [
        migrations.RunPython(
            set_superusers_to_administration,
            reverse_code=noop_reverse,
        ),
    ]
