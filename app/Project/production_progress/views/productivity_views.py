from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    TemplateView,
)

from app.Account.subscription_config import Subscription
from app.core.Utilities.mixins import BreadcrumbMixin
from app.core.Utilities.subscriptions import SubscriptionRequiredMixin
from app.Project.models import Project

from ..production_forms import (
    AggregatedLabourFormSet,
    DailyActivityReportForm,
    DailyPlantUsageFormSet,
    DailyProductionForm,
)
from ..production_models import (
    DailyActivityEntry,
    DailyActivityReport,
    DailyLabourUsage,
    DailyProduction,
    ProductionPlan,
    ProductionResource,
)


class DailyProductionCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, CreateView
):
    """Form to log daily quantities."""

    model = DailyProduction
    form_class = DailyProductionForm
    template_name = "production_progress/tracking/production_form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {"title": "Production Dashboard", "url": reverse_lazy("project:production-dashboard", kwargs={"project_pk": project_pk})},
            {"title": "Log Daily Quantities", "url": None},
        ]

    def get_success_url(self):
        return reverse_lazy(
            "project:production-dashboard",
            kwargs={"project_pk": self.kwargs["project_pk"]},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        return context

    def form_valid(self, form):
        form.instance.project_id = self.kwargs["project_pk"]
        return super().form_valid(form)


class DailyProductivityCreateView(
    SubscriptionRequiredMixin, LoginRequiredMixin, BreadcrumbMixin, TemplateView
):
    """View to handle the composite Daily Productivity Form."""

    template_name = "production_progress/tracking/productivity_form.html"
    required_tiers = [Subscription.PROFIT_AND_LOSS]

    def get_breadcrumbs(self):
        project_pk = self.kwargs["project_pk"]
        return [
            {"title": "Projects", "url": reverse_lazy("project:portfolio-dashboard")},
            {"title": "Production Dashboard", "url": reverse_lazy("project:production-dashboard", kwargs={"project_pk": project_pk})},
            {"title": "Daily Productivity Log", "url": None},
        ]

    def get_context_data(self, post_data=None, **kwargs):
        context = super().get_context_data(**kwargs)
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)
        context["project"] = project
        context["all_plans"] = ProductionPlan.objects.filter(
            project=project, is_archived=False
        )

        selected_plans_ids = self.request.POST.getlist("selected_plans")
        if not selected_plans_ids:
            selected_plans_ids = self.request.GET.getlist("selected_plans")

        selected_plans = (
            ProductionPlan.objects.filter(
                id__in=selected_plans_ids, project=project
            ).order_by("id")
            if selected_plans_ids
            else ProductionPlan.objects.none()
        )
        context["selected_plans"] = selected_plans
        context["selected_plans_ids"] = [
            int(sid) for sid in selected_plans_ids if str(sid).isdigit()
        ]

        plan_resources = {}
        plant_formsets = {}

        for plan in selected_plans:
            resources = ProductionResource.objects.filter(production_plan=plan)
            plan_resources[plan.id] = {
                "skilled": resources.filter(
                    resource_type="LABOUR", skill_type__name__icontains="skilled"
                ).exists(),
                "semi_skilled": resources.filter(
                    resource_type="LABOUR", skill_type__name__icontains="semi"
                ).exists(),
                "unskilled": resources.filter(
                    resource_type="LABOUR", skill_type__name__icontains="unskilled"
                ).exists(),
                "plant": resources.filter(resource_type="PLANT").exists(),
            }

            planned_plants = resources.filter(resource_type="PLANT")
            plant_initial = [
                {"resource": res.id, "number": int(res.number), "hours": 8.0}
                for res in planned_plants
            ]

            p_prefix = f"plant_{plan.id}"
            if post_data:
                p_formset = DailyPlantUsageFormSet(
                    post_data, prefix=p_prefix, form_kwargs={"activity_id": plan.id}
                )
            else:
                p_formset = DailyPlantUsageFormSet(
                    prefix=p_prefix,
                    initial=plant_initial,
                    form_kwargs={"activity_id": plan.id},
                )

            for f in p_formset.forms:
                f.fields["resource"].queryset = planned_plants
                f.fields["activity"].initial = plan.id
                f.fields["activity"].queryset = ProductionPlan.objects.filter(
                    id=plan.id
                )
            plant_formsets[plan.id] = p_formset

        context["plan_resources"] = plan_resources
        context["plant_formsets"] = plant_formsets

        labour_initial = [{"activity": plan.id} for plan in selected_plans]
        if post_data:
            labour_formset = AggregatedLabourFormSet(
                post_data, prefix="labour", form_kwargs={"project_id": project.id}
            )
        else:
            labour_formset = AggregatedLabourFormSet(
                prefix="labour",
                initial=labour_initial,
                form_kwargs={"project_id": project.id},
            )

        for form, plan in zip(labour_formset.forms, selected_plans, strict=False):
            form.fields["activity"].queryset = ProductionPlan.objects.filter(id=plan.id)
            res_info = plan_resources[plan.id]
            if not res_info["skilled"]:
                form.fields["skilled_number"].disabled = True
            if not res_info["semi_skilled"]:
                form.fields["semi_skilled_number"].disabled = True
            if not res_info["unskilled"]:
                form.fields["unskilled_number"].disabled = True

        context["labour_formset"] = labour_formset
        context["labour_forms_with_plans"] = list(
            zip(labour_formset.forms, selected_plans, strict=False)
        )
        context["plant_formset"] = next(
            iter(plant_formsets.values()), None
        ) or DailyPlantUsageFormSet(prefix="plant")

        if post_data:
            context["report_form"] = DailyActivityReportForm(post_data)
        else:
            context["report_form"] = DailyActivityReportForm(
                initial={"date": timezone.now().date()}
            )

        return context

    def post(self, request, *args, **kwargs):
        project_pk = self.kwargs["project_pk"]
        project = get_object_or_404(Project, pk=project_pk)

        report_form = DailyActivityReportForm(request.POST)
        labour_formset = AggregatedLabourFormSet(
            request.POST, prefix="labour", form_kwargs={"project_id": project.id}
        )

        selected_plans_ids = request.POST.getlist("selected_plans")
        selected_plans = ProductionPlan.objects.filter(
            id__in=selected_plans_ids, project=project
        ).order_by("id")
        plan_map = {str(p.id): p for p in selected_plans}

        for form in labour_formset.forms:
            act_id = form.data.get(
                f"labour-{form.prefix}-activity"
            ) or form.initial.get("activity")
            if str(act_id) in plan_map:
                form.fields["activity"].queryset = ProductionPlan.objects.filter(
                    id=act_id
                )

        plant_formsets = {}
        plant_valid = True
        for plan in selected_plans:
            p_prefix = f"plant_{plan.id}"
            if f"{p_prefix}-TOTAL_FORMS" not in request.POST:
                continue

            p_formset = DailyPlantUsageFormSet(
                request.POST, prefix=p_prefix, form_kwargs={"activity_id": plan.id}
            )

            planned_plants = ProductionResource.objects.filter(
                production_plan=plan, resource_type="PLANT"
            )
            for f in p_formset.forms:
                f.fields["resource"].queryset = planned_plants
                f.fields["activity"].queryset = ProductionPlan.objects.filter(
                    id=plan.id
                )

            plant_formsets[plan.id] = p_formset
            if not p_formset.is_valid():
                plant_valid = False

        if report_form.is_valid() and labour_formset.is_valid() and plant_valid:
            try:
                with transaction.atomic():
                    report, _ = DailyActivityReport.objects.get_or_create(
                        project=project, date=report_form.cleaned_data["date"]
                    )

                    entries = {}

                    for form in labour_formset:
                        if form.cleaned_data:
                            plan = form.cleaned_data["activity"]
                            entry, _ = DailyActivityEntry.objects.update_or_create(
                                report=report,
                                production_plan=plan,
                                defaults={
                                    "quantity": form.cleaned_data.get("quantity") or 0.0
                                },
                            )
                            entries[plan.id] = entry

                            entry.labour_usage.all().delete()

                            for name_part, number in [
                                ("skilled", form.cleaned_data.get("skilled_number")),
                                ("semi", form.cleaned_data.get("semi_skilled_number")),
                                (
                                    "unskilled",
                                    form.cleaned_data.get("unskilled_number"),
                                ),
                            ]:
                                if number and number > 0:
                                    res = ProductionResource.objects.filter(
                                        production_plan=plan,
                                        resource_type="LABOUR",
                                        skill_type__name__icontains=name_part,
                                    ).first()
                                    if res:
                                        DailyLabourUsage.objects.create(
                                            entry=entry,
                                            resource=res,
                                            number=number,
                                            hours=form.cleaned_data.get("total_hours")
                                            or 0.0,
                                        )

                    for plan_id, p_fs in plant_formsets.items():
                        entry = entries.get(plan_id)
                        if not entry:
                            plan = plan_map.get(str(plan_id))
                            entry, _ = DailyActivityEntry.objects.update_or_create(
                                report=report,
                                production_plan=plan,
                                defaults={"quantity": 0},
                            )
                            entries[plan_id] = entry

                        for p_form in p_fs:
                            if p_form.cleaned_data:
                                if p_form.cleaned_data.get("DELETE", False):
                                    if p_form.instance.pk:
                                        p_form.instance.delete()
                                else:
                                    usage = p_form.save(commit=False)
                                    usage.entry = entry
                                    usage.save()

                    messages.success(
                        request, "Daily productivity logs saved successfully."
                    )
                    return redirect(
                        "project:production-dashboard", project_pk=project_pk
                    )

            except Exception as e:
                messages.error(request, f"Error during save: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form.")

        context = self.get_context_data(post_data=request.POST)
        context.update(
            {
                "report_form": report_form,
                "labour_formset": labour_formset,
                "plant_formsets": plant_formsets,
            }
        )
        return self.render_to_response(context)
