### Goal
Restyle the Report Column Customization table using DaisyUI classes and standard Heroicon outline SVG icons.

### Assumptions
- DaisyUI is configured and loaded on the page.
- Pytest test suite runs correctly.

### Plan
1. Update HTML table, inputs, checkboxes, and buttons with DaisyUI styling in `report_config.html`.
2. Update SVG icons with Heroicons v2 outline coordinates and standard `stroke-width="1.5"`.
3. Verify changes with unit tests and manual visual checks.

### Risks & Mitigations
- None. DaisyUI is already active and tested on other pages in the app.

### Rollback plan
```bash
git checkout -- app/Project/templates/project/report_config.html
```
