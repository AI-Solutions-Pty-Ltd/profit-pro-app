import mimetypes
import os
from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.db import models
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from app.core.Utilities.permissions import permitted_groups
from app.Inventories.forms import (
    AddOrderLineFormSet,
    CompositionFilterForm,
    CreateOrderForm,
    DeliverOrderFormSet,
    DeliveryFilterForm,
    DeliveryNoteUploadForm,
    OrderFilterForm,
    QuoteUploadForm,
    UpdateOrderLineFormSet,
)
from app.Inventories.models import (
    Inventory,
    InventoryTransaction,
    Order,
    OrderComposition,
    Transaction,
)
from app.Inventories.models_suppliers import Invoice

from .apps import ObjectMixin


class OrderPlaceView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Inventories/Orders/order_place.html"
        self.context = ObjectMixin.get_default_context("Order Inventory")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        form_order = CreateOrderForm()
        formset_add_order_line = AddOrderLineFormSet(queryset=Inventory.objects.none())

        self.context["form_order"] = form_order
        self.context["formset_addorderline"] = formset_add_order_line

        return render(request, self.template_name, self.context)

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def post(self, request, *args, **kwargs):
        form_order = CreateOrderForm(request.POST)
        formset_addorderline = AddOrderLineFormSet(request.POST)

        if "create order" in request.POST:
            if form_order.is_valid():
                order = form_order.save(commit=False)
                order.status_id = 1
                for form in formset_addorderline:
                    order_inventory = OrderComposition(
                        inventory_id=form["inventory"].value(),
                        warehouse_id=form["warehouse"].value(),
                        qty_ordered=form["qty_ordered"].value(),
                        qty_delivered=0,
                        qty_returned=0,
                        vat_id=form["vat"].value(),
                        price_excl=form["price_excl"].value(),
                        price_incl=form["price_incl"].value(),
                    )
                    order_inventory.save()
                    order.save()
                    order.order.add(order_inventory)
                    order.save()

                messages.success(request, "Order placed")

                return redirect("inventories:order_composition_view", order=order.id)
            else:
                messages.error(request, "order form faulty")

        self.context["form_order"] = form_order
        self.context["formset_addorderline"] = formset_addorderline

        return render(request, self.template_name, self.context)


class OrderDetailView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Inventories/Orders/order_composition.html"
        self.context = ObjectMixin.get_default_context("Order Detail")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        order_id = self.kwargs.get("order")

        order = get_object_or_404(Order, id=order_id)
        order_composition = OrderComposition.objects.filter(order=order)
        order_composition = order_composition.extra(
            select={"total_incl": "price_incl * qty_ordered"}
        )
        order_composition = order_composition.extra(
            select={"total_excl": "price_excl * qty_ordered"}
        )

        total_incl = 0
        total_excl = 0
        total_vat = 0
        for instance in order_composition:
            total_incl += instance.total_incl
            total_excl += instance.total_excl
            total_vat += instance.total_incl - instance.total_excl

        self.context["order"] = order
        self.context["total_incl"] = total_incl
        self.context["total_excl"] = total_excl
        self.context["total_vat"] = total_vat
        self.context["order_composition"] = order_composition
        return render(request, self.template_name, self.context)

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def post(self, request, *args, **kwargs):
        order_id = self.kwargs.get("order")

        order = get_object_or_404(Order, id=order_id)
        if "approve order" in request.POST:
            if order.status == Order.Status.PENDING:
                order.status = Order.Status.DELIVERED
                order.save()
                messages.success(request, "Order Approved")
            else:
                messages.error(request, "Order already approved")
        elif "revoke order" in request.POST:
            if order.status == Order.Status.DELIVERED:
                order.status = Order.Status.PENDING
                order.save()
                messages.success(request, "Order Revoked")
            else:
                messages.error(request, "Not updated")

        return redirect("inventories:order_list_view")


