from django.db import migrations


def clear_senders_receivers(apps, schema_editor):
    CorrespondenceDialog = apps.get_model("BillOfQuantities", "CorrespondenceDialog")
    CorrespondenceDialog.objects.all().update(sender="", recipient="")


class Migration(migrations.Migration):
    dependencies = [
        ("BillOfQuantities", "0020_contractualcorrespondence_recipient_user_and_more"),
    ]

    operations = [
        migrations.RunPython(clear_senders_receivers, migrations.RunPython.noop),
    ]
