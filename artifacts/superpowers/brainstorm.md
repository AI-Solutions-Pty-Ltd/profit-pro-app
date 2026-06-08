## Goal
Implement a report selection and column configuration system in the Project Setup, allowing users to:
1. Select a default report layout style (Standard vs. Lephadimisha BOQ Report).
2. Preview their layout selection visually.
3. Rename, reorder, and customize the visibility of columns.
4. Download reports matching this configuration under a simplified "2-card" layout in the PDF/Excel download interface, with page selectors and dual PDF/Excel download options.

## Constraints
- **OS**: Windows environment.
- **Python Runtime**: Python 3.13+ within the `.venv` virtual environment.
- **Base Model Rules**: Any new database entities must inherit from `BaseModel`.
- **Testing Rules**: All test objects must be created using `factory_boy` factories.
- **Layout Fidelity**: The output reports must match the exact structures of `Lephadimisha_BOQ_Report.pdf` and `Lephadimisha_BOQ_Report .xlsx` when that layout is selected.

## Known context
- **Project Model**: Defined in `app/Project/projects/projects_models.py` with `certificate_layout` choices (`STANDARD`, `VALTERRA_RPM`).
- **PDF Generation Task**: In `app/BillOfQuantities/tasks.py` (`compile_pdf_for_certificate`), which uses HTML templates in `pdf_templates/`.
- **Excel Generation**: In `app/BillOfQuantities/exporters/excel_exporter.py` (`generate_payment_certificate_excel`), which generates sheets for Front, Summary, and detailed structures.
- **UI Details**: The current payment certificate detail page (`payment_certificate_detail.html`) renders 4 distinct download cards.

## Risks
1. **Broken Excel Formulas**: The Excel exporter currently writes formulas referencing hardcoded columns (e.g. `SUM(G{start}:G{end})`). If columns are reordered or disabled, the column letters (like G, I, K, M) change, which would break static references.
   *Mitigation*: Implement dynamic column letter resolution in `excel_exporter.py` based on the active sorted position of each enabled column.
2. **PDF Width Constraints**: Reordering or enabling too many columns could cause tables in the PDF to stretch or wrap awkwardly.
   *Mitigation*: Limit maximum columns or auto-scale widths based on visible columns using CSS flex/table sizing.
3. **Template Complexities**: Standard vs Valterra vs Lephadimisha templates must support the customizable column ordering and labels.
   *Mitigation*: Pass the resolved column structure from Django views into HTML templates and loop over columns dynamically.

## Options (2–4)
- **Option A (Recommended)**: 
  - Add `LEPHADIMISHA` choice to `certificate_layout` choices in `Project.CertificateLayout`.
  - Add a JSONField `column_config` to the `Project` model storing a list of column definitions: `[{'id': 'item_no', 'label': 'Item No.', 'enabled': True, 'order': 1}, ...]`.
  - Build a sleek, interactive drag-and-drop/sortable table interface using vanilla JS in the Setup tab, with a live mock table preview.
  - Update `compile_pdf_for_certificate` and `excel_exporter.py` to dynamically resolve active columns, labels, and Excel formula coordinate letters.
- **Option B**:
  - Define a separate model `ReportColumnConfig` linked to `Project` with fields for each column's name, ordering, and state.
  - While normalized, this increases DB queries and complicates test factory setup.
- **Option C**:
  - Implement predefined static layouts (Standard, RPM, Lephadimisha) without allowing reordering or renaming.
  - This is rejected because it fails to satisfy the user's explicit customization requirements.

## Recommendation
We recommend **Option A**. Storing the column config in a `JSONField` directly on the `Project` model is lightweight, easy to serialize/deserialize, keeps database queries to a minimum, and integrates cleanly with django-crispy-forms. It allows us to supply standard defaults and fallbacks when rendering, preventing breaking changes.

## Acceptance criteria
1. **Project Setup**:
   - A dedicated "Report Layout & Column Configuration" section in setup.
   - Layout selector (Standard vs Lephadimisha) with layout previews.
   - Interactive column configuration: reorder (drag/drop or up/down), rename, and toggle visibility.
   - Real-time live header preview showing custom names and order.
2. **Download Interface**:
   - "Download PDF Reports" screen shows exactly 2 cards: "Full Payment Certificate" and "Abridged Certificate".
   - Each card embeds checkboxes to select sections (Cover Page, Valuation Summary, Detailed Report) and has "Download PDF" and "Download Excel" buttons.
3. **Fidelity and Alignment**:
   - Downloaded PDFs/Excels reflect the selected layout, custom column headings, custom column order, and only show enabled columns.
   - Excel formulas evaluate correctly regardless of column order/existence.
4. **Validation**:
   - Existing unit and view tests pass, and new tests are written using factories to verify saving and rendering of configs.