class OrderUpdateView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Inventories/Orders/order_update.html"
        self.context = ObjectMixin.get_default_context("Update Order")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        order_id = self.kwargs.get("order")

        order = get_object_or_404(Order, id=order_id)
        order_composition = OrderComposition.objects.filter(order=order)

        form_order = CreateOrderForm(instance=order)
        update_order_line_formset = UpdateOrderLineFormSet(queryset=order.order.all())

        self.context["form_order"] = form_order
        self.context["updateorderlineformset"] = update_order_line_formset
        self.context["order"] = order
        self.context["order_composition"] = order_composition
        return render(request, self.template_name, self.context)

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get("order")

        order = get_object_or_404(Order, id=pk)
        order_composition = OrderComposition.objects.filter(order=order)
        composition_tx = InventoryTransaction.objects.filter(
            ordercomposition__order__pk=order.pk
        )
        tx_supplier_invoice = Invoice.objects.filter(order=order)
        supplier_invoice_tx = Transaction.objects.filter(invoice__order=order)

        form_order = CreateOrderForm(request.POST, instance=order)
        update_order_line_formset = UpdateOrderLineFormSet(
            request.POST, queryset=order.order.all()
        )

        if "update order" in request.POST:
            if form_order.is_valid():
                order = form_order.save(commit=False)
                order.save()
                for instance in order_composition:
                    instance.delete()
                for instance in composition_tx:
                    instance.delete()
                for instance in tx_supplier_invoice:
                    instance.delete()
                for instance in supplier_invoice_tx:
                    instance.delete()

                for form in update_order_line_formset:
                    order_inventory = OrderComposition(
                        inventory_id=form["inventory"].value(),
                        warehouse_id=form["warehouse"].value(),
                        qty_ordered=form["qty_ordered"].value(),
                        qty_delivered=0,
                        qty_returned=0,
                        vat_id=form["vat"].value(),
                        price_excl=form["price_excl"].value(),
                        price_incl=form["price_incl"].value(),
                    )
                    order_inventory.save()
                    order.save()
                    order.order.add(order_inventory)
                    order.save()

                messages.success(request, "Order Updated")
                return redirect("inventories:order_composition_view", order=order.id)
            else:
                messages.error(request, "order form faulty")

        self.context["form_order"] = form_order
        self.context["formset_addorderline"] = update_order_line_formset

        return render(request, self.template_name, self.context)


class OrderReceiveView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Inventories/Orders/order_receive.html"
        self.context = ObjectMixin.get_default_context("Receive Order")

    def get_return_url(self, request, *args, **kwargs):
        group = request.user.groups.all()
        redirect_url = redirect(
            "inventories:order_composition_view", order=self.kwargs.get("order")
        )
        for group in request.user.groups.all():
            if group.name == "Storeman":
                redirect_url = redirect("inventories:order_receive_view")
        return redirect_url

    @method_decorator(
        permitted_groups(allowed_roles=["super", "consultant", "Storeman"])
    )
    def get(self, request, *args, **kwargs):
        order_id = self.kwargs.get("order")

        if order_id:
            order = get_object_or_404(Order, id=order_id)
            if order.status == Order.Status.COMPLETED:
                messages.error(request, "Order already filled")
                return self.get_return_url(request, *args, **kwargs)
            order_composition = OrderComposition.objects.filter(order=order)
            order_composition = order_composition.annotate(sum=Sum("price_excl"))

            total = 0
            qty_delivered = 0
            qty_returned = 0
            qty = 0
            for instance in order_composition:
                qty_delivered = 0
                qty_returned = 0
                qty = instance.qty_ordered
                if instance.qty_delivered:
                    qty_delivered = instance.qty_delivered
                else:
                    qty_delivered = 0
                if instance.qty_returned:
                    qty_returned = instance.qty_returned
                else:
                    qty_returned = 0
                total = qty - (qty_delivered + qty_returned)
                instance.sum = total  # type: ignore
                total = 0

            deliverorderformset = DeliverOrderFormSet(queryset=order_composition)

            self.context["deliverorderformset"] = deliverorderformset
            self.context["order"] = order
            self.context["order_composition"] = order_composition

        form_order = OrderFilterForm()  # 104692 intik
        self.context["form_order"] = form_order
        return render(request, self.template_name, self.context)

    @method_decorator(
        permitted_groups(allowed_roles=["super", "consultant", "Storeman"])
    )
    def post(self, request, *args, **kwargs):
        order_id = self.kwargs.get("order")
        if order_id:
            order = get_object_or_404(Order, id=order_id)
            if order.status == Order.Status.COMPLETED:
                messages.error(request, "Order already filled")
                return self.get_return_url(request, *args, **kwargs)
            deliverorderformset = DeliverOrderFormSet(request.POST)

            if "receive order" in request.POST:
                deliverorderformset.save(commit=False)
                should_invoice = False

                for instance in deliverorderformset:
                    try:
                        comp_id = int(instance["id"].value())

                        qty_ordered = 0
                        qty_delivered = 0
                        qty_returned = 0
                        qty_remaining = 0

                        qty_total = 0
                        delivered = 0

                        tot_returned = 0
                        tot_delivered = 0

                        order_comp = get_object_or_404(OrderComposition, id=comp_id)
                        if order_comp.qty_ordered:
                            qty_ordered = order_comp.qty_ordered
                        else:
                            qty_ordered = 0

                        if order_comp.qty_delivered:
                            qty_delivered = order_comp.qty_delivered
                        else:
                            qty_delivered = 0

                        if order_comp.qty_returned:
                            qty_returned = order_comp.qty_returned
                        else:
                            qty_returned = 0

                        qty_remaining = qty_ordered - (qty_delivered + qty_returned)

                        if instance["qty_delivered"]:
                            delivered = Decimal(instance["qty_delivered"].value())
                        else:
                            delivered = 0

                        if instance["qty_returned"]:
                            returned = Decimal(instance["qty_returned"].value())
                        else:
                            returned = 0

                        qty_total = delivered + returned

                        if qty_remaining >= qty_total and qty_total != 0:
                            tot_delivered = qty_delivered + delivered
                            tot_returned = qty_returned + returned

                            if delivered > 0:
                                delivery_note = InventoryTransaction(
                                    date=datetime.now(),
                                    type_id=1,
                                    inventory=order_comp.inventory,
                                    qty=delivered,
                                    warehouse=order_comp.warehouse,
                                    order_composition=order_comp,
                                    price_excl=order_comp.price_excl,
                                    price_incl=order_comp.price_incl,
                                )

                                if not should_invoice:
                                    invoice = Invoice(
                                        date=datetime.now(),
                                        supplier=order.supplier,
                                        order=order,
                                    )
                                    invoice.save()
                                    should_invoice = True

                                excl = float(delivery_note.qty * order_comp.price_excl)
                                incl = float(delivery_note.qty * order_comp.price_incl)

                                transaction = Transaction(
                                    date=datetime.now(),
                                    supplier=order.supplier,
                                    category_id=1,
                                    description=f"{delivery_note.inventory.description} x {delivery_note.qty}",
                                    amount_excl=excl,
                                    amount_incl=incl,
                                )
                                transaction.save()
                                delivery_note.supplier_invoice = transaction
                                delivery_note.save()

                                invoice.tx.add(transaction)
                            order_comp.qty_delivered = tot_delivered
                            order_comp.qty_returned = tot_returned
                            order_comp.save()
                    except Exception as _:
                        pass
                order_composition = OrderComposition.objects.filter(order=order)
                total = 0
                for instance in order_composition:
                    total += (
                        instance.qty_ordered
                        - instance.qty_delivered
                        - instance.qty_returned
                    )

                if total == 0:
                    order.status = Order.Status.COMPLETED
                    order.save()
                else:
                    order.status = Order.Status.PENDING
                    order.save()
                return self.get_return_url(request, *args, **kwargs)

        if "filter" in request.POST:
            form_order = OrderFilterForm(request.POST)
            if form_order.is_valid():
                form_order.save(commit=False)
                try:
                    order = Order.objects.get(
                        id=int(request.POST.get("purchase_order"))
                    )
                    return redirect(
                        "inventories:order_receive_view",
                        order=int(request.POST.get("purchase_order")),
                    )
                except Exception as _:
                    messages.error(request, "Invalid Purchase Order number")
                    return redirect("inventories:order_receive_view")


