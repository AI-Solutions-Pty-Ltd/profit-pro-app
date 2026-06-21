# Brainstorming: Negative Sign for Items with "Less" Indicators

## Goal
Ensure that any number value (HTML cover page, compiled PDF report, exported Excel spreadsheet, and the Live Cover Page Preview mockup) that corresponds to an item with a "less" indicator (e.g. label containing "less" case-insensitively) is formatted and displayed as a negative value (prefixed with a negative sign).

## Constraints
- **Dynamic Scan**: Scans the item's label string dynamically (case-insensitively) for `"less"` to support both standard defaults and custom user labels.
- **Presentation-Layer Only**: Keeps database calculations intact; negations must only apply to the presentation/export layer.
- **Clean Formatting**: Renders negative currency as `-R X,XXX.XX` instead of `R -X,XXX.XX` for correct South African Rand representation.

## Known context
- Values are resolved via `get_resolved_cover_page_sections` in `payment_certificate_views.py`.
- Excel values are exported via `export_cover_page_to_xlsx` in `cover_page_exporter.py`.
- JS preview mockup uses `renderSectionMock` inside `cover_config.html`.

## Risks
- **Double Negation**: If a special item is already negative (value `< 0`) and has a label starting with "LESS:", negating it again could make it positive.
  - *Mitigation*: Ensure the negation logic only applies to strictly positive numeric values (`val > 0`).

## Options (2–4)

### Option 1: Dynamic Label Scan & Value Negation (Recommended)
Add a presentation-layer check for all views (Python resolution, Excel exporter, and JS mockup). If the item's label contains the substring `"less"` (case-insensitive) and the numeric value is positive, negate it.
- **Pros**: Flexible, robust, handles user-customized labels, and works identically across all formats.
- **Cons**: Requires adding string checks on labels in Python, Excel exporter, and JS.

### Option 2: Hardcoded Field ID Negation
Specifically target field IDs that represent deductions (e.g. `progressive_previous`) and negate them.
- **Pros**: Direct and simple.
- **Cons**: Does not support user customizations (e.g., if a user renames `amendments_value` to `Omissions (Less)` or if a custom special item is added).

## Recommendation
**Option 1** is recommended because it is flexible, matches the user's description, and handles custom labels seamlessly.

## Acceptance criteria
1. **HTML & PDF views**: Values for fields containing "less" (case-insensitive) in the label (like "LESS: Previous Amount Due") render with a negative sign (e.g. `-R 900,000.00`).
2. **Excel Exporter**: Output cell values for fields with "less" indicators are exported as negative numbers (e.g. `-900000.00`) and styled correctly in openpyxl.
3. **Live UI Preview**: The mockup canvas on the configuration page displays the mockup numbers with a negative sign (e.g. `-R 900,000.00`) when the label contains "less".
4. **Safety**: Existing negative numbers (like special item deductions) remain negative and are not double-negated.
