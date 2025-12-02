"""Views for Ledger Management (Advance Payments, Retention, Materials, etc.)."""

from decimal import Decimal

from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    UpdateView,
)

from app.BillOfQuantities.models import (
    AdvancePayment,
    Escalation,
    MaterialsOnSite,
    Retention,
    SpecialItemTransaction,
)
from app.core.Utilities.forms import styled_date_input
from app.core.Utilities.permissions import UserHasGroupGenericMixin
from app.Project.models import Project

# =============================================================================
# Advance Payment Views
# =============================================================================


class AdvancePaymentListView(UserHasGroupGenericMixin, ListView):
    """List all advance payments for a project."""

    model = AdvancePayment
    template_name = "ledger/advance_payment_list.html"
    context_object_name = "transactions"
    permissions = ["contractor"]

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter advance payments by project."""
        return AdvancePayment.objects.filter(
            project=self.get_project(),
            deleted=False,
        ).order_by("-date", "-created_at")

    def get_context_data(self, **kwargs):
        """Add project and balance info to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project

        # Calculate running balance
        balance = AdvancePayment.get_balance_for_project(project)
        context["current_balance"] = balance

        # Get ledger with running balances
        transactions = list(self.get_queryset())
        running_balance = Decimal("0.00")
        for txn in reversed(transactions):
            running_balance += txn.signed_amount
            txn.running_balance = running_balance  # type: ignore
        context["transactions"] = transactions

        # Project advance payment settings
        context["advance_percentage"] = project.advance_payment_percentage
        context["recovery_percentage"] = project.advance_recovery_percentage

        return context


