ACTION ITEMS

SCOPE PLANNING

1. [DONE] Replace sub-title ‘Manyama Engineering Phase – Milestone Tracking’ with ‘Manyama Engineering Phase – Scope Planning’
2. [DONE] Remove the ‘Add Milestone’ button on the top right
3. [DONE] Replace ‘WBS Hierarchy’ with ‘Work Breakdown Structure and Timelines’
4. [DONE ]Add ability for attaching a document to each level.
5. After adding L2/L3 items, the cursor should remain on the item added so one can see it. It currently shows L1 and one cannot see the added item.

BUDGET FORECAST

1. Replace the tab name ‘Budget Forecast’ with ‘Cost Planning’
2. Change heading ‘Budget’ to ‘Cost Planning’
3. Have the following cost fields:
   a. Total Cost
   b. Supply Only
   c. Install Only
   d. Preliminaries
4. Add the ability to attach a cost estimate backup to each level.

DESIGN DEVELOPMENT

1. Remove ‘Overview’ from the heading
2. Please restore the ability to add drawings, design criteria and documents to each level
3. Error 404 appears when one clicks of the attachment

PROCUREMENT PACKAGES

1. Remove ‘Overview’ from the heading
2. Change subheading to ‘Package Timelines’
3. Add ‘Close Out’ stage after ‘Execution’ stage
4. Also add before documentation stage, start and finish dates for ‘Package Breakdown Structure’ with a place for its attachment.
5. The view button in the Procurement Package shows confusing details not relevant to the tab. Please remove these and let it show only what is relevant as we would typically see when we click the edit button.

TENDER DOCUMENTATION

1. Remove ‘Overview’ from the heading
2. Replace the View button with a collapse button
3. One collapsed, we should see the package overall %completion
4. The cancel button, back button and upload buttons links to a wrong page

TENDER PROCESS

1. Remove ‘Overview’ from the heading
2. Replace ‘Applied to Advert Completed’ with ‘Advert Completed’
3. Replace the View button with a collapse button
4. One collapsed, we should see the package overall %completion
5. The cancel button, back button and upload buttons links to a wrong page

E-PROCUREMENT

1. Move the E-Procurement Tab to below ‘Tender Process’ as an additional Tab to Planning and Procurement

GENERAL FEEDBACK

1. When editing the WBS elements - The cancel button does not work
2. Fix the back and forward buttons to the correct ones. It currently goes back to setup instead of Project Management Page
3. Each Tab is referred to as ‘Time Forecast’ instead of its correct name
4. Rename ‘Category’. ‘Subcategory’, and ‘Group’ to ‘WBS Level 1, 2 & 3’ respectively
5. Collapse of items
   a. In addition to the individual WBS level collapse buttons, may we have grouping buttons or filters at the top that enable us to show the different levels
   b. We need to be able to see the entire WBS so we can see if there are missing scope items, budgets or designs.
   c. We need the collapse buttons to the following Tabs also:
   i. Tender Documentation
   ii. Tender Process
6. Link Discipline to Levels
   a. We need the ability to discipline to each level 1 and the lowest level (2 or 3)
   b. I think discipline should be set in the setup and added as dropdowns to the respective levels.

ESTIMATOR PERFORMANCE

1. [DONE] Apply the lazy-options pattern to plant + labour spec def pages (project + system equivalents).
2. [DONE] Material Calculator N+1 — dropped overriding `.select_related("material")` in view loop and in model `components` / `rate_per_unit` properties so prefetch is reused. Verified 3 queries for the page regardless of spec count.
3. [DONE] Pagination — added `paginate_by = 50` to the six spec ListViews (project + system × material/labour/plant), shared `_pagination.html` partial, `query_params` helper preserves filters across page nav. Calculator TemplateViews skipped for now (filters mitigate; lazy-options + N+1 fixes already help). Output BoQ tracked separately in #4.
4. Output BoQ (Project Estimator dashboard) — biggest stress page (~2000 rows × 16 cols × inline editors). Pagination or virtual scrolling here likely matters most for power users.
5. Reports (material_components_list, plant_components_list, etc.) — currently aggregate over all BOQ items in Python. Push the aggregation into the DB with `.values().annotate(Sum())` for larger projects.
6. Composite indexes (only when data grows further):
   a. BOQItem(project_id, is_section_header, specification_id) — covers the dominant filter combo
   b. BOQItem(project_id, section) — only if section filtering becomes hot
   Skip for now — current single-column FK indexes are sufficient at present row counts.
