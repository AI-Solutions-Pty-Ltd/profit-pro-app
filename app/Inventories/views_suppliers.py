import mimetypes
import os

from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from app.core.Utilities.permissions import permitted_groups
from app.Inventories.apps import ObjectMixin
from app.Inventories.forms_suppliers import (
    InvoiceTransactionCreateForm,
    InvoiceTransactionCreateFormSet,
    Supplier,
    SupplierCreateForm,
    SupplierInvoiceUploadForm,
)
from app.Inventories.models_suppliers import Invoice, Transaction


class SupplierListView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Suppliers/supplier_list.html"
        self.context = ObjectMixin.get_default_context("Suppliers")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        queryset = Supplier.objects.all().order_by("description")
        queryset = queryset.annotate(sum=Sum("transaction__amount_incl"))
        self.context["queryset"] = queryset
        return render(request, self.template_name, self.context)


class SupplierDetailView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Suppliers/supplier_detail.html"
        self.context = ObjectMixin.get_default_context("Supplier Detail")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        supplier_id = self.kwargs.get("supplier")

        supplier = get_object_or_404(Supplier, id=supplier_id)

        form = SupplierCreateForm(instance=supplier)

        self.context["form"] = form
        self.context["object"] = supplier
        return render(request, self.template_name, self.context)

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def post(self, request, *args, **kwargs):
        supplier_id = self.kwargs.get("supplier")

        supplier = get_object_or_404(Supplier, id=supplier_id)

        form = SupplierCreateForm(request.POST, instance=supplier)
        if "update" in request.POST:
            if form.is_valid():
                form.save()
                return redirect("suppliers:supplier_detail_view", supplier=supplier_id)
        self.context["form"] = form
        self.context["object"] = supplier
        return render(request, self.template_name, self.context)


class SupplierCreateView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Suppliers/supplier_create.html"
        self.context = ObjectMixin.get_default_context("Create Supplier")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        form = SupplierCreateForm()
        self.context["form"] = form
        return render(request, self.template_name, self.context)

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def post(self, request, *args, **kwargs):
        form = SupplierCreateForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.save()
            return redirect("suppliers:supplier_detail_view", supplier=supplier.id)
        self.context["form"] = form
        return render(request, self.template_name, self.context)


