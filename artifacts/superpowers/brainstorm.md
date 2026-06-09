# Brainstorm: Payment Certificate Detail — In-Browser Section Views

## Goal

Add **in-browser (HTML) view buttons** to the Payment Certificate detail page
(`bill-of-quantities/project/<pk>/payment-certificates/<pk>/detail/`) for three
document sections that currently only exist inside the downloaded PDF:

| Section | Description |
|---|---|
| **Cover Page** | Project details, contract summary, and payment certificate summary |
| **Valuation Summary** | Budget vs cumulative vs current-claim grouped by Structure -> Bill (valterra_rpm layout) |
| **Detailed Report** | The line-item table — full or abridged (claimed items only) |

Users will be able to choose between **Full** and **Abridged** variants of the
detailed page directly from the detail UI, without downloading a PDF.

## Constraints

- No new models or migrations required.
- Valuation Summary is only meaningful for valterra_rpm layout; guard with template check.
- Permission boundary unchanged — all new views inherit PaymentCertificateMixin.
- Must not break existing PDF download or async PDF generation.
- Factories/tests must use factory_boy; no raw Model.objects.create().

## Known context

### Existing PDF pipeline
- compile_pdf_for_certificate() in tasks.py
- layouts: standard and valterra_rpm
- front-page.html, 2-summary.html (valterra_rpm only), 2-line-items.html / 3-detailed.html

### Helper functions already available
- get_valuation_summary_data(payment_certificate) — tasks.py
- group_line_items_by_hierarchy(line_items) — tasks.py
- LineItem.abridged_payment_certificate(cert) — model manager
- LineItem.construct_payment_certificate(cert) — model manager

### What is missing today
- No browser view of cover page
- No browser view of valuation summary
- No browser view of detailed report (full vs abridged)
- No buttons for these in the detail page header

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Valuation summary shown on non-VALTERRA_RPM | Medium | Guard: return 404 or redirect for wrong layout |
| Large line-item tables cause slow browser render | Medium | Abridged limits to claimed items; full is opt-in |
| Duplicate context assembly | Low | Reuse existing helper functions directly |

## Options

### Option A — New dedicated view pages (recommended)

Three new CBV views:
- PaymentCertificateCoverPageView — .../cover-page/
- PaymentCertificateValuationSummaryView — .../valuation-summary/
- PaymentCertificateDetailedView — .../view-detailed/?mode=full|abridged

Four buttons added to detail page header.

Pros: Bookmarkable URLs, clean separation, easy to test, follows project conventions.
Cons: Three new templates needed.

### Option B — HTMX tab panels inside the detail page

Single URL; lazy-loaded tab panels via HTMX.

Pros: Single-page feel.
Cons: Codebase doesn't use HTMX for this pattern; harder to link to specific section.

### Option C — Reuse PDF HTML templates as inline iframes

Render existing PDF HTML inside iframes.

Pros: Zero new templates.
Cons: PDF print CSS looks bad in browser; complex to secure.

## Recommendation

**Option A — Dedicated view pages.**

Matches how the project is structured (Django CBV, one view per concern),
gives bookmarkable URLs, reuses all existing helper functions.

## Acceptance criteria

1. Cover Page view (/cover-page/) renders project details, contract summary, cert summary. Auth-guarded.
2. Valuation Summary view (/valuation-summary/) only accessible for valterra_rpm projects. Uses get_valuation_summary_data(). Returns 404 for wrong layout.
3. Detailed view (/view-detailed/?mode=full|abridged) shows full or abridged line items. Default = full.
4. Four new buttons on detail page: View Cover Page, Valuation Summary (conditional), View Detailed Full, View Detailed Abridged.
5. Tests in test_payment_certificate_section_views.py: 200/403 auth, valuation summary layout guard, abridged vs full queryset.
6. No regressions: existing tests pass, existing PDF download flow unchanged.
