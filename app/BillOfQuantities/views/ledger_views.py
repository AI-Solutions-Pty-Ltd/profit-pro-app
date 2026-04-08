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

from app.Account.subscription_config import Subscription
from app.BillOfQuantities.forms import (
    AdvancedPaymentCreateUpdateForm,
    EscalationCreateUpdateForm,
    MaterialsOnSiteCreateUpdateForm,
    RetentionCreateUpdateCreateForm,
)
from app.BillOfQuantities.models import (
    AdvancePayment,
    Escalation,
    MaterialsOnSite,
    Retention,
    SpecialItemTransaction,
)
from app.core.Utilities.forms import styled_date_input
from app.core.Utilities.subscription_and_role_mixin import (
    SubscriptionAndRoleRequiredMixin,
)
from app.Project.models import Project, Role

# =============================================================================
# Advance Payment Views
# =============================================================================


def get_ledger_transactions_with_balance(model_class, project):
    """
    Get ledger transactions with running balance for a given model and project.

    Args:
        model_class: The ledger model class (AdvancePayment, Retention, MaterialsOnSite, Escalation)
        project: The project instance

    Returns:
        tuple: (transactions_list, current_balance)
    """
    # Get balance using the model's class method
    current_balance = model_class.get_balance_for_project(project)

    # Get transactions ordered by date
    transactions = list(
        model_class.objects.filter(
            project=project,
            deleted=False,
        ).order_by("-date", "-created_at")
    )

    # Calculate running balances
    running_balance = Decimal("0.00")
    transactions_with_balance = []

    for txn in reversed(transactions):
        running_balance += txn.signed_amount
        # Create a dict with transaction data and running balance
        txn_data = {
            "id": txn.pk,
            "transaction_type": txn.transaction_type,
            "amount": txn.amount,
            "description": txn.description,
            "date": txn.date,
            "payment_certificate": txn.payment_certificate,
            "captured_by": txn.captured_by,
            "created_at": txn.created_at,
            "signed_amount": txn.signed_amount,
            "running_balance": running_balance,
            "instance": txn,  # Keep reference to original instance for template access
        }

        # Add model-specific fields
        if hasattr(txn, "recovery_method"):  # AdvancePayment
            txn_data.update(
                {
                    "recovery_method": txn.recovery_method,
                    "recovery_percentage": txn.recovery_percentage,
                    "guarantee_reference": txn.guarantee_reference,
                    "guarantee_expiry": txn.guarantee_expiry,
                }
            )
        elif hasattr(txn, "retention_type"):  # Retention
            txn_data.update(
                {
                    "retention_type": txn.retention_type,
                    "retention_percentage": txn.retention_percentage,
                }
            )
        elif hasattr(txn, "material_status"):  # MaterialsOnSite
            txn_data.update(
                {
                    "material_status": txn.material_status,
                    "material_description": txn.material_description,
                    "quantity": txn.quantity,
                    "unit": txn.unit,
                    "unit_price": txn.unit_price,
                    "delivery_note_reference": txn.delivery_note_reference,
                    "storage_location": txn.storage_location,
                }
            )
        elif hasattr(txn, "escalation_type"):  # Escalation
            txn_data.update(
                {
                    "escalation_type": txn.escalation_type,
                    "base_date": txn.base_date,
                    "current_date": txn.current_date,
                    "base_index": txn.base_index,
                    "current_index": txn.current_index,
                    "escalation_factor": txn.escalation_factor,
                    "formula_reference": txn.formula_reference,
                }
            )

        transactions_with_balance.append(txn_data)

    return transactions_with_balance, current_balance


class AdvancePaymentListView(SubscriptionAndRoleRequiredMixin, ListView):
    """List all advance payments for a project."""

    model = AdvancePayment
    template_name = "ledger/advance_payment_list.html"
    context_object_name = "transactions"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
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

        # Get transactions with running balance using reusable function
        transactions_with_balance, current_balance = (
            get_ledger_transactions_with_balance(AdvancePayment, project)
        )
        context["transactions"] = transactions_with_balance
        context["current_balance"] = current_balance

        # Project advance payment settings
        context["advance_percentage"] = project.advance_payment_percentage
        context["recovery_percentage"] = project.advance_recovery_percentage
        context["advanced_payment_form"] = AdvancedPaymentCreateUpdateForm(
            project=project
        )

        return context


class AdvancePaymentCreateView(SubscriptionAndRoleRequiredMixin, CreateView):
    """Create a new advance payment transaction."""

    model = AdvancePayment
    template_name = "ledger/advance_payment_form.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    form_class = AdvancedPaymentCreateUpdateForm
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
        )

    def get_form_kwargs(self):
        """Pass project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

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
        context["advanced_payment_form"] = context["form"]
        return context


class AdvancePaymentUpdateView(SubscriptionAndRoleRequiredMixin, UpdateView):
    """Update an advance payment transaction."""

    model = AdvancePayment
    template_name = "ledger/advance_payment_form.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    form_class = AdvancedPaymentCreateUpdateForm
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
        )

    def get_form_kwargs(self):
        """Pass project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

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
        context["advanced_payment_form"] = context["form"]
        return context


