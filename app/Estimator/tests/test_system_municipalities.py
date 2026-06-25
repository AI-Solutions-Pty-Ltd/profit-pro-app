import pytest
from app.Estimator.forms import SystemMunicipalityForm

def test_system_municipality_form_validation():
    form_data = {
        "province": "Gauteng",
        "municipality_name": "City of Johannesburg",
        "code": "COJ",
        "district": "Johannesburg",
    }
    form = SystemMunicipalityForm(data=form_data)
    assert form.is_valid()