class AdvancePaymentCreateView(UserHasGroupGenericMixin, CreateView):
    """Create a new advance payment transaction."""

    class CreateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["date"].widget = styled_date_input
            self.fields["guarantee_expiry"].widget = styled_date_input

        class Meta:
            model = AdvancePayment
            fields = [
                "transaction_type",
                "amount",
                "description",
                "date",
                "payment_certificate",
                "recovery_method",
                "recovery_percentage",
                "guarantee_reference",
                "guarantee_expiry",
            ]

    model = AdvancePayment
    template_name = "ledger/advance_payment_form.html"
    permissions = ["contractor"]
    form_class = CreateForm

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def form_valid(self, form):
        """Set project and captured_by before saving."""
        form.instance.project = self.get_project()
        form.instance.captured_by = self.request.user
        messages.success(
            self.request, "Advance payment transaction created successfully!"
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to advance payment list."""
        return reverse(
            "bill_of_quantities:advance-payment-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = True
        return context


class AdvancePaymentUpdateView(UserHasGroupGenericMixin, UpdateView):
    """Update an advance payment transaction."""

    class UpdateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["date"].widget = styled_date_input
            self.fields["guarantee_expiry"].widget = styled_date_input

        class Meta:
            model = AdvancePayment
            fields = [
                "transaction_type",
                "amount",
                "description",
                "date",
                "payment_certificate",
                "recovery_method",
                "recovery_percentage",
                "guarantee_reference",
                "guarantee_expiry",
            ]

    model = AdvancePayment
    template_name = "ledger/advance_payment_form.html"
    permissions = ["contractor"]
    form_class = UpdateForm

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter by project."""
        return AdvancePayment.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Add success message."""
        messages.success(
            self.request, "Advance payment transaction updated successfully!"
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to advance payment list."""
        return reverse(
            "bill_of_quantities:advance-payment-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = False
        return context


class AdvancePaymentDeleteView(UserHasGroupGenericMixin, DeleteView):
    """Delete an advance payment transaction."""

    model = AdvancePayment
    template_name = "ledger/advance_payment_confirm_delete.html"
    permissions = ["contractor"]

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter by project."""
        return AdvancePayment.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Soft delete the transaction."""
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(
            self.request, "Advance payment transaction deleted successfully!"
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to advance payment list."""
        return reverse(
            "bill_of_quantities:advance-payment-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


# =============================================================================
# Retention Views
# =============================================================================


class RetentionListView(UserHasGroupGenericMixin, ListView):
    """List all retention transactions for a project."""

    model = Retention
    template_name = "ledger/retention_list.html"
    context_object_name = "transactions"
    permissions = ["contractor"]

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter retentions by project."""
        return Retention.objects.filter(
            project=self.get_project(),
            deleted=False,
        ).order_by("-date", "-created_at")

    def get_context_data(self, **kwargs):
        """Add project and balance info to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project

        # Calculate running balance
        balance = Retention.get_balance_for_project(project)
        context["current_balance"] = balance

        # Get ledger with running balances
        transactions = list(self.get_queryset())
        running_balance = Decimal("0.00")
        for txn in reversed(transactions):
            running_balance += txn.signed_amount
            txn.running_balance = running_balance  # type: ignore
        context["transactions"] = transactions

        # Project retention settings
        context["retention_percentage"] = project.retention_percentage
        context["retention_limit"] = project.retention_limit_percentage

        return context


class RetentionCreateView(UserHasGroupGenericMixin, CreateView):
    """Create a new retention transaction."""

    class CreateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["date"].widget = styled_date_input

        class Meta:
            model = Retention
            fields = [
                "retention_type",
                "transaction_type",
                "amount",
                "description",
                "date",
                "payment_certificate",
                "retention_percentage",
            ]

    model = Retention
    template_name = "ledger/retention_form.html"
    permissions = ["contractor"]
    form_class = CreateForm

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def form_valid(self, form):
        """Set project and captured_by before saving."""
        form.instance.project = self.get_project()
        form.instance.captured_by = self.request.user
        messages.success(self.request, "Retention transaction created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to retention list."""
        return reverse(
            "bill_of_quantities:retention-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = True
        return context


class RetentionUpdateView(UserHasGroupGenericMixin, UpdateView):
    """Update a retention transaction."""

    class UpdateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["date"].widget = styled_date_input

        class Meta:
            model = Retention
            fields = [
                "retention_type",
                "transaction_type",
                "amount",
                "description",
                "date",
                "payment_certificate",
                "retention_percentage",
            ]

    model = Retention
    template_name = "ledger/retention_form.html"
    permissions = ["contractor"]
    form_class = UpdateForm

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter by project."""
        return Retention.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Add success message."""
        messages.success(self.request, "Retention transaction updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to retention list."""
        return reverse(
            "bill_of_quantities:retention-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = False
        return context


class RetentionDeleteView(UserHasGroupGenericMixin, DeleteView):
    """Delete a retention transaction."""

    model = Retention
    template_name = "ledger/retention_confirm_delete.html"
    permissions = ["contractor"]

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter by project."""
        return Retention.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Soft delete the transaction."""
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(self.request, "Retention transaction deleted successfully!")
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to retention list."""
        return reverse(
            "bill_of_quantities:retention-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


# =============================================================================
# Materials on Site Views
# =============================================================================


class MaterialsOnSiteListView(UserHasGroupGenericMixin, ListView):
    """List all materials on site for a project."""

    model = MaterialsOnSite
    template_name = "ledger/materials_list.html"
    context_object_name = "transactions"
    permissions = ["contractor"]

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter materials by project."""
        return MaterialsOnSite.objects.filter(
            project=self.get_project(),
            deleted=False,
        ).order_by("-date", "-created_at")

    def get_context_data(self, **kwargs):
        """Add project and balance info to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project

        # Calculate running balance
        balance = MaterialsOnSite.get_balance_for_project(project)
        context["current_balance"] = balance

        # Get ledger with running balances
        transactions = list(self.get_queryset())
        running_balance = Decimal("0.00")
        for txn in reversed(transactions):
            running_balance += txn.signed_amount
            txn.running_balance = running_balance  # type: ignore
        context["transactions"] = transactions

        return context


class MaterialsOnSiteCreateView(UserHasGroupGenericMixin, CreateView):
    """Create a new materials on site transaction."""

    class CreateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["date"].widget = styled_date_input

        class Meta:
            model = MaterialsOnSite
            fields = [
                "material_status",
                "transaction_type",
                "amount",
                "description",
                "date",
                "payment_certificate",
                "material_description",
                "quantity",
                "unit",
                "unit_price",
                "delivery_note_reference",
                "storage_location",
            ]

    model = MaterialsOnSite
    template_name = "ledger/materials_form.html"
    permissions = ["contractor"]
    form_class = CreateForm

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def form_valid(self, form):
        """Set project and captured_by before saving."""
        form.instance.project = self.get_project()
        form.instance.captured_by = self.request.user
        messages.success(
            self.request, "Materials on site transaction created successfully!"
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to materials list."""
        return reverse(
            "bill_of_quantities:materials-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = True
        return context


class MaterialsOnSiteUpdateView(UserHasGroupGenericMixin, UpdateView):
    """Update a materials on site transaction."""

    class UpdateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["date"].widget = styled_date_input

        class Meta:
            model = MaterialsOnSite
            fields = [
                "material_status",
                "transaction_type",
                "amount",
                "description",
                "date",
                "payment_certificate",
                "material_description",
                "quantity",
                "unit",
                "unit_price",
                "delivery_note_reference",
                "storage_location",
            ]

    model = MaterialsOnSite
    template_name = "ledger/materials_form.html"
    permissions = ["contractor"]
    form_class = UpdateForm

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter by project."""
        return MaterialsOnSite.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Add success message."""
        messages.success(
            self.request, "Materials on site transaction updated successfully!"
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to materials list."""
        return reverse(
            "bill_of_quantities:materials-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = False
        return context


class MaterialsOnSiteDeleteView(UserHasGroupGenericMixin, DeleteView):
    """Delete a materials on site transaction."""

    model = MaterialsOnSite
    template_name = "ledger/materials_confirm_delete.html"
    permissions = ["contractor"]

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter by project."""
        return MaterialsOnSite.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Soft delete the transaction."""
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(
            self.request, "Materials on site transaction deleted successfully!"
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to materials list."""
        return reverse(
            "bill_of_quantities:materials-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


# =============================================================================
# Escalation Views
# =============================================================================


class EscalationListView(UserHasGroupGenericMixin, ListView):
    """List all escalation transactions for a project."""

    model = Escalation
    template_name = "ledger/escalation_list.html"
    context_object_name = "transactions"
    permissions = ["contractor"]

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter escalations by project."""
        return Escalation.objects.filter(
            project=self.get_project(),
            deleted=False,
        ).order_by("-date", "-created_at")

    def get_context_data(self, **kwargs):
        """Add project and balance info to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project

        # Calculate running balance
        balance = Escalation.get_balance_for_project(project)
        context["current_balance"] = balance

        # Get ledger with running balances
        transactions = list(self.get_queryset())
        running_balance = Decimal("0.00")
        for txn in reversed(transactions):
            running_balance += txn.signed_amount
            txn.running_balance = running_balance  # type: ignore
        context["transactions"] = transactions

        return context


class EscalationCreateView(UserHasGroupGenericMixin, CreateView):
    """Create a new escalation transaction."""

    class CreateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["date"].widget = styled_date_input
            self.fields["base_date"].widget = styled_date_input
            self.fields["current_date"].widget = styled_date_input

        class Meta:
            model = Escalation
            fields = [
                "escalation_type",
                "transaction_type",
                "amount",
                "description",
                "date",
                "payment_certificate",
                "base_date",
                "current_date",
                "base_index",
                "current_index",
                "escalation_factor",
                "formula_reference",
            ]

    model = Escalation
    template_name = "ledger/escalation_form.html"
    permissions = ["contractor"]
    form_class = CreateForm

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def form_valid(self, form):
        """Set project and captured_by before saving."""
        form.instance.project = self.get_project()
        form.instance.captured_by = self.request.user
        messages.success(self.request, "Escalation transaction created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to escalation list."""
        return reverse(
            "bill_of_quantities:escalation-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = True
        return context


class EscalationUpdateView(UserHasGroupGenericMixin, UpdateView):
    """Update an escalation transaction."""

    class UpdateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["date"].widget = styled_date_input
            self.fields["base_date"].widget = styled_date_input
            self.fields["current_date"].widget = styled_date_input

        class Meta:
            model = Escalation
            fields = [
                "escalation_type",
                "transaction_type",
                "amount",
                "description",
                "date",
                "payment_certificate",
                "base_date",
                "current_date",
                "base_index",
                "current_index",
                "escalation_factor",
                "formula_reference",
            ]

    model = Escalation
    template_name = "ledger/escalation_form.html"
    permissions = ["contractor"]
    form_class = UpdateForm

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter by project."""
        return Escalation.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Add success message."""
        messages.success(self.request, "Escalation transaction updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to escalation list."""
        return reverse(
            "bill_of_quantities:escalation-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = False
        return context


class EscalationDeleteView(UserHasGroupGenericMixin, DeleteView):
    """Delete an escalation transaction."""

    model = Escalation
    template_name = "ledger/escalation_confirm_delete.html"
    permissions = ["contractor"]

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter by project."""
        return Escalation.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Soft delete the transaction."""
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(self.request, "Escalation transaction deleted successfully!")
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to escalation list."""
        return reverse(
            "bill_of_quantities:escalation-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context


# =============================================================================
# Special Items Views (reusing existing special item views for now)
# =============================================================================


class SpecialItemTransactionListView(UserHasGroupGenericMixin, ListView):
    """List all special item transactions for a project."""

    model = SpecialItemTransaction
    template_name = "ledger/special_item_list.html"
    context_object_name = "transactions"
    permissions = ["contractor"]

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
            account=self.request.user,
        )

    def get_queryset(self):
        """Filter special items by project."""
        return SpecialItemTransaction.objects.filter(
            project=self.get_project(),
            deleted=False,
        ).order_by("-date", "-created_at")

    def get_context_data(self, **kwargs):
        """Add project and balance info to context."""
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project

        # Calculate running balance
        balance = SpecialItemTransaction.get_balance_for_project(project)
        context["current_balance"] = balance

        # Get ledger with running balances
        transactions = list(self.get_queryset())
        running_balance = Decimal("0.00")
        for txn in reversed(transactions):
            running_balance += txn.signed_amount
            txn.running_balance = running_balance  # type: ignore
        context["transactions"] = transactions

        return context
