from datetime import datetime

from django.contrib import messages
from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from app.core.Utilities.permissions import permitted_groups
from app.Inventories.apps import ObjectMixin
from app.Inventories.models import (
    Inventory,
    InventoryTransaction,
    Order,
    OrderComposition,
    Warehouse,
)

from .forms import (
    InventoryCreateForm,
    InventoryFilterForm,
    InventoryMovementForm,
    InventoryTransactionFilterForm,
    InventoryTxEditForm,
    WarehouseForm,
)


def inventory_fifo_tx(inventory, warehouse, qty_requested):
    queryset = InventoryTransaction.objects.filter(
        inventory=inventory, warehouse=warehouse
    ).order_by("date")

    queryset = queryset.annotate(
        sum=Coalesce(
            Sum("bookings__qty") + F("qty"), F("qty"), output_field=models.FloatField()
        )
    ).filter(sum__gt=0)
    # i now have all positive deliveries and stock booked out against that entry

    # now to check how much is left versus what is being adjusted

    for instance in queryset:
        if qty_requested <= instance.sum:  # type: ignore
            return instance, qty_requested

        elif qty_requested > instance.sum:  # type: ignore
            return instance, instance.sum  # type: ignore
    return None, float(0)


class WarehouseListView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Inventories/Warehouses/warehouse_list.html"
        self.context = ObjectMixin.get_default_context("Warehouses")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        form_warehouse = WarehouseForm(initial={"date": datetime.now()})

        self.context["queryset"] = Warehouse.objects.all()
        self.context["form_warehouse"] = form_warehouse
        return render(request, self.template_name, self.context)

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def post(self, request, *args, **kwargs):
        if "create warehouse" in request.POST:
            form_warehouse = WarehouseForm(request.POST)
            if form_warehouse.is_valid():
                form_warehouse.save()
                return redirect("inventories:warehouse_list_view")
        else:
            for key in request.POST.keys():
                if key.startswith("edit warehouse"):
                    warehouse_id = key[14:]
                    instance = get_object_or_404(Warehouse, id=warehouse_id)

                    form_warehouse = WarehouseForm(request.POST, instance=instance)
                    if form_warehouse.is_valid():
                        form_warehouse.save()
                        return redirect("inventories:warehouse_list_view")

        form_warehouse = WarehouseForm(request.POST)
        self.context["queryset"] = Warehouse.objects.all()
        self.context["form_warehouse"] = form_warehouse
        return render(request, self.template_name, self.context)


