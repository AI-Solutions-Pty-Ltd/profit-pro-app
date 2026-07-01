# PDF Number Formatting Design

## Goal
Format all currency values in the aggregated Valuation Summary PDF report with space separation for thousands (e.g., R 10 185 098.35) instead of unformatted float strings (e.g., R 10185098.35).

## Proposed Approach
Load the custom `template_extras` tag library and apply the `space_intcomma` filter to all values in the PDF template:
* File to modify: [valuation_summary_pdf.html](file:///c:/Users/nebst/Projects/profit-pro-app/app/Project/templates/portfolio/reports/valuation_summary_pdf.html)

## Design Details
1. Add `{% load template_extras %}` to the top of the template.
2. In the `<tbody>` loop for project rows, replace:
   - `R {{ row.contract_value|floatformat:2 }}` -> `R {{ row.contract_value|floatformat:2|space_intcomma }}`
   - `R {{ row.variations|floatformat:2 }}` -> `R {{ row.variations|floatformat:2|space_intcomma }}`
   - `R {{ row.revised_contract_value|floatformat:2 }}` -> `R {{ row.revised_contract_value|floatformat:2|space_intcomma }}`
   - `R {{ row.certified_previous|floatformat:2 }}` -> `R {{ row.certified_previous|floatformat:2|space_intcomma }}`
   - `R {{ row.certified_amount|floatformat:2 }}` -> `R {{ row.certified_amount|floatformat:2|space_intcomma }}`
   - `R {{ row.net_claimed|floatformat:2 }}` -> `R {{ row.net_claimed|floatformat:2|space_intcomma }}`
   - `R {{ row.forecast_amount|floatformat:2 }}` -> `R {{ row.forecast_amount|floatformat:2|space_intcomma }}`
   - `R {{ row.variance|floatformat:2 }}` -> `R {{ row.variance|floatformat:2|space_intcomma }}`
3. In the subtotal rows for province reports, replace:
   - `R {{ rep.budget|floatformat:2 }}` -> `R {{ rep.budget|floatformat:2|space_intcomma }}`
   - `R {{ rep.variations|floatformat:2 }}` -> `R {{ rep.variations|floatformat:2|space_intcomma }}`
   - `R {{ rep.revised|floatformat:2 }}` -> `R {{ rep.revised|floatformat:2|space_intcomma }}`
   - `R {{ rep.previous|floatformat:2 }}` -> `R {{ rep.previous|floatformat:2|space_intcomma }}`
   - `R {{ rep.cumulative|floatformat:2 }}` -> `R {{ rep.cumulative|floatformat:2|space_intcomma }}`
   - `R {{ rep.net|floatformat:2 }}` -> `R {{ rep.net|floatformat:2|space_intcomma }}`
   - `R {{ rep.forecast|floatformat:2 }}` -> `R {{ rep.forecast|floatformat:2|space_intcomma }}`
   - `R {{ rep.variance|floatformat:2 }}` -> `R {{ rep.variance|floatformat:2|space_intcomma }}`
4. In the `<tfoot>` totals row, replace:
   - `R {{ total_budget|floatformat:2 }}` -> `R {{ total_budget|floatformat:2|space_intcomma }}`
   - `R {{ total_variations|floatformat:2 }}` -> `R {{ total_variations|floatformat:2|space_intcomma }}`
   - `R {{ total_revised|floatformat:2 }}` -> `R {{ total_revised|floatformat:2|space_intcomma }}`
   - `R {{ total_previous|floatformat:2 }}` -> `R {{ total_previous|floatformat:2|space_intcomma }}`
   - `R {{ total_cumulative|floatformat:2 }}` -> `R {{ total_cumulative|floatformat:2|space_intcomma }}`
   - `R {{ total_current|floatformat:2 }}` -> `R {{ total_current|floatformat:2|space_intcomma }}`
   - `R {{ total_forecast|floatformat:2 }}` -> `R {{ total_forecast|floatformat:2|space_intcomma }}`
   - `R {{ total_variance|floatformat:2 }}` -> `R {{ total_variance|floatformat:2|space_intcomma }}`