class SupplierStatementView(View):
    def __init__(self, *args, **kwargs):
        self.template_name = "Suppliers/supplier_statement.html"
        self.context = ObjectMixin.get_default_context("Supplier Statement")

    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        supplier_id = self.kwargs.get("supplier")

        supplier = get_object_or_404(Supplier, id=supplier_id)
        queryset = Invoice.objects.filter(supplier=supplier).order_by("date")
        queryset = queryset.annotate(sum=Sum("tx__amount_incl"))
        queryset = queryset.annotate(balance=Sum("tx__amount_incl"))

        invoices = Transaction.objects.filter(supplier=supplier)

        total = 0
        for instance in queryset:
            if instance.sum:  # type: ignore
                total += float(instance.sum)  # type: ignore
                instance.balance = total  # type: ignore
        form_add_tx = InvoiceTransactionCreateForm()
        form_tx = InvoiceTransactionCreateFormSet(queryset=invoices)
        form_file = SupplierInvoiceUploadForm()

        self.context["object"] = supplier
        self.context["form_add_tx"] = form_add_tx
        self.context["form_tx"] = form_tx
        self.context["form_file"] = form_file
        self.context["queryset"] = queryset
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        supplier_id = self.kwargs.get("supplier")

        supplier = get_object_or_404(Supplier, id=supplier_id)
        Invoice.objects.filter(supplier=supplier).order_by("date")
        form_file = SupplierInvoiceUploadForm()

        for key in request.POST.keys():
            if key == "create invoice":
                form_tx = InvoiceTransactionCreateForm(request.POST)
                if form_tx.is_valid:
                    form = form_tx.save(commit=False)
                    if form.category_id == 2:
                        if form.amount_incl < 0:
                            form.amount_incl = -form.amount_incl

                        if supplier.vat:
                            form.amount_excl = round(float(form.amount_incl) / 1.15, 2)
                        else:
                            form.amount_excl = form.amount_incl

                    elif form.category_id == 3:
                        if form.amount_incl > 0:
                            form.amount_incl = -form.amount_incl
                            form.amount_excl = form.amount_incl

                    form.supplier = supplier
                    form.save()

                    inv = Invoice(
                        date=form.date,
                        supplier=supplier,
                        order=None,
                    )
                    inv.save()
                    inv.tx.add(form)
                    inv.save()
                    return redirect(
                        "suppliers:supplier_statement_view", supplier=supplier_id
                    )

            elif key.startswith("update transaction"):
                instance_id = key[18:]
                tx = get_object_or_404(Transaction, id=instance_id)

                form_set = InvoiceTransactionCreateFormSet(request.POST)
                instances = form_set.save(commit=False)
                for form in instances:
                    try:
                        if form.category == Transaction.Category.INVOICE:
                            if form.amount_incl < 0:
                                form.amount_incl = -form.amount_incl

                            if supplier.vat:
                                form.amount_excl = round(
                                    float(form.amount_incl) / 1.15, 2
                                )
                            else:
                                form.amount_excl = form.amount_incl

                        elif form.category == Transaction.Category.DEBIT_NOTE:
                            if form.amount_incl > 0:
                                form.amount_incl = -form.amount_incl
                                form.amount_excl = form.amount_incl
                        form.save()

                        messages.success(request, "Transaction updated")
                    except Exception as _:
                        pass

            elif key.startswith("delete transaction"):
                instance_id = key[18:]
                tx = get_object_or_404(Transaction, id=instance_id)
                inv = get_object_or_404(Invoice, tx=tx)
                tx.delete()
                inv.delete()

            elif key.startswith("edit file"):
                instance_id = key[9:]
                instance = get_object_or_404(Invoice, id=instance_id)

                form_file = SupplierInvoiceUploadForm(request.POST, request.FILES)

                if form_file.is_valid:
                    if instance.invoice:
                        if os.path.isfile(instance.invoice.path):
                            os.remove(instance.invoice.path)

                        instance.invoice = None
                        instance.invoice.delete()
                        instance.save()
                    form_file = SupplierInvoiceUploadForm(
                        request.POST, request.FILES, instance=instance
                    )
                    if form_file.is_valid:
                        form_file.save()
                        return redirect(
                            "suppliers:supplier_statement_view", supplier=supplier_id
                        )

            elif key.startswith("delete file"):
                instance_id = key[11:]
                instance = get_object_or_404(Invoice, id=instance_id)
                try:
                    if instance.invoice:
                        instance.invoice.delete()
                        instance.save()

                    if instance.invoice:
                        if os.path.isfile(instance.invoice.path):
                            os.remove(instance.invoice.path)
                except Exception as _:
                    messages.error(request, "File not deleted")
                    return redirect(
                        "suppliers:supplier_statement_view", supplier=supplier_id
                    )

        return redirect("suppliers:supplier_statement_view", supplier=supplier_id)


class SupplierInvoiceFileServeView(View):
    @method_decorator(permitted_groups(allowed_roles=["super", "consultant"]))
    def get(self, request, *args, **kwargs):
        invoice_id = self.kwargs.get("invoice")
        invoice = Invoice.objects.get(id=invoice_id)
        try:
            file_type = mimetypes.guess_type(invoice.invoice.path)
            response = HttpResponse(invoice.invoice.read(), content_type=file_type[0])
            response["Content-Disposition"] = "inline;filename=some_file"
        except Exception as _:
            messages.error(request, "File not found")
            return redirect(
                "suppliers:supplier_statement_view", supplier=invoice.supplier.id
            )
        return response
