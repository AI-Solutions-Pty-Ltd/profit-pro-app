from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercaseValidator:
    """Validate that the password contains at least one uppercase letter."""

    def validate(self, password, user=None):
        if not any(char.isupper() for char in password):
            raise ValidationError(
                _("This password must contain at least one uppercase letter."),
                code="password_no_uppercase",
            )

    def get_help_text(self):
        return _("Your password must contain at least one uppercase letter.")


class LowercaseValidator:
    """Validate that the password contains at least one lowercase letter."""

    def validate(self, password, user=None):
        if not any(char.islower() for char in password):
            raise ValidationError(
                _("This password must contain at least one lowercase letter."),
                code="password_no_lowercase",
            )

    def get_help_text(self):
        return _("Your password must contain at least one lowercase letter.")


# ELM validators
def validate_elm_length(number):
    pass


def validate_elm_numeric(number):
    pass


# Meter validators
def validate_meter_length(number):
    pass


def validate_meter_alphanumeric(number):
    pass


# Water meter validators
def validate_water_meter_format(number):
    pass


# Postcode validators
def validate_postcode_length(number):
    pass
