"""CRUD views for Meeting."""

import json

from django.contrib import messages
from django.forms import DateInput
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbItem, BreadcrumbMixin
from app.core.Utilities.permissions import UserHasProjectRoleGenericMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project, Role
from app.SiteManagement.models.meeting import (
    Meeting,
    MeetingAction,
    MeetingActionStatus,
    MeetingDecision,
)


class MeetingMixin(
    SubscriptionRequiredMixin, UserHasProjectRoleGenericMixin, BreadcrumbMixin
):
    """Mixin for Meeting views."""

    model = Meeting
    required_tiers = [Subscription.SITE_MANAGEMENT]
    roles = [Role.ADMIN, Role.USER]
    project_slug = "project_pk"

    def get_project(self) -> Project:
        return Project.objects.get(pk=self.kwargs["project_pk"])

    def get_queryset(self):
        return Meeting.objects.filter(project=self.get_project())


class MeetingListView(MeetingMixin, ListView):
    """List all meetings for a project."""

    template_name = "site_management/meeting/list.html"
    context_object_name = "meetings"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["open_count"] = self.get_queryset().filter(status="OPEN").count()
        context["closed_count"] = self.get_queryset().filter(status="CLOSED").count()
        context["tab"] = "meetings"
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management",
                        kwargs={"pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title="Meetings", url=None),
        ]


