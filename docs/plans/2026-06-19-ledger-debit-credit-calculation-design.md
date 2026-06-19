# Design: Ledger Debit & Credit Calculations Correctness

## Status
Approved

## Problem
In `PaymentCertificate` model helper methods (such as `get_advance_payment_total()`, `get_retention_total()`, etc.) and their previous certificates property counterparts, values are summed using the absolute transaction `amount` field. This ignores the transaction type (`DEBIT` vs `CREDIT`), treating all recoveries or releases as positive additions rather than subtractions.

## Proposed Design
We will rewrite all current and previous total calculation methods for:
- Advance Payments
- Retention
- Materials on Site
- Escalation
- Special Items

For each calculation:
1. Filter the relevant queryset into debits (`transaction_type=DEBIT`).
2. Filter the relevant queryset into credits (`transaction_type=CREDIT`).
3. Subtract the sum of credits from the sum of debits using the existing `sum_queryset` utility.

## Affected Files
- `app/BillOfQuantities/models/payment_certificate_models.py`
