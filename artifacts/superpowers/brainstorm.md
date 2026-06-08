# Superpowers Brainstorm: Add Bi-Weekly Safety and NCR Cards to Company Management

## Goal
The goal is to add "Bi-Weekly Safety" and "Non-Conformance Report" (NCR) cards to the "Site Management" grid section of the Business Management Center dashboard (`company_management.html`), specifically appending them to the end of the site cards list (Option 1).

## Constraints
- **Styling**: The new cards must conform to the existing visual design system: Tailwind CSS layout (`flex flex-col justify-center items-center px-4 py-4 bg-white rounded-xl border border-*-200`), transition/hover animations, and outline Heroicons style.
- **Context Parameter**: The URL parameter must use `company.pk` because in `company_management.html`, the template context variable representing the active project is named `company`.
- **URL Namespaces**: The correct Django URL patterns are:
  - Bi-Weekly Safety: `site_management:biweekly-safety-list`
  - NCR Register: `site_management:ncr-list`

## Known context
- The "Site Management" section in `company_management.html` contains a grid of links pointing to various site logs.
- Currently, there are 16 cards in this grid, all rendered in `<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">`.
- "Bi-Weekly Safety" is configured with the `shield-exclamation` icon and uses `indigo` accents.
- "NCR Register" is configured with the `document-check` icon and uses `rose` or `amber` accents.

## Risks
- **Mismatch in Context Variable**: Accidentally using `project.pk` instead of `company.pk` will cause Django's template engine to fail to resolve the URL at runtime.
- **Visual Alignment**: Adding two new cards shifts the total count from 16 to 18 cards, which might leave an uneven grid row on larger screens (18 is not divisible by 4, leaving 2 cards on the last row). However, Tailwind's grid naturally centers/wraps elements seamlessly.

## Options (2?4)

### Option 1: Append both cards to the end of the grid list (Selected)
Add the "Bi-Weekly Safety" and "NCR Register" cards at the very end of the list.
*   **Pros**: Simplifies code modification and diff representation; no risk of breaking order logic.
*   **Cons**: Groups items arbitrarily at the end of the list without thematic relationship to their neighbor cards.

### Option 2: Place cards next to related items (Thematic Grouping)
Insert the cards inline where they relate to other items:
- Insert "NCR Register" directly after the "Quality Control" card.
- Insert "Bi-Weekly Safety" directly after the "Safety Observations" card.
*   **Pros**: Logical user interface flow. Users find NCR directly under Quality Control, and Bi-Weekly Safety directly next to Safety Observations.
*   **Cons**: Requires non-contiguous template edits.

## Recommendation
The user selected Option 1: Append both cards to the end of the grid list. We will proceed with this option.

## Acceptance criteria
1.  **Bi-Weekly Safety Card**:
    *   Renders in the "Site Management" grid, appended to the end of the list (after Overhead Log).
    *   Targets `{% url 'site_management:biweekly-safety-list' company.pk %}`.
    *   Uses the `shield-exclamation` Heroicon and `indigo` styling.
2.  **NCR Register Card**:
    *   Renders in the "Site Management" grid, appended to the end of the list (after Bi-Weekly Safety).
    *   Targets `{% url 'site_management:ncr-list' company.pk %}`.
    *   Uses the `document-check` Heroicon and `rose` or `amber` styling.
3.  **Correct Page Context**: All URLs resolve correctly using the `company.pk` key.
4.  **Aesthetics**: The design and hover animations match the premium card design layout.
5.  **Passing Tests**: All existing template rendering and view unit tests continue to pass.