class AdvancePaymentDeleteView(SubscriptionAndRoleRequiredMixin, DeleteView):
    """Delete an advance payment transaction."""

    model = AdvancePayment
    template_name = "ledger/advance_payment_confirm_delete.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
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


class RetentionListView(SubscriptionAndRoleRequiredMixin, ListView):
    """List all retention transactions for a project."""

    model = Retention
    template_name = "ledger/retention_list.html"
    context_object_name = "transactions"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
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

        # Get transactions with running balance using reusable function
        transactions_with_balance, current_balance = (
            get_ledger_transactions_with_balance(Retention, project)
        )
        context["transactions"] = transactions_with_balance
        context["current_balance"] = current_balance

        # Project retention settings
        context["retention_percentage"] = project.retention_percentage
        context["retention_limit"] = project.retention_limit_percentage
        context["retention_form"] = RetentionCreateUpdateCreateForm(project=project)
        return context


class RetentionCreateView(SubscriptionAndRoleRequiredMixin, CreateView):
    """Create a new retention transaction."""

    model = Retention
    template_name = "ledger/retention_form.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    form_class = RetentionCreateUpdateCreateForm
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
        )

    def get_form_kwargs(self):
        """Pass project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

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
        context["retention_form"] = context["form"]
        return context


class RetentionUpdateView(SubscriptionAndRoleRequiredMixin, UpdateView):
    """Update a retention transaction."""

    model = Retention
    template_name = "ledger/retention_form.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    form_class = RetentionCreateUpdateCreateForm
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
        )

    def get_form_kwargs(self):
        """Pass project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

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
        context["retention_form"] = context["form"]
        return context


class RetentionDeleteView(SubscriptionAndRoleRequiredMixin, DeleteView):
    """Delete a retention transaction."""

    model = Retention
    template_name = "ledger/retention_confirm_delete.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
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


# Materials on Site Views
# =============================================================================


class MaterialsOnSiteListView(SubscriptionAndRoleRequiredMixin, ListView):
    """List all materials on site transactions."""

    model = MaterialsOnSite
    template_name = "ledger/materials_list.html"
    context_object_name = "transactions"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
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

        # Get transactions with running balance using reusable function
        transactions_with_balance, current_balance = (
            get_ledger_transactions_with_balance(MaterialsOnSite, project)
        )
        context["transactions"] = transactions_with_balance
        context["current_balance"] = current_balance

        context["materials_on_site_form"] = MaterialsOnSiteCreateUpdateForm(
            project=project
        )
        return context


class MaterialsOnSiteCreateView(SubscriptionAndRoleRequiredMixin, CreateView):
    """Create a new materials on site transaction."""

    model = MaterialsOnSite
    template_name = "ledger/materials_form.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    form_class = MaterialsOnSiteCreateUpdateForm
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
        )

    def get_form_kwargs(self):
        """Pass project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

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
        context["materials_on_site_form"] = context["form"]
        return context


class MaterialsOnSiteUpdateView(SubscriptionAndRoleRequiredMixin, UpdateView):
    """Update a materials on site transaction."""

    model = MaterialsOnSite
    template_name = "ledger/materials_form.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    form_class = MaterialsOnSiteCreateUpdateForm
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
        )

    def get_form_kwargs(self):
        """Pass project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

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
        context["materials_on_site_form"] = context["form"]
        return context


class MaterialsOnSiteDeleteView(SubscriptionAndRoleRequiredMixin, DeleteView):
    """Delete a materials on site transaction."""

    model = MaterialsOnSite
    template_name = "ledger/materials_confirm_delete.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
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


class EscalationListView(SubscriptionAndRoleRequiredMixin, ListView):
    """List all escalation transactions."""

    model = Escalation
    template_name = "ledger/escalation_list.html"
    context_object_name = "transactions"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
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

        # Get transactions with running balance using reusable function
        transactions_with_balance, current_balance = (
            get_ledger_transactions_with_balance(Escalation, project)
        )
        context["transactions"] = transactions_with_balance
        context["current_balance"] = current_balance

        context["escalation_form"] = EscalationCreateUpdateForm(project=project)
        return context


class EscalationCreateView(SubscriptionAndRoleRequiredMixin, CreateView):
    """Create a new escalation transaction."""

    model = Escalation
    template_name = "ledger/escalation_form.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    form_class = EscalationCreateUpdateForm
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
        )

    def get_form_kwargs(self):
        """Pass project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

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
        context["escalation_form"] = context["form"]
        return context


class EscalationUpdateView(SubscriptionAndRoleRequiredMixin, UpdateView):
    """Update an escalation transaction."""

    model = Escalation
    template_name = "ledger/escalation_form.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    form_class = EscalationCreateUpdateForm
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
        )

    def get_form_kwargs(self):
        """Pass project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

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
        context["escalation_form"] = context["form"]
        return context


