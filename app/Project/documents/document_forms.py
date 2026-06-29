"""Forms for Project app."""

from django import forms

from app.Project.models import (
    Drawing,
    ProjectDocument,
)


class ProjectDocumentForm(forms.ModelForm):
    """Form for uploading project documents."""

    wbs_level = forms.ChoiceField(
        choices=[],
        required=False,
        label="WBS Level",
        widget=forms.Select(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
            }
        ),
        help_text="Select the WBS level this document belongs to",
    )

    class Meta:
        model = ProjectDocument
        fields = [
            "category",
            "title",
            "document_number",
            "revision_number",
            "file",
            "notes",
            "project_category",
            "area",
            "project_discipline",
        ]
        widgets = {
            "category": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Enter document title",
                }
            ),
            "document_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "e.g., DOC-101",
                }
            ),
            "revision_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "e.g., A or 01",
                }
            ),
            "file": forms.FileInput(
                attrs={
                    "class": "mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100",
                    "accept": ".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.zip",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "Optional notes about this document",
                    "rows": 3,
                }
            ),
            "project_category": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "area": forms.Select(
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
            "category": "Document Category",
            "title": "Document Title",
            "document_number": "Document Number",
            "revision_number": "Revision Number",
            "file": "File",
            "notes": "Notes (Optional)",
            "project_category": "Sector",
            "area": "Area",
            "project_discipline": "Discipline",
        }
        help_texts = {
            "document_number": "Unique identifier for the document",
            "revision_number": "Current revision number (e.g., A, 01, Rev 1)",
            "file": "Accepted formats: PDF, Word, Excel, Images, ZIP",
            "project_category": "Select the project sector",
            "area": "Select the project area (Municipality)",
            "project_discipline": "Select the discipline",
        }

    def __init__(self, *args, **kwargs):
        from app.Account.models import Municipality
        from app.Project.projects.projects_models import (
            Category,
            Discipline,
        )

        project = kwargs.pop("project", None)
        is_edit = kwargs.pop("is_edit", False)
        super().__init__(*args, **kwargs)

        # Make file field optional when editing
        if is_edit and self.instance and self.instance.pk:
            self.fields["file"].required = False
            self.fields["file"].help_text = "Leave empty to keep the current file"

        self.fields["project_discipline"].label = "Discipline"
        self.fields["project_discipline"].help_text = "Select the discipline"

        if project:
            # Filter categories, areas, and disciplines by project

            # Filter for project-specific categories
            category_field = self.fields["project_category"]
            if hasattr(category_field, "queryset"):
                category_field.queryset = Category.objects.filter(  # type: ignore
                    project_id=project.pk, deleted=False
                ).order_by("name")

            # Filter for project-specific areas
            area_field = self.fields["area"]
            if hasattr(area_field, "queryset"):
                area_field.queryset = Municipality.objects.filter(  # type: ignore
                    projects=project
                ).order_by("municipality_name")

            # Filter for project-specific disciplines
            discipline_field = self.fields["project_discipline"]
            if hasattr(discipline_field, "queryset"):
                discipline_field.queryset = Discipline.objects.filter(  # type: ignore
                    project_id=project.pk, deleted=False
                ).order_by("name")

            # Build hierarchical options for WBS Levels
            wbs_choices = [("", "---------")]
            categories = Category.objects.filter(
                project=project, deleted=False
            ).order_by("name")
            for cat in categories:
                wbs_choices.append((f"category_{cat.pk}", f"L1: {cat.name}"))
                subcategories = cat.subcategories.filter(deleted=False).order_by("name")
                for sub in subcategories:
                    wbs_choices.append((f"subcategory_{sub.pk}", f"  L2: {sub.name}"))
                    groups = sub.groups.filter(deleted=False).order_by("name")
                    for grp in groups:
                        wbs_choices.append((f"group_{grp.pk}", f"    L3: {grp.name}"))
            self.fields["wbs_level"].choices = wbs_choices

            # Set initial value for wbs_level when editing
            if self.instance and self.instance.pk:
                if self.instance.group_id:
                    self.initial["wbs_level"] = f"group_{self.instance.group_id}"
                elif self.instance.sub_category_id:
                    self.initial["wbs_level"] = (
                        f"subcategory_{self.instance.sub_category_id}"
                    )
                elif self.instance.project_category_id:
                    self.initial["wbs_level"] = (
                        f"category_{self.instance.project_category_id}"
                    )

            # Make fields optional
            self.fields["project_category"].required = False
            self.fields["area"].required = False
            self.fields["project_discipline"].required = False
            self.fields["document_number"].required = False
            self.fields["revision_number"].required = False

    def save(self, commit=True):
        from app.Project.projects.projects_models import Group, SubCategory

        instance = super().save(commit=False)
        wbs_level = self.cleaned_data.get("wbs_level")

        # Reset and resolve from WBS level selection
        instance.project_category = None
        instance.sub_category = None
        instance.group = None

        if wbs_level:
            level_type, level_id = wbs_level.split("_")
            if level_type == "category":
                instance.project_category_id = int(level_id)
            elif level_type == "subcategory":
                sub_cat = SubCategory.objects.filter(pk=level_id, deleted=False).first()
                if sub_cat:
                    instance.project_category = sub_cat.category
                    instance.sub_category = sub_cat
            elif level_type == "group":
                grp = Group.objects.filter(pk=level_id, deleted=False).first()
                if grp:
                    instance.group = grp
                    if grp.sub_category:
                        instance.sub_category = grp.sub_category
                        instance.project_category = grp.sub_category.category

        if commit:
            instance.save()
        return instance


