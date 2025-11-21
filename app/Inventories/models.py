from django.db import models

from .models_suppliers import Supplier, Transaction


def quote_upload_path(instance, filename):
    """Generate upload path for quote files."""
    return f"quotes/{instance.pk}/{filename}"


def delivery_note_upload_path(instance, filename):
    """Generate upload path for delivery note files."""
    return f"delivery_notes/{instance.pk}/{filename}"


class Note(models.Model):
    description = models.CharField(blank=False, null=False, max_length=240)

    def __str__(self):
        return self.description


class Type(models.Model):
    description = models.CharField(blank=False, null=False, max_length=240)

    def __str__(self):
        return self.description


class Inventory(models.Model):
    description = models.CharField(blank=False, null=False, max_length=240)
    type = models.ForeignKey(Type, on_delete=models.SET_NULL, blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.description


class Warehouse(models.Model):
    description = models.CharField(blank=False, null=False, max_length=240)

    def __str__(self):
        return self.description


class VAT(models.Model):
    description = models.CharField(blank=False, null=False, max_length=240)
    percentage = models.DecimalField(
        blank=False, null=False, decimal_places=2, max_digits=3
    )

    def __str__(self):
        return self.description


class OrderComposition(models.Model):
    inventory = models.ForeignKey(Inventory, on_delete=models.SET_NULL, null=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)
    vat = models.ForeignKey(VAT, on_delete=models.SET_NULL, blank=True, null=True)

    qty_ordered = models.DecimalField(
        blank=False, null=False, decimal_places=3, max_digits=10
    )
    qty_delivered = models.DecimalField(
        blank=True, null=True, decimal_places=3, max_digits=10
    )
    qty_returned = models.DecimalField(
        blank=True, null=True, decimal_places=3, max_digits=10
    )

    price_excl = models.DecimalField(
        blank=False, null=False, decimal_places=3, max_digits=10
    )
    price_incl = models.DecimalField(
        blank=False, null=False, decimal_places=3, max_digits=10
    )

    def __str__(self):
        return f"{self.inventory} - {self.qty_ordered}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        DELIVERED = "Delivered", "Delivered"
        RETURNED = "Returned", "Returned"
        COMPLETED = "Completed", "Completed"

    date = models.DateTimeField(blank=False, null=False)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, blank=True, null=True
    )
    order = models.ManyToManyField(OrderComposition)
    status = models.CharField(
        choices=Status.choices, default=Status.PENDING, max_length=20, blank=True
    )
    note = models.ManyToManyField(Note)
    quote = models.FileField(
        upload_to=quote_upload_path,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.supplier} - {self.date}"


class InventoryTransaction(models.Model):
    class Type(models.TextChoices):
        IN = "In", "In"
        OUT = "Out", "Out"

    date = models.DateTimeField(blank=False, null=False)
    type = models.CharField(
        choices=Type.choices, default=Type.IN, max_length=20, blank=True
    )
    inventory = models.ForeignKey(
        Inventory, on_delete=models.SET_NULL, blank=True, null=True
    )
    qty = models.DecimalField(blank=False, null=False, decimal_places=3, max_digits=10)
    price_excl = models.DecimalField(
        blank=False, null=False, decimal_places=3, max_digits=10
    )
    price_incl = models.DecimalField(
        blank=False, null=False, decimal_places=3, max_digits=10
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, blank=True, null=True
    )
    order_composition = models.ForeignKey(
        OrderComposition, on_delete=models.SET_NULL, blank=True, null=True
    )
    supplier_invoice = models.OneToOneField(
        Transaction, on_delete=models.SET_NULL, blank=True, null=True
    )

    delivery_note = models.FileField(
        upload_to=delivery_note_upload_path,
        blank=True,
        null=True,
    )
    bookings = models.ManyToManyField("InventoryTransaction")

    def __str__(self):
        return f"{self.inventory} - {self.qty}"