class InventoryListView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Inventories/Warehouses/inventory_list.html"
        self.context = ObjectMixin.get_default_context("Inventory List")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        queryset = Inventory.objects.all().order_by("type__description", "description")
        queryset = queryset.select_related()
        queryset = queryset.values(
            "id",
            "description",
            "type__description",
            "inventorytransaction__warehouse__description",
            "active",
        )
        queryset = queryset.annotate(sum=Sum("inventorytransaction__qty"))
        # queryset = None
        form = InventoryCreateForm()
        form_filter = InventoryFilterForm()
        form_movement = InventoryMovementForm(
            initial={"qty": 10, "warehouse": 1, "inventory": 543, "type": 5}
        )

        self.context["form"] = form
        self.context["form_filter"] = form_filter
        self.context["form_movement"] = form_movement

        self.context["object"] = object
        self.context["queryset"] = queryset
        return render(request, self.template_name, self.context)

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def post(self, request, *args, **kwargs):
        if "filter" in request.POST:
            form_filter = InventoryFilterForm(request.POST)

            queryset = Inventory.objects.all().order_by(
                "type__description", "description"
            )

            queryset = Inventory.objects.all().order_by(
                "type__description", "description"
            )
            queryset = queryset.select_related("type")
            queryset = queryset.select_related("inventorytransaction")
            queryset = queryset.select_related("inventorytransaction__warehouse")

            if form_filter["description"].value():
                queryset = queryset.filter(
                    description__icontains=form_filter["description"].value()
                )
            if form_filter["warehouse"].value():
                queryset = queryset.filter(
                    inventorytransaction__warehouse__id=form_filter["warehouse"].value()
                )
            if form_filter["type"].value():
                queryset = queryset.filter(type_id=form_filter["type"].value())

            queryset = queryset.values(
                "id",
                "description",
                "type__description",
                "inventorytransaction__warehouse__description",
                "active",
            )
            queryset = queryset.annotate(sum=Sum("inventorytransaction__qty"))

            form = InventoryCreateForm()
            form_movement = InventoryMovementForm()

            self.context["form"] = form
            self.context["form_filter"] = form_filter
            self.context["form_movement"] = form_movement

            self.context["object"] = object
            self.context["queryset"] = queryset
            return render(request, self.template_name, self.context)

        elif "create inventory" in request.POST:
            form = InventoryCreateForm(request.POST)
            if form.is_valid():
                form.save()

        elif "create transaction" in request.POST:
            form = InventoryMovementForm(request.POST)
            if form.is_valid():
                inv_tx = form.save(commit=False)
                total_qty = float(inv_tx.qty)
                if total_qty < 0:
                    total_qty = -total_qty  # absolute

                if inv_tx.type_id == 3:  # transfer
                    if (
                        float(request.POST.get("to_warehouse")) != inv_tx.warehouse_id
                        and total_qty > 0
                    ):
                        while total_qty > 0:
                            start = total_qty
                            inv_obj, qty_final = inventory_fifo_tx(
                                inv_tx.inventory, inv_tx.warehouse, total_qty
                            )

                            debit_tx = InventoryTransaction(
                                date=inv_tx.date,
                                type=inv_tx.type,
                                inventory=inv_tx.inventory,
                                qty=-qty_final,
                                warehouse=inv_tx.warehouse,
                                price_excl=0,
                                price_incl=0,
                            )

                            credit_tx = InventoryTransaction(
                                date=inv_tx.date,
                                type=inv_tx.type,
                                inventory=inv_tx.inventory,
                                qty=qty_final,
                                warehouse_id=float(request.POST.get("to_warehouse")),
                                price_excl=0,
                                price_incl=0,
                            )

                            if inv_obj:
                                debit_tx.price_excl = inv_obj.price_excl
                                debit_tx.price_incl = inv_obj.price_incl
                                credit_tx.price_excl = inv_obj.price_excl
                                credit_tx.price_incl = inv_obj.price_incl
                            else:
                                try:
                                    tx = InventoryTransaction.objects.filter(
                                        inventory=inv_tx.inventory
                                    ).latest("date")
                                except Exception as _:
                                    tx = None
                                if tx:
                                    debit_tx.price_excl = tx.price_excl
                                    debit_tx.price_incl = tx.price_incl
                                    credit_tx.price_excl = tx.price_excl
                                    credit_tx.price_incl = tx.price_incl

                            if qty_final <= 0:
                                debit_tx.qty = -total_qty
                                credit_tx.qty = total_qty
                                total_qty = 0
                            else:
                                total_qty = total_qty - qty_final

                            debit_tx.save()
                            credit_tx.save()

                            if inv_obj:
                                inv_obj.bookings.add(debit_tx)
                                inv_obj.save()

                            if start == total_qty:
                                messages.error(
                                    request, "Could not complete transaction"
                                )
                                total_qty = 0
                    else:
                        if inv_tx.qty < 0:
                            messages.error(request, "Please enter Positive Qty")
                        else:
                            messages.error(
                                request, "Please choose a different warehouse"
                            )

                elif inv_tx.type_id == 2:  # in
                    try:
                        tx = InventoryTransaction.objects.filter(
                            inventory=inv_tx.inventory
                        ).latest("date")
                    except Exception as _:
                        tx = None

                    inv_tx = InventoryTransaction(
                        date=inv_tx.date,
                        type=inv_tx.type,
                        inventory=inv_tx.inventory,
                        qty=total_qty,
                        warehouse=inv_tx.warehouse,
                        price_excl=0,
                        price_incl=0,
                    )
                    if tx:
                        inv_tx.price_excl = tx.price_excl
                        inv_tx.price_incl = tx.price_incl
                    inv_tx.save()
                    messages.success(request, "Inventory increased")

                elif inv_tx.type_id == 5:  # out
                    while total_qty > 0:
                        start = total_qty
                        inv_obj = None
                        qty_final = 0.0

                        inv_obj, qty_final = inventory_fifo_tx(
                            inv_tx.inventory, inv_tx.warehouse, total_qty
                        )

                        total_qty = total_qty - float(qty_final)

                        inv_tx = InventoryTransaction(
                            date=inv_tx.date,
                            type=inv_tx.type,
                            inventory=inv_tx.inventory,
                            qty=-qty_final,
                            warehouse=inv_tx.warehouse,
                            price_excl=0,
                            price_incl=0,
                        )

                        inv_tx.save()

                        if inv_obj and qty_final > 0:
                            inv_tx.price_excl = inv_obj.price_excl
                            inv_tx.price_incl = inv_obj.price_incl
                            inv_tx.save()
                            inv_obj.bookings.add(inv_tx)
                            inv_obj.save()
                        else:
                            queryset = InventoryTransaction.objects.filter(
                                inventory=inv_tx.inventory
                            ).order_by("-date")
                            if queryset:
                                for instance in InventoryTransaction.objects.filter(
                                    inventory=inv_tx.inventory
                                ).order_by("-date"):
                                    if instance.qty > 0:
                                        inv_tx.price_excl = instance.price_excl
                                        inv_tx.price_incl = instance.price_incl
                                        inv_tx.qty = -total_qty
                                        inv_tx.save()
                                        total_qty = 0
                                        break
                            else:
                                inv_tx.qty = -total_qty
                                inv_tx.save()
                                total_qty = 0
                        if start == total_qty:
                            messages.error(request, "Could not complete transaction")
                            total_qty = 0

        else:
            for key in request.POST.keys():
                if key.startswith("edit inventory"):
                    inv_id = key[14:]
                    instance = get_object_or_404(Inventory, id=inv_id)

                    form = InventoryCreateForm(request.POST, instance=instance)
                    if form.is_valid():
                        form.save()
                        messages.success(request, "Inventory Item updated")
                        return redirect("inventories:inventory_list_view")
                    else:
                        messages.error(request, "Update Inventory Failed")
        return redirect("inventories:inventory_list_view")