class OrderListView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Inventories/Orders/order_list.html"
        self.context = ObjectMixin.get_default_context("Current Orders")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        form_file = QuoteUploadForm()
        queryset = Order.objects.all()
        queryset = queryset.select_related("supplier")
        queryset = queryset.select_related("status")
        queryset = queryset.annotate(
            total=Sum(
                F("order__price_incl") * F("order__qty_ordered"),
                output_field=models.FloatField(),
            )
        )

        self.context["queryset"] = queryset
        self.context["form_file"] = form_file
        return render(request, self.template_name, self.context)

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def post(self, request, *args, **kwargs):
        form_file = QuoteUploadForm()

        for key in request.POST.keys():
            if key.startswith("edit quote"):
                order_id = key[10:]
                instance = get_object_or_404(Order, id=order_id)

                form_file = QuoteUploadForm(request.POST, request.FILES)

                if form_file.is_valid:
                    if instance.quote:
                        if os.path.isfile(instance.quote.path):
                            os.remove(instance.quote.path)

                        instance.quote = None
                        instance.quote.delete()
                        instance.save()
                    form_file = QuoteUploadForm(
                        request.POST, request.FILES, instance=instance
                    )
                    if form_file.is_valid:
                        form_file.save()
                        return redirect("inventories:order_list_view")

            elif key.startswith("delete quote"):
                order_id = key[12:]
                instance = get_object_or_404(Order, id=order_id)
                try:
                    if os.path.isfile(instance.quote.path):
                        os.remove(instance.quote.path)

                    instance.quote = None
                    instance.quote.delete()
                    instance.save()
                except Exception as _:
                    messages.error(request, "File not deleted")
                    return redirect("inventories:order_list_view")

        self.context["queryset"] = Order.objects.all()
        self.context["form_file"] = form_file
        return render(request, self.template_name, self.context)


