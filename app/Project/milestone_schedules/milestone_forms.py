"""Forms for Project app."""

from django import forms

from app.Project.models import (
    Milestone,
)


class MilestoneForm(forms.ModelForm):
    """Form for creating and updating milestones."""

    class Meta:
        model = Milestone
        fields = [
            "name",
            "project_category",
            "project_category_start_date",
            "project_category_end_date",
            "project_sub_category",
            "project_sub_category_start_date",
            "project_sub_category_end_date",
            "project_group",
            "project_group_start_date",
            "project_group_end_date",
            "project_discipline",
            "project_discipline_start_date",
            "project_discipline_end_date",
            "planned_date",
            "forecast_date",
            "reason_for_change",
            "sequence",
            "is_completed",
            "actual_date",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter milestone name",
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "end_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "planned_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "forecast_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "reason_for_change": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter reason for change in forecast date",
                    "rows": 3,
                }
            ),
            "sequence": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "min": "0",
                }
            ),
            "is_completed": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded",
                }
            ),
            "actual_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "project_category": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "project_sub_category": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "project_discipline": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "project_group": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "project_category_start_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "project_category_end_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "project_sub_category_start_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "project_sub_category_end_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "project_group_start_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "project_group_end_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "project_discipline_start_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
            "project_discipline_end_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),
        }
        labels = {
            "name": "Milestone Name",
            "project_category": "WBS Level 1",
            "project_category_start_date": "L1 Start Date",
            "project_category_end_date": "L1 End Date",
            "project_sub_category": "WBS Level 2",
            "project_sub_category_start_date": "L2 Start Date",
            "project_sub_category_end_date": "L2 End Date",
            "project_group": "WBS Level 3 - Group",
            "project_group_start_date": "L3 Start Date",
            "project_group_end_date": "L3 End Date",
            "project_discipline": "Discipline",
            "project_discipline_start_date": "Discipline Start Date",
            "project_discipline_end_date": "Discipline End Date",
            "start_date": "Start Date",
            "end_date": "End Date",
            "planned_date": "Planned Date (Baseline)",
            "forecast_date": "Forecast Date",
            "reason_for_change": "Reason for Change",
            "sequence": "Order/Sequence",
            "is_completed": "Completed",
            "actual_date": "Actual Completion Date",
        }
        help_texts = {
            "project_category": "Select the WBS Level 1 classification",
            "project_category_start_date": "Start date for WBS Level 1",
            "project_category_end_date": "End date for WBS Level 1",
            "project_sub_category": "Select the WBS Level 2 classification",
            "project_sub_category_start_date": "Start date for WBS Level 2",
            "project_sub_category_end_date": "End date for WBS Level 2",
            "project_group": "Select the WBS Level 3 Group classification",
            "project_group_start_date": "Start date for WBS Level 3 Group",
            "project_group_end_date": "End date for WBS Level 3 Group",
            "project_discipline": "Select the discipline classification",
            "project_discipline_start_date": "Start date for discipline",
            "project_discipline_end_date": "End date for discipline",
            "start_date": "Planned start date for this milestone",
            "end_date": "Planned end date for this milestone",
            "planned_date": "Original planned completion date",
            "forecast_date": "Current forecast completion date (leave blank if same as planned)",
            "reason_for_change": "Explain why the forecast date differs from the planned date",
            "sequence": "Order in which milestones should appear (0 = first)",
        }

    def clean(self):
        """Validate milestone dates."""
        cleaned_data = super().clean() or {}
        planned_date = cleaned_data.get("planned_date")
        forecast_date = cleaned_data.get("forecast_date")
        is_completed = cleaned_data.get("is_completed")
        actual_date = cleaned_data.get("actual_date")
        reason_for_change = cleaned_data.get("reason_for_change")

        # Require reason if forecast differs from planned
        if forecast_date and planned_date and forecast_date != planned_date:
            if not reason_for_change:
                self.add_error(
                    "reason_for_change",
                    "Reason is required when forecast date differs from planned date.",
                )

        # Require actual date if completed
        if is_completed and not actual_date:
            self.add_error(
                "actual_date",
                "Actual completion date is required when milestone is marked as completed.",
            )

        return cleaned_data

    def __init__(self, *args, **kwargs):
        from app.Project.projects.projects_models import (
            Category,
            Discipline,
            Group,
            SubCategory,
        )

        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        if project:
            # Filter categories, subcategories, and disciplines by project

            # Filter for project-specific categories
            category_field = self.fields["project_category"]
            if hasattr(category_field, "queryset"):
                category_field.queryset = Category.objects.filter(  # type: ignore[attr-defined]
                    project_id=project.pk, deleted=False
                ).order_by("name")

            # Filter for project-specific subcategories
            subcategory_field = self.fields["project_sub_category"]
            if hasattr(subcategory_field, "queryset"):
                subcategory_field.queryset = SubCategory.objects.filter(  # type: ignore[attr-defined]
                    project_id=project.pk, deleted=False
                ).order_by("name")

            # Filter for project-specific groups
            group_field = self.fields["project_group"]
            if hasattr(group_field, "queryset"):
                group_field.queryset = Group.objects.filter(  # type: ignore[attr-defined]
                    project_id=project.pk, deleted=False
                ).order_by("name")

            # Filter for project-specific disciplines
            discipline_field = self.fields["project_discipline"]
            if hasattr(discipline_field, "queryset"):
                discipline_field.queryset = Discipline.objects.filter(  # type: ignore[attr-defined]
                    project_id=project.pk, deleted=False
                ).order_by("name")

            # Make fields optional
            self.fields["project_category"].required = False
            self.fields["project_sub_category"].required = False
            self.fields["project_group"].required = False
            self.fields["project_discipline"].required = False
