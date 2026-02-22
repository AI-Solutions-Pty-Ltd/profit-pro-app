# Generated migration to convert financial_statement choices to ForeignKey

from django.db import migrations, models


def migrate_choices_to_temp(apps, schema_editor):
    """Copy data from original financial_statement field to temp field."""
    Ledger = apps.get_model("Ledger", "Ledger")

    for ledger in Ledger.objects.all():
        # Copy the original field value to temp field
        ledger.financial_statement_temp = ledger.financial_statement
        ledger.save()


def migrate_financial_statement_choices_to_fk(apps, schema_editor):
    """Migrate existing financial_statement choices to ForeignKey relationships."""
    Ledger = apps.get_model("Ledger", "Ledger")
    FinancialStatement = apps.get_model("Ledger", "FinancialStatement")

    # Map the old choices to the new FinancialStatement names
    choice_mapping = {
        "balance_sheet": "Balance Sheet",
        "income_statement": "Income Statement",
        "cash_flow_statement": "Cash Flow Statement",
        "statement_of_changes_in_equity": "Statement of Changes in Equity",
    }

    # Get all existing FinancialStatement records
    fs_records = {fs.name: fs for fs in FinancialStatement.objects.all()}

    # Update all Ledger records
    for ledger in Ledger.objects.all():
        old_choice = ledger.financial_statement_temp  # Get from temp field
        if old_choice in choice_mapping:
            fs_name = choice_mapping[old_choice]
            if fs_name in fs_records:
                ledger.financial_statement_new = fs_records[fs_name]
                ledger.save()


def reverse_migrate_financial_statement_fk_to_choices(apps, schema_editor):
    """Reverse migration: convert ForeignKey back to choices."""
    Ledger = apps.get_model("Ledger", "Ledger")

    # Map the FinancialStatement names back to choices
    reverse_mapping = {
        "Balance Sheet": "balance_sheet",
        "Income Statement": "income_statement",
        "Cash Flow Statement": "cash_flow_statement",
        "Statement of Changes in Equity": "statement_of_changes_in_equity",
    }

    # Update all Ledger records
    for ledger in Ledger.objects.all():
        if ledger.financial_statement_new:
            fs_name = ledger.financial_statement_new.name
            if fs_name in reverse_mapping:
                ledger.financial_statement_temp = reverse_mapping[fs_name]
                ledger.save()


class Migration(migrations.Migration):
    dependencies = [
        ("Ledger", "0008_financialstatement"),
    ]

    operations = [
        # Step 1: Create new temporary field for the new ForeignKey
        migrations.AddField(
            model_name="ledger",
            name="financial_statement_new",
            field=models.ForeignKey(
                to="Ledger.FinancialStatement",
                on_delete=models.PROTECT,
                null=True,
                blank=True,
                default=None,
                related_name="ledgers_new",
            ),
        ),
        # Step 2: Create temporary field to hold old choices data
        migrations.AddField(
            model_name="ledger",
            name="financial_statement_temp",
            field=models.CharField(
                max_length=35,
                choices=[
                    ("balance_sheet", "Balance Sheet"),
                    ("income_statement", "Income Statement"),
                    ("cash_flow_statement", "Cash Flow Statement"),
                    (
                        "statement_of_changes_in_equity",
                        "Statement of Changes in Equity",
                    ),
                ],
                default="balance_sheet",
            ),
        ),
        # Step 3: Copy data from original field to temp field
        migrations.RunPython(
            migrate_choices_to_temp,
            reverse_code=migrations.RunPython.noop,
        ),
        # Step 4: Populate new ForeignKey field based on choices
        migrations.RunPython(
            migrate_financial_statement_choices_to_fk,
            reverse_code=reverse_migrate_financial_statement_fk_to_choices,
        ),
        # Step 5: Make the new field required (remove null=True)
        migrations.AlterField(
            model_name="ledger",
            name="financial_statement_new",
            field=models.ForeignKey(
                on_delete=models.PROTECT,
                related_name="ledgers",
                to="Ledger.financialstatement",
            ),
        ),
        # Step 6: Delete the old choices field
        migrations.RemoveField(
            model_name="ledger",
            name="financial_statement",
        ),
        # Step 7: Delete the temp field
        migrations.RemoveField(
            model_name="ledger",
            name="financial_statement_temp",
        ),
        # Step 8: Rename the new field to the original name
        migrations.RenameField(
            model_name="ledger",
            old_name="financial_statement_new",
            new_name="financial_statement",
        ),
        migrations.AlterModelOptions(
            name="ledger",
            options={
                "ordering": ["financial_statement__name", "code", "name"],
                "verbose_name": "Ledger",
                "verbose_name_plural": "Ledgers",
            },
        ),
    ]
