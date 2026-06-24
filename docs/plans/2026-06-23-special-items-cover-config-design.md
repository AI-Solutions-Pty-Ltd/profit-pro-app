# Special Items Cover Config & Reports Design

This document details the design for integrating the custom ledger fields (`advance_payment`, `retention`, `material_on_site`, and `other_specify`) into the project's cover configuration and reports (both Excel and PDF formats).

## Background & Objectives
In the project cover page customization view, users can configure visibility, custom labels, and the order of four custom ledger fields:
1. Advance Payment (`advance_payment`)
2. Retention (`retention`)
3. Material on Site (`material_on_site`)
4. Other - Specify (`other_specify`)

However, the backend default configuration in the `Project` model and the view resolver (`get_resolved_cover_page_sections`), as well as the Excel exporter (`export_cover_page_to_xlsx`), did not support these fields, resulting in them not rendering.

The objective is to fully integrate these fields into the configuration database defaults, views, PDF compile logic, and Excel exporters.

## Proposed Design

### 1. Default Cover Page Configuration
Update `get_cover_page_config()` in `app/Project/projects/projects_models.py` to include these four custom ledger fields:
- `advance_payment` (label: "Advance payment", enabled: True)
- `retention` (label: "Retention", enabled: True)
- `material_on_site` (label: "Material on Site", enabled: True)
- `other_specify` (label: "Other - Specify", enabled: True)

### 2. View Resolver (`get_resolved_cover_page_sections`)
In `app/BillOfQuantities/views/payment_certificate_views.py`, update `get_resolved_cover_page_sections` to compute the raw values of:
- `advance_payment` = current certificate advance payment + previous advance payment
- `retention` = current certificate retention + previous retention
- `material_on_site` = current certificate material on site + previous material on site
- `other_specify` = current certificate special items of type `OTHER` + previous special items of type `OTHER`

Recalculate subsequent fields to mathematically incorporate these ledger items:
- `progressive_to_date` = `work_progressive_to_date + advance_payment + retention + material_on_site + other_specify`
- `progressive_previous` = `work_progressive_previous + ap_prev + ret_prev + mat_prev + other_prev`
- `current_claim_total` = `progressive_to_date - progressive_previous`
- `vat_now` = `current_claim_total * 0.15` (if VAT enabled)
- `total_certified` = `current_claim_total + vat_now`

### 3. Excel Exporter (`export_cover_page_to_xlsx`)
In `app/BillOfQuantities/exporters/cover_page_exporter.py`, apply the same value resolver and fields formatting logic. Render the rows in the same order as configured by the user.

## Verification Plan

### Automated Tests
- Add a new test case `test_cover_page_ledger_fields` in `app/BillOfQuantities/tests/test_exporters.py` to verify that when `advance_payment`, `retention`, `material_on_site`, and `other_specify` are enabled, they are correctly resolved, subtotaled, and exported to Excel and PDF.
