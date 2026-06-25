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


@pytest.mark.django_db
def test_municipality_importer(tmp_path):
    import os
    import openpyxl
    from app.Account.models import Municipality
    from app.Estimator.importers import MunicipalityImporter

    # Create simple excel sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Municipalities"
    ws.append(["Province", "Municipality Name", "Code", "District"])
    ws.append(["Western Cape", "George Local Municipality", "WC044", "Garden Route"])

    file_path = os.path.join(tmp_path, "test_mun.xlsx")
    wb.save(file_path)

    importer = MunicipalityImporter(file_path)
    result = importer.run()

    assert result["created"] == 1
    assert result["skipped"] == 0

    # Verify DB record
    mun = Municipality.objects.get(code="WC044")
    assert mun.province == "Western Cape"
    assert mun.municipality_name == "George Local Municipality"
    assert mun.district == "Garden Route"

