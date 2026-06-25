# Design: Reusable Project Configuration Navigation Tabs

Date: 2026-06-25

## Goal
Make WBS Levels, Disciplines, Drawing Types, and Construction Milestones navigation tabs reusable, unified, and displayed consistently across all four list/register pages.

## Proposed Design
Create a single reusable include template: `app/Project/templates/project/includes/setup_nav.html`.

This file will:
1. Accept `project` and `active_tab` (e.g. `'wbs'`, `'disciplines'`, `'drawing_types'`, `'milestones'`).
2. Render four tabs in a unified horizontal list:
   - **WBS Levels**: Link to `project:project-category-list`, Icon: `rectangle-stack`
   - **Disciplines**: Link to `project:project-discipline-list`, Icon: `academic-cap`
   - **Drawing Types**: Link to `project:project-drawing-type-list`, Icon: `document-text`
   - **Construction Milestones**: Link to `project:project-milestone-setup`, Icon: `calendar`
3. Apply active styling (`border-indigo-500 text-indigo-600`) to the tab matching `active_tab`, and inactive styling (`border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300`) to others.

## Target Templates to Modify
1. `app/Project/templates/project/categories/category_manage.html` (active_tab="wbs")
2. `app/Project/templates/project/disciplines/discipline_manage.html` (active_tab="disciplines")
3. `app/Project/templates/project/drawing_types/drawing_type_manage.html` (active_tab="drawing_types")
4. `app/Project/templates/project/milestones/milestone_manage.html` (active_tab="milestones")

## Verification Plan
1. Render each page and verify the tabs are visible and formatted correctly.
2. Click on each tab to ensure navigation works correctly.
3. Verify that the active tab is highlighted correctly.