class EscalationDeleteView(SubscriptionAndRoleRequiredMixin, DeleteView):
    """Delete an escalation transaction."""

    model = Escalation
    template_name = "ledger/escalation_confirm_delete.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
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


class SpecialItemTransactionListView(SubscriptionAndRoleRequiredMixin, ListView):
    """List all special item transactions."""

    model = SpecialItemTransaction
    template_name = "ledger/special_item_list.html"
    context_object_name = "transactions"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
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

        # Add payment certificates for the form
        context["payment_certificates"] = project.payment_certificates.all().order_by(
            "-certificate_number"
        )

        # Get ledger with running balances
        transactions = list(self.get_queryset())
        running_balance = Decimal("0.00")
        transactions_with_balance = []
        for txn in reversed(transactions):
            running_balance += txn.signed_amount
            # Create a dict with transaction data and running balance
            txn_data = {
                "id": txn.pk,
                "transaction_type": txn.transaction_type,
                "amount": txn.amount,
                "description": txn.description,
                "date": txn.date,
                "payment_certificate": txn.payment_certificate,
                "captured_by": txn.captured_by,
                "created_at": txn.created_at,
                "signed_amount": txn.signed_amount,
                "running_balance": running_balance,
                "instance": txn,  # Keep reference to original instance for template access
            }
            transactions_with_balance.append(txn_data)
        context["transactions"] = transactions_with_balance

        return context


class SpecialItemTransactionCreateView(SubscriptionAndRoleRequiredMixin, CreateView):
    """Create a new special item transaction."""

    class CreateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            self.project = kwargs.pop("project", None)
            super().__init__(*args, **kwargs)
            self.fields["date"].widget = styled_date_input

            # Filter payment certificates to current project
            if self.project:
                self.fields[
                    "payment_certificate"
                ].queryset = self.project.payment_certificates.all().order_by(  # type: ignore
                    "-created_at"
                )

        class Meta:
            model = SpecialItemTransaction
            fields = [
                "transaction_type",
                "amount",
                "description",
                "date",
                "payment_certificate",
            ]

    model = SpecialItemTransaction
    template_name = "ledger/special_item_form.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    form_class = CreateForm
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
        )

    def get_form_kwargs(self):
        """Pass project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

    def form_valid(self, form):
        """Set project and captured_by before saving."""
        form.instance.project = self.get_project()
        form.instance.captured_by = self.request.user
        messages.success(self.request, "Special item transaction created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to special item list."""
        return reverse(
            "bill_of_quantities:special-item-ledger-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = True
        return context


class SpecialItemTransactionUpdateView(SubscriptionAndRoleRequiredMixin, UpdateView):
    """Update a special item transaction."""

    class UpdateForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            self.project = kwargs.pop("project", None)
            super().__init__(*args, **kwargs)
            self.fields["date"].widget = styled_date_input

            # Filter payment certificates to current project
            if self.project:
                self.fields[
                    "payment_certificate"
                ].queryset = self.project.payment_certificates.all().order_by(  # type: ignore
                    "-created_at"
                )

        class Meta:
            model = SpecialItemTransaction
            fields = [
                "transaction_type",
                "amount",
                "description",
                "date",
                "payment_certificate",
            ]

    model = SpecialItemTransaction
    template_name = "ledger/special_item_form.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    form_class = UpdateForm
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
        )

    def get_form_kwargs(self):
        """Pass project to form."""
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_project()
        return kwargs

    def get_queryset(self):
        """Filter by project."""
        return SpecialItemTransaction.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Add success message."""
        messages.success(self.request, "Special item transaction updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect to special item list."""
        return reverse(
            "bill_of_quantities:special-item-ledger-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["is_create"] = False
        return context


class SpecialItemTransactionDeleteView(SubscriptionAndRoleRequiredMixin, DeleteView):
    """Delete a special item transaction."""

    model = SpecialItemTransaction
    template_name = "ledger/special_item_confirm_delete.html"
    roles = [Role.USER]
    required_tiers = [Subscription.PAYMENTS_AND_INVOICES]
    project_slug = "project_pk"

    def get_project(self):
        """Get the project from URL and verify ownership."""
        return get_object_or_404(
            Project,
            pk=self.kwargs["project_pk"],
        )

    def get_queryset(self):
        """Filter by project."""
        return SpecialItemTransaction.objects.filter(
            project=self.get_project(),
            deleted=False,
        )

    def form_valid(self, form):
        """Soft delete the transaction."""
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(self.request, "Special item transaction deleted successfully!")
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to special item list."""
        return reverse(
            "bill_of_quantities:special-item-ledger-list",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        """Add project to context."""
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
