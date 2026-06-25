import pytest

from app.Estimator.forms import SystemMunicipalityForm


@pytest.mark.django_db
def test_system_municipality_form_validation():
    from app.Account.tests.factories import ProvinceFactory
    province = ProvinceFactory(name="Gauteng")
    form_data = {
        "province": province.id,
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
    assert mun.province.name == "Western Cape"
    assert mun.municipality_name == "George Local Municipality"
    assert mun.district == "Garden Route"


@pytest.mark.django_db
def test_system_municipalities_views(client):
    from django.urls import reverse

    from app.Account.models import Municipality
    from app.Account.tests.factories import (
        ProvinceFactory,
        SuperuserFactory,
        UserFactory,
    )

    url = reverse("estimator:sys_municipalities")

    # Guest/Regular user redirected or denied
    user = UserFactory()
    client.force_login(user)
    response = client.get(url)
    assert response.status_code in (403, 302)

    # Staff user allowed
    admin = SuperuserFactory()
    client.force_login(admin)
    response = client.get(url)
    assert response.status_code == 200

    # Add a municipality
    prov = ProvinceFactory(name="Western Cape")
    post_data = {
        "province": prov.id,
        "municipality_name": "George Local Municipality",
        "code": "WC044",
        "district": "Garden Route",
    }
    response = client.post(url, data=post_data)
    assert response.status_code == 302  # Redirect on success
    assert Municipality.objects.filter(code="WC044").exists()


@pytest.mark.django_db
def test_tab_in_base_system(client):
    from django.urls import reverse

    from app.Account.tests.factories import SuperuserFactory

    admin = SuperuserFactory()
    client.force_login(admin)
    url = reverse("estimator:sys_trade_codes")
    response = client.get(url)
    assert response.status_code == 200
    assert b"/estimator/system/municipalities/" in response.content
    assert b"Municipalities" in response.content
    assert b"/estimator/system/provinces/" in response.content
    assert b"Provinces" in response.content


@pytest.mark.django_db
def test_system_province_views(client):
    from django.urls import reverse

    from app.Account.models import Province
    from app.Account.tests.factories import (
        SuperuserFactory,
        UserFactory,
    )

    url = reverse("estimator:sys_provinces")

    # Guest/Regular user redirected or denied
    user = UserFactory()
    client.force_login(user)
    response = client.get(url)
    assert response.status_code in (403, 302)

    # Staff user allowed
    admin = SuperuserFactory()
    client.force_login(admin)
    response = client.get(url)
    assert response.status_code == 200

    # Add a province
    post_data = {
        "name": "Gauteng",
        "code": "GP",
    }
    response = client.post(url, data=post_data)
    assert response.status_code == 302  # Redirect on success
    assert Province.objects.filter(code="GP").exists()


@pytest.mark.django_db
def test_load_default_provinces(client):
    from django.urls import reverse

    from app.Account.models import Province
    from app.Account.tests.factories import SuperuserFactory

    url = reverse("estimator:sys_provinces")
    admin = SuperuserFactory()
    client.force_login(admin)

    # Post load_defaults action
    response = client.post(url, data={"load_defaults": ""})
    assert response.status_code == 302
    assert Province.objects.count() == 9
    assert Province.objects.filter(name="Kwa-Zulu Natal").exists()


@pytest.mark.django_db
def test_load_default_municipalities(client):
    from django.urls import reverse

    from app.Account.models import Municipality, Province
    from app.Account.tests.factories import SuperuserFactory

    url = reverse("estimator:sys_municipalities")
    admin = SuperuserFactory()
    client.force_login(admin)

    # Post load_defaults action
    response = client.post(url, data={"load_defaults": ""})
    assert response.status_code == 302
    
    # Check that a sample of municipalities and provinces were created
    assert Municipality.objects.filter(code="WC025").exists()
    assert Municipality.objects.filter(code="NC092").exists()
    assert Municipality.objects.filter(code="EC441").exists()
    assert Municipality.objects.filter(code="FS205").exists()
    assert Municipality.objects.filter(code="GT421").exists()
    assert Municipality.objects.filter(code="KZN254").exists()
    assert Municipality.objects.filter(code="LIM351").exists()
    assert Municipality.objects.filter(code="MP325").exists()
    assert Municipality.objects.filter(code="NW374").exists()

    # Verify matching provinces exist and are correctly linked
    breede = Municipality.objects.get(code="WC025")
    assert breede.province.name == "Western Cape"
    assert breede.province.code == "WC"

