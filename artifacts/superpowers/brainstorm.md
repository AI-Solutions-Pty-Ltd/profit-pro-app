# Onboarding Welcome Modal for Demo Tier Users - Brainstorm (Upgrade & Lock Protection)

## Goal
To design and implement a premium, non-dismissable full-screen overlay popup/modal (powered by robust server-side protection) that lock-protects the entire Profit Pro application whenever a user on the `DEMO_TIER` has had their demo period expire (i.e., `user.subscription == Subscription.DEMO_TIER` and `user.is_subscription_expired` is `True`).

The lock-out state must:
1. **Lock protect the entire app**: Prevent users from accessing dashboards, project lists, BOQs, cost modules, and libraries.
2. **Be completely non-dismissable**: Have no close button ("X"), disable clicking on the backdrop to dismiss, and ignore `Escape` key actions.
3. **Offer an upgrade path**: Provide a high-visibility, premium call-to-action button linking directly to the marketing website checkout page (`https://sedgepro.co.za/#prelaunch-promotion`) to upgrade.
4. **Provide a safe exit**: Include a clean, functional "Logout" button so users aren't trapped in the locked state and can log out or switch accounts.

---

## Constraints
1. **Tech Stack**: Django 5.2, Tailwind CSS, and Vanilla JavaScript. We must utilize the current styling framework of the application.
2. **Absolute Lock Protection**: The protection must not be bypassable by simple inspection/DOM manipulation (like deleting the modal elements via Chrome DevTools). The server must actively enforce the block.
3. **Safe Exceptions**: Standard authentication flows (login, registration, email verification, password reset) and static/media assets must remain accessible so users aren't locked out of changing credentials.
4. **Usability**: Trapping users without a logout option is unacceptable and causes major user frustration. A clear exit path must be visible.

---

## Known context
1. **Account Properties**:
   - `user.has_demo_permission` returns `True` only if `subscription == DEMO_TIER` and `not is_subscription_expired`.
   - `user.is_subscription_expired` returns `True` if `timezone.now() > subscription_expires_at`.
2. **Routing / Nav**:
   - A sticky demo ribbon already exists in `nav.html` showing active trial time left.
   - The marketing website target is `https://sedgepro.co.za/#prelaunch-promotion`.

---

## Risks
1. **Redirect Loops**: Redirection middlewares are prone to infinite redirect loops if we accidentally intercept requests to the `/demo-expired/` view itself, the logout route, or static assets.
2. **DOM-Level Hacking**: If we only enforce the lockout in the HTML/CSS template layer, tech-savvy users can bypass the lock by hiding the DOM node and continuing to use the backend features.
3. **Trapped Sessions**: Without an explicit logout option on the locked page, users might remain permanently locked out of all parts of the app without any means of logging into a paid account.

---

## Options (2–4)

### Option 1: Global Non-Dismissable Modal Overlay in `layout.html` via Custom Context Processor
* **Summary**: We inject a `show_demo_expired_modal` boolean variable into the global template context. In `layout.html`, if this flag is `True`, we render a full-screen, blurred glassmorphic overlay (`z-[100000]`) with a warning card and an upgrade button, but no close buttons or click-to-close scripts.
* **Pros**:
  * Very easy to implement.
  * Preserves the exact URL path in the address bar so the user can easily see what page they were viewing.
* **Cons**:
  * Tech-savvy users can use DevTools to delete the overlay element and bypass the lock.
  * Form submissions and AJAX requests might still execute in the background if the user acts quickly or uses browser consoles.
* **Complexity / Risk**: Low.

### Option 2: Server-side Middleware + Special Dedicated `/demo-expired/` Locked View (Recommended)
* **Summary**: We register a custom Django middleware `DemoExpiredMiddleware`. It intercepts all requests from authenticated users. If they are in the `DEMO_TIER` and `is_subscription_expired` is `True`, the middleware immediately redirects them to `/users/demo-expired/` (with safe exclusions for the view itself, logout view, static assets, and admin paths).
* **Pros**:
  * **100% Server-side Secure**: Bypassing is completely impossible since the server refuses to render any views other than the dedicated locked view.
  * Beautiful dedicated page that is clutter-free (removes standard nav/footer).
  * Highly professional enterprise pattern.
* **Cons**:
  * Slightly more files to touch (requires new middleware, URL, view, template, and test).
* **Complexity / Risk**: Medium.

### Option 3: Hybrid Inline Rendering Middleware
* **Summary**: The middleware intercepts the request and, if expired, returns the locked page directly inline as a 200 (or 403) response instead of doing a 302 redirect.
* **Pros**:
  * Retains the user's current URL, allowing them to refresh to resume work once upgraded.
* **Cons**:
  * Breaks API / AJAX routes that expect JSON payloads.
* **Complexity / Risk**: Medium.

---

## Recommendation
**Option 2: Server-side Middleware + Special Dedicated `/demo-expired/` Locked View** is the ideal solution. It provides bulletproof protection at the server layer, preventing DOM inspection bypasses or malicious form submissions, while rendering a visually stunning, premium, non-dismissable locked view.

---

## Acceptance criteria
1. **Middleware Lockout**: Any request from an authenticated expired demo user (non-superuser) redirects immediately to `/users/demo-expired/`, except for the `/users/demo-expired/` view itself, `/users/auth/logout/`, static resources, and media.
2. **Premium Lockout UI**: The `/users/demo-expired/` page displays a gorgeous, premium, glassmorphic layout:
   - Full-page immersive blurred background (`bg-slate-900/80 backdrop-blur-md`).
   - Premium card layout with modern typography, custom icons, and visual cues showing the demo trial has expired.
3. **Upgrade CTA**: A prominent, high-contrast, beautiful button: "Upgrade & Unlock" linking to `https://sedgepro.co.za/#prelaunch-promotion` in a new tab.
4. **Completely Non-Dismissable**: No close button, backdrop clicks do not close, Escape key does not close, and browser navigation within the app redirects back to the lockout page.
5. **Escape Hatch (Logout)**: A clear, accessible "Logout" option is present on the page so users can exit the locked account and sign in with a different account.
6. **API / AJAX Safety**: If an AJAX/fetch request is intercepted, the middleware returns a `403 Forbidden` JSON payload: `{"error": "Demo trial period has expired"}` instead of an HTML redirect response.
7. **Comprehensive Unit Tests**: Pytest suite asserting active demo accounts can browse, expired demo accounts are locked out, and expired demo accounts can still successfully log out.
