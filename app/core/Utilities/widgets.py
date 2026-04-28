from django import forms


class SearchableSelectWidget(forms.Widget):
    """
    A custom searchable select widget with dynamic filtering and optional "Quick Create" button.
    Inherits from forms.Widget (instead of forms.Select) to prevent Crispy Forms
    from bypassing our custom template rendering.
    """

    template_name = "widgets/searchable_select_widget.html"

    def __init__(
        self,
        attrs=None,
        choices=(),
        create_url=None,
        resource_type=None,
        choice_data=None,
    ):
        """
        Initialize the widget.

        Args:
            attrs: Optional dictionary of attributes.
            choices: Optional list of choices.
            create_url: Optional boolean or URL string to enable the "Quick Create" button.
            resource_type: Optional slug for dynamic modal loading.
            choice_data: Optional dict mapping choice IDs to data attributes (e.g., {'1': {'data-rate': '100'}}).
        """
        super().__init__(attrs)
        self.choices = choices
        self.create_url = create_url
        self.resource_type = resource_type
        self.choice_data = choice_data or {}

    def get_context(self, name, value, attrs):
        """
        Add custom data and mimic choice grouping for the custom template.
        """
        context = super().get_context(name, value, attrs)
        context["widget"]["create_url"] = self.create_url
        context["widget"]["resource_type"] = self.resource_type
        context["widget"]["choice_data"] = self.choice_data

        # Manually generate optgroups similar to ChoiceWidget
        # This allows our template to iterate through choices as it expects
        search_val = (
            str(value[0]) if isinstance(value, (list, tuple)) else str(value or "")
        )

        # Normalize choices to groups
        groups = []
        for i, (val, label) in enumerate(self.choices):
            if isinstance(label, (list, tuple)):
                # Grouped choices
                group_name, group_choices = val, label
                options = []
                for sub_val, sub_label in group_choices:
                    options.append(
                        {
                            "name": name,
                            "value": sub_val,
                            "label": sub_label,
                            "selected": str(sub_val) == search_val,
                            "index": str(i),
                            "data": self.choice_data.get(str(sub_val), {}),
                        }
                    )
                groups.append((group_name, options, i))
            else:
                # Flat choices
                # Check if we already have a main flat group or create one
                if not groups or groups[0][0] is not None:
                    groups.insert(0, (None, [], i))
                groups[0][1].append(
                    {
                        "name": name,
                        "value": val,
                        "label": label,
                        "selected": str(val) == search_val,
                        "index": str(i),
                        "data": self.choice_data.get(str(val), {}),
                    }
                )

        context["widget"]["optgroups"] = groups

        # Pre-calculate the selected label for the button display
        selected_label = None
        for _, options, _ in groups:
            for option in options:
                if option["selected"]:
                    selected_label = option["label"]
                    break
            if selected_label:
                break

        context["widget"]["selected_label"] = selected_label
        return context

    class Media:
        js = ("js/searchable_select.js",)
