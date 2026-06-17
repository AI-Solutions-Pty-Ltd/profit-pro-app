## Goal
The goal is to implement robust, fully functional, and visually correct column reordering on the **Report Column Customization** page (`report_config.html`). The current page has template placeholders for Up/Down buttons under "ACTIONS", but they are not rendering correctly (showing an empty ACTIONS column in the UI) and need to be verified, fixed, and integrated.

## Constraints
1. **No External Dependencies**: Keep the solution lightweight and written in vanilla JavaScript without introducing heavy libraries unless necessary (SortableJS is used elsewhere in the codebase, but vanilla JS/HTML buttons are already outlined in the code).
2. **Backward Compatibility**: Column ordering must correctly update the JSON config saved in `project.column_config` and render correctly in both PDF exports and Excel reports.
3. **Tailwind / Styles**: Ensure styling is consistent with Tailwind CSS guidelines. The SVG elements must have robust rendering attributes so they don't collapse to 0x0.

## Known context
1. **Existing Page**: `app/Project/templates/project/report_config.html` has a table with `id="columns-config-table"` and a list container `id="columns-config-list"`.
2. **Current JS Implementation**:
   - `renderColumns()` generates row HTML including up/down buttons.
   - `moveColumn(idx, direction)` performs array element swapping and calls `renderColumns()` to refresh the view.
   - The form submits a JSON string containing the ordered array to `column-config-input`.
3. **Database Field**: `column_config` is stored as a JSONField on the `Project` model.
4. **Current Issue**: The "ACTIONS" column cells are rendering completely empty. This is likely due to the SVG elements collapsing or failing to render due to missing `width` and `height` attributes in raw HTML, styling class mismatches, or layout properties hiding the buttons.

## Risks
1. **SVG Collapsing / Visibility Issue**: In some environments, SVG tags without explicit `width` and `height` properties fail to render or collapse when dynamically injected via JS, resulting in a blank ACTIONS column.
   * *Mitigation*: Specify explicit `width="16" height="16"` attributes and proper classes on the `<svg>` tags.
2. **JavaScript State Desynchronization**: Rearranging the column list could cause input elements (like custom label texts) to lose focus or state during re-rendering if not handled carefully.
   * *Mitigation*: Ensure event listeners and data binding preserve the custom labels before re-rendering. (The current script does this by updating `col.label = this.value` on the input event).
3. **Index Boundary Errors**: Moving the first item up or the last item down must be safely prevented or disabled.
   * *Mitigation*: Correctly assign the `disabled` attribute to the Up button when `idx === 0` and the Down button when `idx === columns.length - 1`.

## Options (2–4)

### Option 1: Fix and Polish arrow-based Vanilla JS Reordering (Recommended)
Keep the existing arrow buttons, but make them robust.
- Add explicit `width="16" height="16"` attributes to the SVG tags.
- Update icon paths to standard Heroicons SVG chevron icons.
- Improve button styles to include proper Tailwind hover/active feedback.
* **Pros**:
  - Requires minimal changes; aligns with the text on the page: *"Use Up/Down buttons to reorder"*.
  - Fully compatible with the existing backend JSON saving logic.
* **Cons**:
  - Relies on button clicks instead of modern drag-and-drop.

### Option 2: Drag-and-Drop Reordering using SortableJS
Integrate SortableJS (already used in the project's item library) to support fluid drag-and-drop ordering.
* **Pros**:
  - Modern, intuitive user experience.
* **Cons**:
  - Higher styling overhead.
  - Requires importing/loading SortableJS script in this template.
  - Diverges from the instruction text *"Use Up/Down buttons to reorder"*.

## Recommendation
We recommend **Option 1**. It fixes the layout bug directly, maintains the intended design language, has zero additional dependencies, and is the most robust and secure approach.

## Acceptance criteria
1. **UI Visibility**: The Up/Down buttons must be clearly visible and correctly styled in the ACTIONS column of the Column Heading Customization table.
2. **Functional Ordering**:
   - Clicking "Up" on a row moves it up by one position, updating the order number, inputs, and the real-time preview table.
   - Clicking "Down" on a row moves it down by one position.
   - The first row's "Up" button and the last row's "Down" button must be disabled.
3. **State Integrity**:
   - Custom labels typed by the user must be preserved when columns are reordered.
   - Show/hide checkbox states must be preserved when columns are reordered.
4. **Data Persistence**: Clicking the "Save Report Configuration" button successfully submits the updated order, which is correctly saved in the database and applied to the PDF/Excel exports.