class DrawingForm(forms.ModelForm):
    """Form for managing project drawings."""

    wbs_level = forms.ChoiceField(
        choices=[],
        required=False,
        label="WBS Level",
        widget=forms.Select(
            attrs={
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
            }
        ),
        help_text="Select the WBS level this drawing belongs to",
    )

    class Meta:
        model = Drawing
        fields = [
            "drawing_number",
            "name",
            "revision_number",
            "discipline",
            "category",
            "drawing_type",
            "file",
            "notes",
        ]
        widgets = {
            "drawing_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "e.g., ARCH-101",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "e.g., Ground Floor Plan",
                }
            ),
            "revision_number": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "placeholder": "e.g., A or 01",
                }
            ),
            "discipline": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "drawing_type": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                }
            ),
            "file": forms.FileInput(
                attrs={
                    "class": "mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100",
                    "accept": ".pdf,.dwg,.dxf,.jpg,.jpeg,.png",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                    "rows": 3,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        from app.Project.projects.projects_models import (
            Category,
            Discipline,
            DrawingType,
        )

        project = kwargs.pop("project", None)
        super().__init__(*args, **kwargs)

        if not project and self.instance and getattr(self.instance, "project_id", None):
            project = self.instance.project

        if project:
            self.instance.project = project
            # Filter discipline and category by project
            self.fields["discipline"].queryset = Discipline.objects.filter(
                project=project, deleted=False
            ).order_by("name")
            self.fields["category"].queryset = Category.objects.filter(
                project=project, deleted=False
            ).order_by("name")

            # Filter drawing types by project
            self.fields["drawing_type"].queryset = DrawingType.objects.filter(
                project=project, deleted=False
            ).order_by("name")
            self.fields["drawing_type"].empty_label = "Select drawing type..."

            # Build hierarchical options for WBS Levels
            wbs_choices = [("", "---------")]
            categories = Category.objects.filter(
                project=project, deleted=False
            ).order_by("name")
            for cat in categories:
                wbs_choices.append((f"category_{cat.pk}", f"L1: {cat.name}"))
                subcategories = cat.subcategories.filter(deleted=False).order_by("name")
                for sub in subcategories:
                    wbs_choices.append((f"subcategory_{sub.pk}", f"  L2: {sub.name}"))
                    groups = sub.groups.filter(deleted=False).order_by("name")
                    for grp in groups:
                        wbs_choices.append((f"group_{grp.pk}", f"    L3: {grp.name}"))
            self.fields["wbs_level"].choices = wbs_choices

            # Set initial value for wbs_level when editing
            if self.instance and self.instance.pk:
                if self.instance.group_id:
                    self.initial["wbs_level"] = f"group_{self.instance.group_id}"
                elif self.instance.sub_category_id:
                    self.initial["wbs_level"] = (
                        f"subcategory_{self.instance.sub_category_id}"
                    )
                elif self.instance.category_id:
                    self.initial["wbs_level"] = f"category_{self.instance.category_id}"

        self.fields["category"].required = False
        self.fields["notes"].required = False
        self.fields["drawing_type"].required = False

    def save(self, commit=True):
        from app.Project.projects.projects_models import Group, SubCategory

        instance = super().save(commit=False)
        wbs_level = self.cleaned_data.get("wbs_level")

        # Reset and resolve from WBS level selection
        instance.category = self.cleaned_data.get("category")
        instance.sub_category = None
        instance.group = None

        if wbs_level:
            level_type, level_id = wbs_level.split("_")
            if level_type == "category":
                instance.category_id = int(level_id)
            elif level_type == "subcategory":
                sub_cat = SubCategory.objects.filter(pk=level_id, deleted=False).first()
                if sub_cat:
                    instance.category = sub_cat.category
                    instance.sub_category = sub_cat
            elif level_type == "group":
                grp = Group.objects.filter(pk=level_id, deleted=False).first()
                if grp:
                    instance.group = grp
                    if grp.sub_category:
                        instance.sub_category = grp.sub_category
                        instance.category = grp.sub_category.category

        if commit:
            instance.save()
        return instance
