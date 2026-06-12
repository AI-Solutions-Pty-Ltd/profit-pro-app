## Goal
Refactor the report configuration UI to improve the card inputs for layout selection and introduce a "Preview" button that opens a native print dialog to showcase the structure of the selected report layout.

## Constraints
- Must align with the existing Django templates, Crispy Forms, and Tailwind CSS stack.
- The preview must accurately reflect the structure of the selected report layout without needing full actual data (placeholder data is acceptable).
- The print dialog preview should format well for printing (e.g., using @media print CSS where needed).

## Known context
- The application is a Django app called Profit Pro.
- The UI contains a "Report Layout Style" selector, a visual layout preview card, a column configuration table, and a real-time column header preview.
- The user wants to refactor the card inputs (likely making the layout cards more modular, responsive, or standardized) and add a preview capability via a print dialog.

## Risks
- Refactoring existing card inputs might break the current real-time HTMX or Javascript interactions for the previews.
- Generating a realistic print layout directly from the configuration page might be complex if it requires rendering a separate view just for the preview.
- Browser inconsistencies with window.print() behavior.

## Options (2?4)
1.  **Option 1: Hidden Iframe Print.** Refactor the UI components. Add a "Preview" button that fetches the report HTML via an endpoint, loads it into a hidden iframe, and calls iframe.contentWindow.print().
2.  **Option 2: New Tab Print.** Add a "Preview" button that opens a new browser tab with the report preview layout and immediately executes window.print() upon load.
3.  **Option 3: In-page Modal Preview.** Refactor the cards and add a "Preview" button that opens a modal within the page showing the report structure, with a secondary "Print" button inside the modal that triggers the print dialog.

## Recommendation
**Option 2 (New Tab Print)** is the most robust and easiest to implement for print previews. It provides a clean, isolated environment for print CSS without interfering with the complex configuration page. The refactoring of the card inputs should focus on creating reusable Django template inclusions with standard Tailwind utility classes.

## Acceptance criteria
1. The card inputs for report selection are refactored for better maintainability and visual consistency.
2. A new "Preview" button is added to the UI.
3. Clicking the "Preview" button successfully opens a print dialog.
4. The print preview accurately displays the structural layout of the selected report style.
