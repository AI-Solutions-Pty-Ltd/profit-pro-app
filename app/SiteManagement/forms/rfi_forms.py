"""Forms for RFI (Request for Information)."""

from django import forms

from app.SiteManagement.models.rfi import RFI


class RFIForm(forms.ModelForm):
    """Form for creating and updating RFIs."""

    class Meta:
        model = RFI
        fields = [
            "to_user",
            "subject",
            "message",
            "respond_by_date",
            "attachment",
            "project_category",
            "project_sub_category",
            "project_discipline",
        ]
        widgets = {
            "to_user": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "subject": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Brief subject of this request",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Detailed description or question requiring a response",
                    "rows": 4,
                }
            ),
            "respond_by_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "type": "date",
                }
            ),
            "attachment": forms.FileInput(
                attrs={
                    "class": "mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100",
                    "accept": ".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.zip",
                }
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
        }
        labels = {
            "to_user": "To",
            "subject": "Subject",
            "message": "Message",
            "respond_by_date": "Response Required By",
            "attachment": "Attachment",
            "project_category": "WBS Level 1",
            "project_sub_category": "WBS Level 2",
            "project_discipline": "WBS Level 3",
        }
        help_texts = {
            "attachment": "Optional: Attach any supporting documents",
            "project_category": "Select the WBS Level 1 classification",
            "project_sub_category": "Select the WBS Level 2 classification",
            "project_discipline": "Select the WBS Level 3 classification",
        }

    def __init__(self, *args, **kwargs):
        from app.Project.projects.projects_models import (
            Category,
            Discipline,
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
                    projects_id=project.pk, deleted=False
                ).order_by("name")

            # Filter for project-specific subcategories
            subcategory_field = self.fields["project_sub_category"]
            if hasattr(subcategory_field, "queryset"):
                subcategory_field.queryset = SubCategory.objects.filter(  # type: ignore[attr-defined]
                    project_id=project.pk, deleted=False
                ).order_by("name")

            # Filter for project-specific disciplines
            discipline_field = self.fields["project_discipline"]
            if hasattr(discipline_field, "queryset"):
                discipline_field.queryset = Discipline.objects.filter(  # type: ignore[attr-defined]
                    projects_id=project.pk, deleted=False
                ).order_by("name")

            # Make fields optional
            self.fields["project_category"].required = False
            self.fields["project_sub_category"].required = False
            self.fields["project_discipline"].required = False


class RFIResponseForm(forms.ModelForm):
    """Form for responding to an RFI."""

    class Meta:
        model = RFI
        fields = [
            "response",
            "response_attachment",
            "status",
        ]
        widgets = {
            "response": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter your response here",
                    "rows": 4,
                }
            ),
            "response_attachment": forms.FileInput(
                attrs={
                    "class": "mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100",
                    "accept": ".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.zip",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
        }
        labels = {
            "response": "Response",
            "response_attachment": "Response Attachment",
            "status": "Status",
        }
        help_texts = {
            "response_attachment": "Optional: Attach any supporting documents for your response",
        }
