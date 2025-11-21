from datetime import datetime

from django import forms
from django.forms import modelformset_factory

from .models import (
    Inventory,
    InventoryTransaction,
    Order,
    OrderComposition,
    Type,
    Warehouse,
)
from .models_suppliers import (
    Supplier,
)


class DateInput(forms.DateInput):
    input_type = "date"


class WarehouseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Warehouse
        fields = "__all__"


class CompositionFilterForm(forms.Form):
    purchase_order = forms.CharField()
    inventory = forms.CharField()
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all())
    status = forms.ChoiceField(choices=Order.Status.choices)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["purchase_order"].required = False
        self.fields["supplier"].required = False
        self.fields["status"].required = False
        self.fields["inventory"].required = False


class DeliveryFilterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["inventory"].queryset = Inventory.objects.filter(
            active=True
        ).order_by("description")

        self.fields["purchase_order"].required = False
        self.fields["supplier"].required = False
        self.fields["inventory"].required = False

    class Meta:
        model = OrderComposition

        fields = {
            "purchase_order",
            "supplier",
            "inventory",
        }

    purchase_order = forms.CharField()
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all())


class AddOrderLineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["inventory"].required = True
        self.fields["inventory"].widget.attrs["onchange"] = "findTotal(0);"
        self.fields["warehouse"].required = True
        self.fields["qty_ordered"].required = True
        self.fields["price_excl"].required = True
        self.fields["price_excl"].widget.attrs["onchange"] = "findTotal(1);"
        self.fields["price_incl"].required = True
        self.fields["price_incl"].widget.attrs["onchange"] = "findTotal(2);"
        self.fields["vat"].empty_label = None
        self.fields["vat"].widget.attrs["onchange"] = "findTotal(0);"
        self.fields["qty_ordered"].initial = 1
        self.fields["qty_ordered"].widget.attrs["onchange"] = "findTotal(0);"
        self.fields["inventory"].queryset = (
            Inventory.objects.filter(active=True)
            .order_by("description")
            .select_related("type")
        )
        self.fields["inventory"].label_from_instance = (
            lambda obj: f"{obj.description}: {obj.type.description}"
        )

    class Meta:
        model = OrderComposition
        exclude = ("qty_delivered", "qty_returned")


AddOrderLineFormSet = modelformset_factory(
    OrderComposition, form=AddOrderLineForm, extra=1
)

UpdateOrderLineFormSet = modelformset_factory(
    OrderComposition, form=AddOrderLineForm, extra=0
)


class DeliverOrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["qty_delivered"].required = True
        self.fields["qty_returned"].required = True

        self.fields["qty_returned"].widget.attrs["onchange"] = "findTotal(0);"
        self.fields["qty_delivered"].widget.attrs["onchange"] = "findTotal(0);"

        self.fields["qty_returned"].widget.attrs["step"] = "1"
        self.fields["qty_delivered"].widget.attrs["step"] = "1"

    class Meta:
        model = OrderComposition

        exclude = (
            "inventory",
            "warehouse",
            "vat",
            "qty_ordered",
            "price_excl",
            "price_incl",
        )


DeliverOrderFormSet = modelformset_factory(
    OrderComposition, form=DeliverOrderForm, extra=0
)


class CreateOrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].initial = datetime.now()
        self.fields["supplier"].required = True
        self.fields["supplier"].queryset = Supplier.objects.filter(
            active=True
        ).order_by("description")
        self.fields["date"].required = True

    class Meta:
        model = Order

        widgets = {
            "date": DateInput(),
        }
        exclude = ("note", "status", "order", "quote")


class DeliveryNoteUploadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["delivery_note"].required = True

    class Meta:
        model = InventoryTransaction
        fields = [
            "delivery_note",
        ]


class QuoteUploadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quote"].required = True

    class Meta:
        model = Order
        fields = [
            "quote",
        ]


class InventoryFilterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["description"].required = False
        self.fields["warehouse"].required = False
        self.fields["type"].required = False

    class Meta:
        model = InventoryTransaction

        fields = {
            "description",
            "warehouse",
            "type",
        }

    description = forms.CharField()
    type = forms.ModelChoiceField(queryset=Type.objects.all())


class InventoryCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"].required = True
        self.fields["type"].required = True

    class Meta:
        model = Inventory

        fields = "__all__"


class InventoryMovementForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["date"].required = True
        self.fields["inventory"].required = True
        self.fields["inventory"].queryset = (
            Inventory.objects.filter(active=True)
            .order_by("description")
            .select_related("type")
        )
        self.fields["warehouse"].required = True
        self.fields["to_warehouse"].required = False
        self.fields["type"].required = True
        self.fields["type"].choices = InventoryTransaction.Type.choices
        self.fields["qty"].required = True
        self.fields["date"].initial = datetime.now()
        self.fields["inventory"].label_from_instance = (
            lambda obj: f"{obj.description}: {obj.type.description}"
        )

    class Meta:
        model = InventoryTransaction
        widgets = {
            "date": DateInput(),
        }
        fields = {
            "date",
            "inventory",
            "warehouse",
            "to_warehouse",
            "type",
            "qty",
        }

    to_warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all())


class InventoryTransactionFilterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["des_inventory"].required = False
        self.fields["warehouse"].required = False
        self.fields["inv_type"].required = False
        self.fields["tx_type"].required = False
        self.fields["purchase_order"].required = False

    class Meta:
        model = InventoryTransaction

        fields = {
            "des_inventory",
            "warehouse",
            "inv_type",
            "tx_type",
            "purchase_order",
        }

    purchase_order = forms.CharField()
    des_inventory = forms.CharField()
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all())
    inv_type = forms.ModelChoiceField(queryset=Type.objects.all())
    tx_type = forms.ChoiceField(choices=InventoryTransaction.Type.choices)


class InventoryTxEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["date"].required = True
        self.fields["inventory"].required = True
        self.fields["warehouse"].required = True
        self.fields["type"].required = True
        self.fields["qty"].required = True
        self.fields["price_excl"].required = True
        self.fields["price_incl"].required = True

        self.fields["date"].initial = datetime.now()
        self.fields["inventory"].queryset = (
            Inventory.objects.filter(active=True)
            .order_by("description")
            .select_related("type")
        )
        self.fields["inventory"].label_from_instance = (
            lambda obj: f"{obj.description}: {obj.type.description}"
        )

    class Meta:
        model = InventoryTransaction
        widgets = {
            "date": DateInput(),
        }
        fields = (
            "date",
            "type",
            "inventory",
            "qty",
            "warehouse",
            "price_excl",
            "price_incl",
        )


class OrderFilterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["purchase_order"].required = False

    class Meta:
        model = Order

        fields = {
            "purchase_order",
        }

    purchase_order = forms.CharField()
