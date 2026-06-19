# Superpowers Brainstorm: Contractual Special Items Integration

## Goal
The goal is to group **Addendum Line Items**, **Special Items**, and **Ledger Totals Summary Items** into a single table with the heading **"Contractual Special Items"**. This table will have four columns:
1. **Description**
2. **Previous Amount**
3. **Current Amount**
4. **Total Amount**

It will also include subtotals for each of the three item types (Addendum, Special, Ledger Totals) and a grand total. This unified table needs to be integrated across:
- **Valuation Summary Page** (`valuation_summary.html`)
- **Detailed Report Page** (`view_detailed.html`)
- **Main Payment Certificate Detail Page** (`payment_certificate_detail.html`)
- **PDF Payment Certificate** (`1-front-page.html` cover and `3-detailed.html` report)
- **Excel Detailed Report Exporter** (`detailed_report_exporter.py`)
- **Excel Summary Report Exporter** (`summary_report_exporter.py`)

## Constraints
- The table columns must be exactly: **Description**, **Previous Amount**, **Current Amount**, and **Total Amount**.
- The table must include clear subtotals for each group and a grand total.
- The calculations must be mathematically correct and consistent across all pages and export files.
- The styling must match the premium design system (Inter font, neutral colors, gold highlights where applicable, clean grid lines).

## Known context
- **Addendum items** are `LineItem` instances where `addendum=True` and `special_item=False`.
- **Special items** are `LineItem` instances where `special_item=True` and `addendum=False`.
- **Ledger Totals Summary items** are:
  - Advance Payments
  - Retention
  - Materials on Site
  - Escalation
  - Other Special Item Transactions (from `SpecialItemTransaction` grouped by type).
- We already have properties and tasks/methods on the `PaymentCertificate` model to retrieve these quantities and totals.

## Risks
- **Rounding / Sign alignment**: Ledger adjustments have debit/credit signs, but are typically displayed in absolute values, while their subtotals are signed net sums. We need to be careful to ensure that the math adds up correctly.
- **Valuation Summary layout**: The valuation summary page has columns for BOQ structure/bill values. Adding a separate table for Contractual Special Items requires clean positioning and accurate grand totals.
- **Export files consistency**: Exporters (Excel detailed report, Excel summary report, PDF template compiler) need to mirror the combined structure exactly so that exported values match what is seen on the screen.

## Options (2–4)
- **Option 1 (Recommended)**: Create a reusable template partial `contractual_special_items.html` for Django views. This template renders a single table with three main sections (Addendum, Special, Ledger) using the four requested columns, computing subtotals for each section, and displaying a grand total. Integrate this template into `payment_certificate_detail.html`, `view_detailed.html`, and `valuation_summary.html`. Rebuild PDF templates and Excel exporters to render this same structure.
- **Option 2**: Individually code the tables on each page without a shared template partial. This is highly redundant and increases the risk of inconsistencies in calculations or design.

## Recommendation
We recommend **Option 1**. Using a shared template partial ensures perfect design and calculation consistency across the three in-app views, while modifying the PDF/Excel exporters ensures the exported reports are completely aligned with the UI.

## Acceptance criteria
- A single "Contractual Special Items" table is shown on the Valuation Summary, View Detailed, and Detail pages.
- The table contains three sections: Addendum Line Items, Special Items, and Ledger Totals.
- Each section lists individual items with their Description, Previous Amount, Current Amount, and Total Amount.
- Each section displays a subtotal row.
- The bottom of the table displays the grand total for all contractual special items.
- The PDF Detailed Report renders this combined table in the same format.
- The Excel Detailed Report exports this combined table on a dedicated "Special Items" (or "Contractual Special Items") sheet.
- The Excel Valuation Summary includes this table below the main BOQ summary.
- All unit and integration tests compile and pass.
