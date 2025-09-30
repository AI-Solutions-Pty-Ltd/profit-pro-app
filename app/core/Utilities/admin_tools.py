import json

from django.db.models import JSONField
from django.forms import Textarea


class JSONPrettyWidget(Textarea):
    """Widget class for pretty JSON display."""

    def format_value(self, value):
        """Override the format_value method to pretty display the json."""
        if value:
            try:
                parsed = json.loads(value)
                pretty = json.dumps(parsed, indent=4, sort_keys=True)
                return pretty
            except json.JSONDecodeError:
                pass  # If it's not valid JSON, just return the original value
        return value


class AdminJSONMixin:
    """Django Admin Mixin class for pretty JSON display."""

    formfield_overrides = {
        JSONField: {"widget": JSONPrettyWidget},
    }