class MeetingDetailView(MeetingMixin, DetailView):
    """View details of a meeting."""

    template_name = "site_management/meeting/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        # Get decisions with their linked actions
        context["decisions"] = self.object.meeting_decisions.prefetch_related(
            "decision_actions"
        ).all()
        # Get actions that are NOT linked to a specific decision (if any)
        context["unlinked_actions"] = self.object.meeting_actions.filter(
            decision__isnull=True
        )
        context["action_statuses"] = MeetingActionStatus.choices
        context["today"] = timezone.now().date()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management",
                        kwargs={"pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(
                title="Meetings",
                url=str(
                    reverse_lazy(
                        "site_management:meeting-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=str(self.get_object()), url=None),
        ]


class MeetingCreateView(MeetingMixin, CreateView):
    """Create a new meeting."""

    template_name = "site_management/meeting/form.html"
    fields = [
        "meeting_type",
        "other_meeting_type",
        "date",
        "key_decisions",
        "attachment",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = DateInput(attrs={"type": "date"})
        form.fields["key_decisions"].widget.attrs["placeholder"] = (
            "Summarise key decisions, actions, and outcomes from this meeting"
        )
        return form

    def form_valid(self, form):
        form.instance.project = self.get_project()
        response = super().form_valid(form)

        # Handle dynamic decisions and actions
        decisions_data = self.request.POST.get("decisions_data")
        decision_summaries = []
        if decisions_data:
            try:
                decisions = json.loads(decisions_data)
                for d_item in decisions:
                    desc = d_item.get("description")
                    if not desc:
                        continue

                    decision = MeetingDecision.objects.create(
                        meeting=self.object,
                        description=desc,
                        responsible_person=d_item.get("responsible_person", ""),
                        due_date=d_item.get("due_date")
                        if d_item.get("due_date")
                        else None,
                    )
                    decision_summaries.append(f"- {desc}")

                    # Create linked register items
                    link_type = d_item.get("link_type")
                    if link_type:
                        self._create_linked_register_item(decision, link_type)

                    # Handle actions for this decision
                    actions = d_item.get("actions", [])
                    for a_item in actions:
                        MeetingAction.objects.create(
                            meeting=self.object,
                            decision=decision,
                            description=a_item.get("description"),
                            assigned_to=a_item.get("assigned_to", ""),
                            due_date=a_item.get("due_date")
                            if a_item.get("due_date")
                            else None,
                        )
            except json.JSONDecodeError:
                pass

        # Handle general actions (unlinked)
        general_actions_data = self.request.POST.get("general_actions_data")
        if general_actions_data:
            try:
                general_actions = json.loads(general_actions_data)
                for a_item in general_actions:
                    MeetingAction.objects.create(
                        meeting=self.object,
                        description=a_item.get("description"),
                        assigned_to=a_item.get("assigned_to", ""),
                        due_date=a_item.get("due_date")
                        if a_item.get("due_date")
                        else None,
                    )
            except json.JSONDecodeError:
                pass

        # Update meeting summary if not explicitly provided
        obj = getattr(self, "object", None)
        existing_summary = (
            getattr(obj, "key_decisions", None) if obj is not None else None
        )
        if obj is not None and decision_summaries and not existing_summary:
            obj.key_decisions = "\n".join(decision_summaries)
            obj.save()

        messages.success(self.request, "Meeting record created successfully.")
        return response

    def _create_linked_register_item(self, decision, link_type):
        """Helper to create a draft record in an external register."""
        from app.SiteManagement.models import (
            RFI,
            EarlyWarning,
            NCRType,
            NonConformance,
            SiteInstruction,
        )

        project = decision.meeting.project
        meeting = decision.meeting
        meeting_display = (
            f"{meeting.get_meeting_type_display()} Meeting ({meeting.date})"
        )
        if meeting.meeting_type == "OTHER" and meeting.other_meeting_type:
            meeting_display = f"{meeting.other_meeting_type} Meeting ({meeting.date})"

        common_data = {
            "project": project,
            "source_decision": decision,
        }

        if link_type == "NCR_QUALITY":
            NonConformance.objects.create(
                **common_data,
                ncr_type=NCRType.QUALITY,
                description=f"Raised from {meeting_display}\nDecision: {decision.description}",
            )
        elif link_type == "NCR_SAFETY":
            NonConformance.objects.create(
                **common_data,
                ncr_type=NCRType.SAFETY,
                description=f"Raised from {meeting_display}\nDecision: {decision.description}",
            )
        elif link_type == "RFI":
            RFI.objects.create(
                **common_data,
                subject=f"RFI from {meeting_display}",
                message=decision.description,
                respond_by_date=decision.due_date
                if decision.due_date
                else timezone.now().date(),
            )
        elif link_type == "SI":
            SiteInstruction.objects.create(
                **common_data,
                subject=f"SI from {meeting_display}",
                instruction=decision.description,
            )
        elif link_type == "EW":
            EarlyWarning.objects.create(
                **common_data,
                subject=f"EW from {meeting_display}",
                message=decision.description,
                respond_by_date=decision.due_date
                if decision.due_date
                else timezone.now().date(),
            )

    def get_success_url(self):
        project_pk = self.get_project().pk
        obj = getattr(self, "object", None)
        if obj is not None:
            return reverse_lazy(
                "site_management:meeting-detail",
                kwargs={"project_pk": project_pk, "pk": obj.pk},
            )
        return reverse_lazy(
            "site_management:meeting-list",
            kwargs={"project_pk": project_pk},
        )


class MeetingAddDecisionView(MeetingMixin, View):
    """Add a decision to a meeting."""

    def post(self, request, *args, **kwargs):
        meeting = get_object_or_404(
            Meeting, pk=kwargs["pk"], project__pk=kwargs["project_pk"]
        )
        description = request.POST.get("description")
        responsible_person = request.POST.get("responsible_person", "")
        due_date = request.POST.get("due_date")

        if description:
            MeetingDecision.objects.create(
                meeting=meeting,
                description=description,
                responsible_person=responsible_person,
                due_date=due_date if due_date else None,
            )
            messages.success(request, "Decision added successfully.")
        else:
            messages.error(request, "Decision description cannot be empty.")
        return redirect(
            "site_management:meeting-detail",
            project_pk=meeting.project.pk,
            pk=meeting.pk,
        )


class MeetingAddActionView(MeetingMixin, View):
    """Add an action item to a meeting."""

    def post(self, request, *args, **kwargs):
        meeting = get_object_or_404(
            Meeting, pk=kwargs["pk"], project__pk=kwargs["project_pk"]
        )
        description = request.POST.get("description")
        assigned_to = request.POST.get("assigned_to", "")
        due_date = request.POST.get("due_date")
        decision_id = request.POST.get("decision_id")

        if description:
            action_data = {
                "meeting": meeting,
                "description": description,
                "assigned_to": assigned_to,
                "due_date": due_date if due_date else None,
            }

            if decision_id:
                action_data["decision_id"] = decision_id

            MeetingAction.objects.create(**action_data)
            messages.success(request, "Action added successfully.")
        else:
            messages.error(request, "Action description cannot be empty.")

        return redirect(
            "site_management:meeting-detail",
            project_pk=kwargs["project_pk"],
            pk=kwargs["pk"],
        )


class MeetingUpdateActionStatusView(MeetingMixin, View):
    """Quickly update the status of an action."""

    def post(self, request, *args, **kwargs):
        action = get_object_or_404(
            MeetingAction, pk=kwargs["action_pk"], meeting__pk=kwargs["pk"]
        )
        new_status = request.POST.get("status")

        if new_status in MeetingActionStatus.values:
            action.status = new_status
            action.save()
            status_label = dict(MeetingActionStatus.choices).get(
                action.status, action.status
            )
            messages.success(request, f"Action status updated to {status_label}.")
        else:
            messages.error(request, "Invalid status.")

        return redirect(
            "site_management:meeting-detail",
            project_pk=kwargs["project_pk"],
            pk=kwargs["pk"],
        )


class MeetingUpdateView(MeetingMixin, UpdateView):
    """Update a meeting."""

    template_name = "site_management/meeting/form.html"
    fields = [
        "meeting_type",
        "other_meeting_type",
        "date",
        "key_decisions",
        "attachment",
        "status",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["date"].widget = DateInput(attrs={"type": "date"})
        form.fields["key_decisions"].widget.attrs["placeholder"] = (
            "Summarise key decisions, actions, and outcomes from this meeting"
        )
        return form

    def form_valid(self, form):
        obj = form.save(commit=False)
        if obj.status == "CLOSED" and not obj.date_closed:
            obj.date_closed = timezone.now().date()
        elif obj.status == "OPEN":
            obj.date_closed = None
        obj.save()

        # Handle dynamic decisions and actions (same logic as CreateView)
        decisions_data = self.request.POST.get("decisions_data")
        if decisions_data:
            try:
                decisions = json.loads(decisions_data)
                for d_item in decisions:
                    desc = d_item.get("description")
                    if not desc:
                        continue

                    decision = MeetingDecision.objects.create(
                        meeting=self.object,
                        description=desc,
                        responsible_person=d_item.get("responsible_person", ""),
                        due_date=d_item.get("due_date")
                        if d_item.get("due_date")
                        else None,
                    )

                    # Create linked register items
                    link_type = d_item.get("link_type")
                    if link_type:
                        self._create_linked_register_item(decision, link_type)

                    # Handle actions for this decision
                    actions = d_item.get("actions", [])
                    for a_item in actions:
                        MeetingAction.objects.create(
                            meeting=self.object,
                            decision=decision,
                            description=a_item.get("description"),
                            assigned_to=a_item.get("assigned_to", ""),
                            due_date=a_item.get("due_date")
                            if a_item.get("due_date")
                            else None,
                        )
            except json.JSONDecodeError:
                pass

        # Handle general actions (unlinked)
        general_actions_data = self.request.POST.get("general_actions_data")
        if general_actions_data:
            try:
                general_actions = json.loads(general_actions_data)
                for a_item in general_actions:
                    MeetingAction.objects.create(
                        meeting=self.object,
                        description=a_item.get("description"),
                        assigned_to=a_item.get("assigned_to", ""),
                        due_date=a_item.get("due_date")
                        if a_item.get("due_date")
                        else None,
                    )
            except json.JSONDecodeError:
                pass

        messages.success(self.request, "Meeting record updated successfully.")
        return super().form_valid(form)

    def _create_linked_register_item(self, decision, link_type):
        """Helper to create a draft record in an external register."""
        from app.SiteManagement.models import (
            RFI,
            EarlyWarning,
            NCRType,
            NonConformance,
            SiteInstruction,
        )

        project = decision.meeting.project
        meeting = decision.meeting
        meeting_display = (
            f"{meeting.get_meeting_type_display()} Meeting ({meeting.date})"
        )
        if meeting.meeting_type == "OTHER" and meeting.other_meeting_type:
            meeting_display = f"{meeting.other_meeting_type} Meeting ({meeting.date})"

        common_data = {
            "project": project,
            "source_decision": decision,
        }

        if link_type == "NCR_QUALITY":
            NonConformance.objects.create(
                **common_data,
                ncr_type=NCRType.QUALITY,
                description=f"Raised from {meeting_display}\nDecision: {decision.description}",
            )
        elif link_type == "NCR_SAFETY":
            NonConformance.objects.create(
                **common_data,
                ncr_type=NCRType.SAFETY,
                description=f"Raised from {meeting_display}\nDecision: {decision.description}",
            )
        elif link_type == "RFI":
            RFI.objects.create(
                **common_data,
                subject=f"RFI from {meeting_display}",
                message=decision.description,
                respond_by_date=decision.due_date
                if decision.due_date
                else timezone.now().date(),
            )
        elif link_type == "SI":
            SiteInstruction.objects.create(
                **common_data,
                subject=f"SI from {meeting_display}",
                instruction=decision.description,
            )
        elif link_type == "EW":
            EarlyWarning.objects.create(
                **common_data,
                subject=f"EW from {meeting_display}",
                message=decision.description,
                respond_by_date=decision.due_date
                if decision.due_date
                else timezone.now().date(),
            )

    def get_success_url(self):
        return reverse_lazy(
            "site_management:meeting-detail",
            kwargs={"project_pk": self.get_project().pk, "pk": self.object.pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context

    def get_breadcrumbs(self) -> list[BreadcrumbItem]:
        project = self.get_project()
        return [
            BreadcrumbItem(
                title="Projects", url=str(reverse_lazy("project:project-list"))
            ),
            BreadcrumbItem(
                title=project.name,
                url=str(
                    reverse_lazy(
                        "project:project-management",
                        kwargs={"pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(
                title="Meetings",
                url=str(
                    reverse_lazy(
                        "site_management:meeting-list",
                        kwargs={"project_pk": project.pk},
                    )
                ),
            ),
            BreadcrumbItem(title=str(self.get_object()), url=None),
        ]


class MeetingDeleteView(MeetingMixin, DeleteView):
    """Delete a meeting."""

    template_name = "site_management/meeting/confirm_delete.html"

    def get_success_url(self):
        messages.success(self.request, "Meeting record deleted successfully.")
        return reverse_lazy(
            "site_management:meeting-list",
            kwargs={"project_pk": self.get_project().pk},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        return context