class InventoryCreateView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Inventories/Warehouses/inventory_create.html"
        self.context = ObjectMixin.get_default_context("Create Inventory")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        form = InventoryCreateForm()
        self.context["form"] = form
        return render(request, self.template_name, self.context)

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def post(self, request, *args, **kwargs):
        if "create inventory" in request.POST:
            form = InventoryCreateForm(request.POST)
            if form.is_valid():
                form.save()
        return redirect("inventories:inventory_list_view")


class InventoryTransactionListView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Inventories/Warehouses/inventory_tx_list.html"
        self.context = ObjectMixin.get_default_context("Inventory Transaction List")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        queryset = InventoryTransaction.objects.all()
        queryset = queryset.select_related("inventory")
        queryset = queryset.select_related("inventory__type")
        queryset = queryset.select_related("warehouse")

        form_filter = InventoryTransactionFilterForm()

        form = InventoryCreateForm()
        form_movement = InventoryMovementForm()
        form_tx = InventoryTxEditForm()

        self.context["queryset"] = queryset
        self.context["form"] = form
        self.context["form_tx"] = form_tx
        self.context["form_filter"] = form_filter
        self.context["form_movement"] = form_movement
        return render(request, self.template_name, self.context)

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def post(self, request, *args, **kwargs):
        queryset = InventoryTransaction.objects.all()
        queryset = queryset.select_related("type")
        queryset = queryset.select_related("inventory")
        queryset = queryset.select_related("inventory__type")
        queryset = queryset.select_related("warehouse")

        form_filter = InventoryTransactionFilterForm()
        form = InventoryCreateForm()
        form_movement = InventoryMovementForm()
        form_tx = InventoryTxEditForm()

        if "filter" in request.POST:
            input_inv = request.POST.get("des_inventory")
            input_warehouse = request.POST.get("warehouse")
            input_tx_type = request.POST.get("tx_type")
            input_inv_type = request.POST.get("inv_type")
            input_po = request.POST.get("purchase_order")

            if input_inv:
                queryset = queryset.filter(inventory__description__icontains=input_inv)
            if input_warehouse:
                queryset = queryset.filter(warehouse=input_warehouse)
            if input_tx_type:
                queryset = queryset.filter(type=input_tx_type)
            if input_inv_type:
                queryset = queryset.filter(inventory__type=input_inv_type)
            if input_po:
                queryset = queryset.filter(
                    ordercomposition__order__id__icontains=input_po
                )

            form_filter = InventoryTransactionFilterForm(request.POST)

            form = InventoryCreateForm()
            form_movement = InventoryMovementForm()

            self.context["queryset"] = queryset
            self.context["form"] = form
            self.context["form_tx"] = form_tx
            self.context["form_filter"] = form_filter
            self.context["form_movement"] = form_movement
            return render(request, self.template_name, self.context)

        elif "create inventory" in request.POST:
            form = InventoryCreateForm(request.POST)
            if form.is_valid():
                form.save()

        elif "create transaction" in request.POST:
            form = InventoryMovementForm(request.POST)
            if form.is_valid():
                inv_tx = form.save(commit=False)
                total_qty = float(inv_tx.qty)
                if total_qty < 0:
                    total_qty = -total_qty  # absolute

                if inv_tx.type_id == 3:  # transfer
                    if (
                        float(request.POST.get("to_warehouse")) != inv_tx.warehouse_id
                        and total_qty > 0
                    ):
                        while total_qty > 0:
                            start = total_qty
                            inv_obj, qty_final = inventory_fifo_tx(
                                inv_tx.inventory, inv_tx.warehouse, total_qty
                            )

                            debit_tx = InventoryTransaction(
                                date=inv_tx.date,
                                type=inv_tx.type,
                                inventory=inv_tx.inventory,
                                qty=-qty_final,
                                warehouse=inv_tx.warehouse,
                                price_excl=0,
                                price_incl=0,
                            )

                            credit_tx = InventoryTransaction(
                                date=inv_tx.date,
                                type=inv_tx.type,
                                inventory=inv_tx.inventory,
                                qty=qty_final,
                                warehouse_id=float(request.POST.get("to_warehouse")),
                                price_excl=0,
                                price_incl=0,
                            )

                            if inv_obj:
                                debit_tx.price_excl = inv_obj.price_excl
                                debit_tx.price_incl = inv_obj.price_incl
                                credit_tx.price_excl = inv_obj.price_excl
                                credit_tx.price_incl = inv_obj.price_incl
                            else:
                                try:
                                    tx = InventoryTransaction.objects.filter(
                                        inventory=inv_tx.inventory
                                    ).latest("date")
                                except Exception as _:
                                    tx = None
                                if tx:
                                    debit_tx.price_excl = tx.price_excl
                                    debit_tx.price_incl = tx.price_incl
                                    credit_tx.price_excl = tx.price_excl
                                    credit_tx.price_incl = tx.price_incl

                            if qty_final <= 0:
                                debit_tx.qty = -total_qty
                                credit_tx.qty = total_qty
                                total_qty = 0
                            else:
                                total_qty = total_qty - qty_final

                            debit_tx.save()
                            credit_tx.save()

                            if inv_obj:
                                inv_obj.bookings.add(debit_tx)
                                inv_obj.save()

                            if start == total_qty:
                                messages.error(
                                    request, "Could not complete transaction"
                                )
                                total_qty = 0
                    else:
                        if inv_tx.qty < 0:
                            messages.error(request, "Please enter Positive Qty")
                        else:
                            messages.error(
                                request, "Please choose a different warehouse"
                            )

                elif inv_tx.type_id == 2:  # in
                    try:
                        tx = InventoryTransaction.objects.filter(
                            inventory=inv_tx.inventory
                        ).latest("date")
                    except Exception as _:
                        tx = None

                    inv_tx = InventoryTransaction(
                        date=inv_tx.date,
                        type=inv_tx.type,
                        inventory=inv_tx.inventory,
                        qty=total_qty,
                        warehouse=inv_tx.warehouse,
                        price_excl=0,
                        price_incl=0,
                    )
                    if tx:
                        inv_tx.price_excl = tx.price_excl
                        inv_tx.price_incl = tx.price_incl
                    inv_tx.save()
                    messages.success(request, "Inventory increased")

                elif inv_tx.type_id == 5:  # out
                    while total_qty > 0:
                        start = total_qty
                        inv_obj = None
                        qty_final = 0.0

                        inv_obj, qty_final = inventory_fifo_tx(
                            inv_tx.inventory, inv_tx.warehouse, total_qty
                        )

                        total_qty = total_qty - float(qty_final)

                        inv_tx = InventoryTransaction(
                            date=inv_tx.date,
                            type=inv_tx.type,
                            inventory=inv_tx.inventory,
                            qty=-qty_final,
                            warehouse=inv_tx.warehouse,
                            price_excl=0,
                            price_incl=0,
                        )

                        inv_tx.save()

                        if inv_obj and qty_final > 0:
                            inv_tx.price_excl = inv_obj.price_excl
                            inv_tx.price_incl = inv_obj.price_incl
                            inv_tx.save()
                            inv_obj.bookings.add(inv_tx)
                            inv_obj.save()
                        else:
                            queryset = InventoryTransaction.objects.filter(
                                inventory=inv_tx.inventory
                            ).order_by("-date")
                            if queryset:
                                for instance in InventoryTransaction.objects.filter(
                                    inventory=inv_tx.inventory
                                ).order_by("-date"):
                                    if instance.qty > 0:
                                        inv_tx.price_excl = instance.price_excl
                                        inv_tx.price_incl = instance.price_incl
                                        inv_tx.qty = -total_qty
                                        inv_tx.save()
                                        total_qty = 0
                                        break
                            else:
                                inv_tx.qty = -total_qty
                                inv_tx.save()
                                total_qty = 0
                        if start == total_qty:
                            messages.error(request, "Could not complete transaction")
                            total_qty = 0

        else:
            for key in request.POST.keys():
                if key.startswith("edit inventory"):
                    inventory_transaction_id = key[14:]
                    instance = get_object_or_404(
                        InventoryTransaction, id=inventory_transaction_id
                    )
                    qty_diff = instance.qty
                    form = InventoryTxEditForm(request.POST, instance=instance)
                    if form.is_valid():
                        form = form.save(commit=False)
                        qty_diff = form.qty - qty_diff

                        try:
                            order_comp = OrderComposition.objects.get(
                                inventorytransaction=instance
                            )
                            order_comp.qty_delivered = float(
                                order_comp.qty_delivered
                            ) + float(qty_diff)
                            order_comp.save()
                            order = get_object_or_404(Order, order=order_comp)
                            order.status = Order.Status.DELIVERED
                            order.save()
                        except Exception as _:
                            pass

                        form.save()
                        messages.success(request, "Inventory Item updated")
                    else:
                        messages.error(request, "Update Inventory Failed")

                if key.startswith("delete inventory"):
                    inventory_transaction_id = key[16:]
                    instance = get_object_or_404(
                        InventoryTransaction, id=inventory_transaction_id
                    )
                    try:
                        order_comp = OrderComposition.objects.get(
                            inventorytransaction=instance
                        )
                        order_comp.qty_delivered = float(
                            order_comp.qty_delivered
                        ) - float(instance.qty)
                        order_comp.save()
                        order = get_object_or_404(Order, order=order_comp)
                        order.status = Order.Status.DELIVERED
                        order.save()
                    except Exception as _:
                        pass

                    try:
                        instance.delete()
                        messages.success(request, "Inventory Tx Delete")
                    except Exception as _:
                        messages.error(request, "Inventory Tx Delete Failed")

        return redirect("inventories:inventory_tx_list_view")
