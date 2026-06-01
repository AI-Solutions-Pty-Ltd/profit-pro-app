# Brainstorm: Setup Cards Get-Started Help Tooltips

## Goal
Add a premium, visually appealing information icon button next to each setup card's heading on the Project Setup page. Clicking the icon opens a toggleable, secure, and beautifully styled tooltip detailing step-by-step help for getting started with that specific setup step.

## Constraints
- **Tailwind Compatibility**: Tooltips must utilize pure Tailwind CSS classes and Vanilla Javascript for smooth, lightweight transitions (no external JQuery or tooltip framework dependencies).
- **No Overflow Clipping**: Tooltips must be positioned defensively to ensure they are never cut off by the `overflow-hidden` properties of parent dashboard panels.
- **Icon Style**: Use standard Heroicon outlines already registered in the template for consistency.
- **Responsive Layout**: Tooltip cards must render perfectly on both mobile screens (single-column) and larger grid screens (up to 3 columns).

## Known context
- **Setup Cards Location**: `app/Project/templates/project/project_setup.html` renders the grid of cards under the "Project Information" panel.
- **Card Elements**: Card headings like "Setup Project", "Allocate Client", "Allocate Contractor", "Allocate Lead Consultant", "Upload BOQ (CSV)", "Attach BOQ (Optional)", and "Allocate Signatory".
- **Global Styles & Templates**: Core assets are defined in `layout.html` and static stylesheets.

## Risks
- **Visual Clutter**: Adding info buttons to 7 different cards in a small grid can look cluttered if not designed with micro-spacing and subtle styling.
  - *Mitigation*: We will use a small, elegant `text-gray-400` color for the icon, matching standard layout tokens, and make it highlight in `text-indigo-600` only on hover/active toggle.
- **Clipping on Grid Edges**: Tooltips near the left/right boundaries of the grid could overflow the container.
  - *Mitigation*: We will position the tooltips relative to the heading text with safe padding and center-align or edge-align them (`left-0` or `right-0`) so they stay contained within the respective card boundaries.

## Options (2–4)

### Option 1: Standard Hover Tooltips (CSS Group)
- **Summary**: Add an absolute-positioned hidden tooltip element inside a relative container. Show it on hover using Tailwind `group-hover:block` or `group-hover:opacity-100` classes.
- **Pros**: Super fast, no JS required, light footprint.
- **Cons**: Cannot be accessed easily by mobile touch-events. Hard to read step-by-step instructions because the tooltip immediately vanishes as soon as the mouse cursor moves a millimeter away.
- **Complexity / risk**: Low complexity / Low risk.

### Option 2: Interactive Click-to-Toggle Tooltip Cards (Recommended)
- **Summary**: Implement a click-to-toggle tooltip card for each setup step. The help card is positioned absolute to the heading, showing a clean checkmark list of getting-started steps, a step title, and a small close cross button. We will write a tiny, global inline JS function (`toggleSetupTooltip`) to show/hide the tooltips and close them when clicking outside or clicking the close button.
- **Pros**:
  - Extremely premium feel: feels like a fully interactive guide.
  - Excellent for mobile: works seamlessly on touch devices.
  - User friendly: stays open while the user performs the actions or reads the steps.
- **Cons**: Requires adding a simple toggle script.
- **Complexity / risk**: Low-Medium complexity / Very low risk.

### Option 3: Inline Expandable Help Drawers (Accordion style)
- **Summary**: Add an inline help drawer inside the card itself. Clicking the info icon expands the drawer vertically within the card, shifting content down.
- **Pros**: 100% immune to clipping since it lives in the normal document flow.
- **Cons**: Modifies the height of individual cards dynamically, creating uneven grid alignment across the columns (ruining the pristine symmetrical dashboard grid look).
- **Complexity / risk**: Medium complexity / Medium risk (aesthetic inconsistency).

## Recommendation
We recommend **Option 2 (Interactive Click-to-Toggle Tooltips)**. It delivers a premium visual experience, functions flawlessly on touch devices, and maintains grid symmetry without altering card heights dynamically.

## Acceptance criteria
- [ ] Every card inside the Project Setup section has a small inline Info Icon button next to its heading.
- [ ] Clicking the icon toggles a structured tooltip containing clear getting-started steps.
- [ ] The tooltip layout is styled with a dark glassmorphism aesthetic (`bg-slate-900 text-white rounded-xl shadow-xl`), custom checkmark bullet points, and an explicit close button.
- [ ] Clicking outside the tooltip or clicking another tooltip closes the open one.
- [ ] Fully responsive: fits cleanly within card borders on all device sizes.
