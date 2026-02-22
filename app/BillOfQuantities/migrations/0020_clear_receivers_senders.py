from django.db import migrations


def clear_senders_receivers(apps, schema_editor):
    CorrespondenceDialog = apps.get_model("BillOfQuantities", "CorrespondenceDialog")
    CorrespondenceDialog.objects.all().update(sender="", receiver="")


class Migration(migrations.Migration):
    dependencies = [
        ("BillOfQuantities", "0019_alter_claim_period"),
    ]

    operations = [
        migrations.RunPython(clear_senders_receivers, migrations.RunPython.noop),
    ]
