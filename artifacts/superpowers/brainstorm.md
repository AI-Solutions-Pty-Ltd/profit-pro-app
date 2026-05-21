# Onboarding Welcome Modal for Demo Tier Users - Brainstorm

## Goal
To design and implement a premium, visually stunning welcome popup/modal on the Portfolio Dashboard for newly registered Demo Tier users who have not yet created a project. The popup will welcome them to the platform, briefly highlight key modules (such as Estimator, Ledger, Site Management), and offer a high-contrast Call-to-Action (CTA) to create their first project, while providing a clear way to dismiss and browse existing demo projects.

## Constraints
* **Tech Stack**: Django 5.2, Tailwind CSS, and Vanilla JavaScript (avoiding heavy external libraries like Alpine.js or Vue since the dashboard relies on standard Tailwind CSS + native JavaScript).
* **Base Layout Compatibility**: The modal must be integrated cleanly within the existing `portfolio_dashboard.html` template and extend `base_full.html` without disrupting the chart rendering or other script behaviors.
* **Aesthetics**: Standard HTML defaults are unacceptable. The modal must leverage premium UI elements (backdrop-blur-sm, modern indigo gradients, smooth entry transitions, and structured grid highlights for features) to wow the user.
* **State & Dismissal**: The popup should be helpful, not intrusive. Users must be able to dismiss it easily, and the system should remember their choice so they aren't repeatedly interrupted as they browse preloaded demo data.
* **No Database Overheads**: The implementation must utilize existing methods (such as the `has_demo_permission` property and `user.get_projects`) and avoid modifying the database schema or adding new models.

## Known context
* **Dashboard View**: `PortfolioDashboardView` in `app/Project/views/portfolio_views.py` is the main landing dashboard rendering `portfolio/portfolio_dashboard.html`.
* **User Permission**: The `Account` model has `has_demo_permission` which returns `True` for active, unexpired demo subscription accounts.
* **Project Structure**: Demo projects are filtered using the `is_demo` flag. A user's own projects can be identified by querying `user.get_projects.filter(is_demo=False)`. If this queryset is empty (`.exists()` is `False`), the user has not created any projects.
* **CTAs**: A "Create Project" link already exists on the dashboard at `{% url 'project:project-create' %}`.

## Risks
* **UX Friction**: Showing a popup on every page refresh or dashboard visit will annoy users trying to inspect demo data. We must ensure robust, reliable state management for dismissing the modal.
* **Mobile Responsiveness**: Large welcome modals often break on mobile viewports. The design must scale down fluidly and ensure close buttons are fully accessible on touch interfaces.
* **Accessibility**: Missing modal close actions (like pressing the Escape key or clicking outside) will impact user accessibility and must be supported natively in the script.

## Options (2?4)

### Option 1: Server-controlled flag with LocalStorage-based client-side dismissal (Recommended)
* **Summary**: The server passes a context variable `show_demo_welcome_popup = user.has_demo_permission and not projects.filter(is_demo=False).exists()`. The template renders the modal marked as `hidden` by default. A small Vanilla JS script checks `localStorage.getItem('dismissed_demo_welcome')`. If not present, the script removes the `hidden` class and animates the modal into view. Clicking "Dismiss" or the close button sets `localStorage.setItem('dismissed_demo_welcome', 'true')` and hides it.
* **Pros**:
  * Persistent across sessions on the same browser (even if they log out and back in).
  * 100% stateless on the server side?no database updates or session state tracking required.
  * Instant load and smooth client-side animation.
* **Cons**:
  * Browser-specific; if the user logs in from a different browser or device, they will see it again (standard for welcome guides).
* **Complexity / Risk**: Very Low.

### Option 2: Pure server-side context with Django Session-based dismissal
* **Summary**: In `PortfolioDashboardView`, the server checks `user.has_demo_permission and not projects.filter(is_demo=False).exists() and not request.session.get('demo_welcome_dismissed')`. If true, `show_demo_welcome_popup = True` is sent to the template. When the user dismisses the modal, a POST request or HTMX call is sent to a Django view to set `request.session['demo_welcome_dismissed'] = True`.
* **Pros**:
  * Consistent dismissal across browsers/sessions on the same device.
  * Server controls dismissal lifecycle.
* **Cons**:
  * Requires setting up a new URL endpoint, writing an AJAX/fetch handler, and adding session mutation logic.
  * Session expiration could cause the welcome modal to reappear.
* **Complexity / Risk**: Medium.

### Option 3: SessionStorage-based client-side dismissal
* **Summary**: Similar to Option 1, but utilizes `sessionStorage` instead of `localStorage`.
* **Pros**:
  * Shows the popup again in future browser sessions, keeping the onboarding reminder active until they actually create their first project.
* **Cons**:
  * Can be annoying to returning users who explicitly dismissed it earlier but haven't started a project yet.
* **Complexity / Risk**: Low.

## Recommendation
**Option 1: Server-controlled flag with LocalStorage-based client-side dismissal** is the ideal solution. It perfectly combines server-side accuracy (using Python to query subscription status and project counts) with fast, responsive, and completely stateless client-side dismissal persistence. This ensures a flawless user experience without the overhead of creating new endpoints, modifying sessions, or mutating the database.

## Acceptance criteria
1. **Condition Matching**: The modal is rendered only when a logged-in user is on the `DEMO_TIER` (validated by `user.has_demo_permission`) AND has created `0` non-demo projects (validated by `not projects.filter(is_demo=False).exists()`).
2. **Harmonious Premium Styling**: The modal features a gorgeous glassmorphism backdrop overlay (`backdrop-blur-sm bg-slate-900/60`), vibrant dark/light gradient header, sleek feature cards detailing what they can do next, and modern typography.
3. **Actionable CTAs**:
   * A primary, high-contrast, pulsating gradient button for "Create Your First Project" linking to `{% url 'project:project-create' %}`.
   * A secondary, clean button for "Explore Preloaded Demo Projects" that closes the modal.
4. **Robust Closing Events**: The modal can be closed by clicking the close button, clicking the background overlay, or pressing the `Escape` key.
5. **Permanent Dismissal Memory**: Once closed or dismissed, `localStorage` is updated, ensuring the modal never displays again on that browser.
6. **Mobile Adaptability**: Fully responsive styling that centers the modal vertically and horizontally on desktop, and transitions to a readable full-width card on mobile screens.
7. **Test Verification**: Includes Unit Tests asserting that the correct context variable (`show_demo_welcome_popup`) is provided under the exact target conditions.