class OrderCompositionListView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Inventories/Orders/order_composition_list.html"
        self.context = ObjectMixin.get_default_context("Current Orders Details")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        form = CompositionFilterForm()

        self.context["form"] = form
        return render(request, self.template_name, self.context)

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def post(self, request, *args, **kwargs):
        queryset = (
            OrderComposition.objects.all()
            .select_related("inventory")
            .prefetch_related("order_set", "order_set__supplier", "order_set__status")
        )
        # queryset = queryset.exclude(Q(order=None)) #not working

        form = CompositionFilterForm(request.POST)
        if "filter" in request.POST:
            f_po = request.POST.get("purchase_order")
            f_supplier = request.POST.get("supplier")
            f_status = request.POST.get("status")
            f_inventory = request.POST.get("inventory")

            if f_po:
                queryset = queryset.filter(order__id__icontains=f_po)
            if f_supplier:
                queryset = queryset.filter(order__supplier=f_supplier)
            if f_status:
                queryset = queryset.filter(order__status=f_status)
            if f_inventory:
                queryset = queryset.filter(
                    inventory__description__icontains=f_inventory
                )

        self.context["form"] = form
        self.context["queryset"] = queryset
        return render(request, self.template_name, self.context)


class OrderDeliveryListView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Inventories/Orders/order_delivery_list.html"
        self.context = ObjectMixin.get_default_context("Current Deliveries")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        queryset = InventoryTransaction.objects.filter(type_id=1)

        form = DeliveryFilterForm()
        form_file = DeliveryNoteUploadForm()

        self.context["form"] = form
        self.context["form_file"] = form_file
        self.context["queryset"] = queryset
        return render(request, self.template_name, self.context)

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def post(self, request, *args, **kwargs):
        queryset = InventoryTransaction.objects.all().order_by("supplier_invoice__date")

        form = DeliveryFilterForm(request.POST)
        if "filter" in request.POST:
            f_po = request.POST.get("purchase_order")
            f_supplier = request.POST.get("supplier")
            request.POST.get("status")
            f_inventory = request.POST.get("inventory")

            if f_po:
                queryset = queryset.filter(ordercomposition__order__id__icontains=f_po)
            if f_supplier:
                queryset = queryset.filter(supplier_invoice__supplier=f_supplier)
            if f_inventory:
                queryset = queryset.filter(inventory=f_inventory)

        else:
            for key in request.POST.keys():
                if key.startswith("edit file"):
                    inv_tx_id = key[9:]
                    instance = get_object_or_404(InventoryTransaction, id=inv_tx_id)

                    form_file = DeliveryNoteUploadForm(request.POST, request.FILES)

                    if form_file.is_valid:
                        if instance.delivery_note:
                            if os.path.isfile(instance.delivery_note.path):
                                os.remove(instance.delivery_note.path)

                            instance.delivery_note = None
                            instance.delivery_note.delete()
                            instance.save()
                        form_file = DeliveryNoteUploadForm(
                            request.POST, request.FILES, instance=instance
                        )
                        if form_file.is_valid:
                            form_file.save()
                            return redirect("inventories:order_delivery_list_view")

                if key.startswith("delete file"):
                    inv_tx_id = key[11:]
                    instance = get_object_or_404(InventoryTransaction, id=inv_tx_id)
                    try:
                        if os.path.isfile(instance.delivery_note.path):
                            os.remove(instance.delivery_note.path)

                        instance.delivery_note = None
                        instance.delivery_note.delete()
                        instance.save()
                    except Exception as _:
                        messages.error(request, "File not deleted")
                        return redirect("inventories:order_delivery_list_view")

        form_file = DeliveryNoteUploadForm()
        self.context["form_file"] = form_file
        self.context["form"] = form
        self.context["queryset"] = queryset
        return render(request, self.template_name, self.context)


class DeliveryNoteFileServeView(View):
    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        inv_tx_id = self.kwargs.get("id")
        inv_tx = InventoryTransaction.objects.get(id=inv_tx_id)
        try:
            file_type = mimetypes.guess_type(inv_tx.delivery_note.path)
            response = HttpResponse(
                inv_tx.delivery_note.read(), content_type=file_type[0]
            )
            response["Content-Disposition"] = "inline;filename=some_file"
        except Exception as _:
            messages.error(request, "File not found")
            return redirect("inventories:order_delivery_list_view")
        return response


class QuoteFileServeView(View):
    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        order_id = self.kwargs.get("id")
        order = Order.objects.get(id=order_id)
        try:
            file_type = mimetypes.guess_type(order.quote.path)
            response = HttpResponse(order.quote.read(), content_type=file_type[0])
            response["Content-Disposition"] = "inline;filename=some_file"
        except Exception as _:
            messages.error(request, "File not found")
            return redirect("inventories:order_list_view")
        return response
