"""URL configuration for BillOfQuantities/Contracts Management app."""

from django.urls import path

from .addendum_urls import addendum_urls
from .api_urls import api_urls
from .contract_urls import contract_urls
from .correspondence_urls import correspondence_urls
from .final_account_urls import final_account_urls
from .forecast_urls import forecast_urls
from .ledger_urls import ledger_urls
from .payment_certificate_payment_urls import payment_certificate_payment_urls
from .payment_certificate_urls import payment_certificate_urls
from .special_item_urls import special_item_urls
from .structure_urls import structure_urls

app_name = "bill_of_quantities"

urlpatterns = (
    structure_urls
    + addendum_urls
    + api_urls
    + contract_urls
    + correspondence_urls
    + forecast_urls
    + final_account_urls
    # + ledger_urls  # escalation, special, materials, retention, advance payments
    + payment_certificate_payment_urls
    + payment_certificate_urls
    + special_item_urls
)
