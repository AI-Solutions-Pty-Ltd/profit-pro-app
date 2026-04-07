from django.db import models

from app.core.Utilities.models import BaseModel
from app.Project.projects.projects_models import Project


class JournalEntry(BaseModel):
    """
    General ledger for all financial transactions related to a project.
    Entries can be associated with site management daily logs.
    """

    class EntryType(models.TextChoices):
        DEBIT = "DEBIT", "Debit"
        CREDIT = "CREDIT", "Credit"

    class Category(models.TextChoices):
        MATERIAL = "MATERIAL", "Material"
        LABOUR = "LABOUR", "Labour"
        SUBCONTRACTOR = "SUBCONTRACTOR", "Subcontractor"
        OVERHEAD = "OVERHEAD", "Overhead"
        PLANT = "PLANT", "Plant"
        OTHER = "OTHER", "Other"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="journal_entries",
        help_text="Project this journal entry belongs to",
    )
    date = models.DateField(help_text="Transaction date")
    category = models.CharField(
        max_length=50, choices=Category.choices, help_text="Category of transaction"
    )
    description = models.CharField(
        max_length=255, help_text="Description of transaction"
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Total amount"
    )
    transaction_type = models.CharField(
        max_length=10, choices=EntryType.choices, default=EntryType.DEBIT
    )
    # Generic linkage to source logs if needed
    source_log_id = models.PositiveIntegerField(
        null=True, blank=True, help_text="ID of the source log (Daily Diary, etc.)"
    )
    source_log_type = models.CharField(
        max_length=100, blank=True, help_text="Type of the source daily log"
    )

    def __str__(self):
        return f"{self.date} - {self.category} - {self.amount}"

    class Meta:
        verbose_name = "Journal Entry"
        verbose_name_plural = "Journal Entries"
        ordering = ["-date", "-created_at"]
