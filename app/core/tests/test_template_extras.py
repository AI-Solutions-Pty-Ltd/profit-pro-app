import pytest
from decimal import Decimal
from app.core.templatetags.template_extras import space_intcomma

def test_space_intcomma_with_floats():
    assert space_intcomma(12345.67) == "12 345.67"
    assert space_intcomma(74593.31) == "74 593.31"
    assert space_intcomma(0.0) in ["0.00", "0.0"]

def test_space_intcomma_with_decimals():
    assert space_intcomma(Decimal("12345.67")) == "12 345.67"
    assert space_intcomma(Decimal("11189.00")) == "11 189.00"

def test_space_intcomma_with_strings():
    assert space_intcomma("12345.67") == "12 345.67"
    assert space_intcomma("12345") == "12 345"
    assert space_intcomma("-") == "-"
    assert space_intcomma(None) is None
    assert space_intcomma("") == ""
