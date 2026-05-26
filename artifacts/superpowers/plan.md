# Implementation Plan: Complimentary Access Notice for Non-Demo Tiers

## Goal
Implement a premium, visually outstanding global notice ribbon in the application navigation indicating that the user is a `Subscriber {{tier}} with complimentary access` for all authenticated users who are NOT in the `DEMO_TIER`.

## Assumptions
1. The `user` object is available in the template context via `request.user` (or `user` globally in standard Django navigation context).
2. The user's subscription tier can be resolved dynamically via `user.get_subscription_display` (or `user.subscription`).
3. Tailwind CSS classes are fully available and compiled properly for styling the ribbon.

## Plan

### Step 1: Add the Complimentary Access Ribbon to the Navigation Template
- **Files**:
  - `app/templates/nav.html`
- **Change**:
  - Underneath the existing `{% if user.is_authenticated and user.subscription == "DEMO_TIER" %}` block (line 27), add a new conditional block:
    ```html
    {% if user.is_authenticated and user.subscription != "DEMO_TIER" %}
        <!-- Complimentary Access Ribbon -->
        <div class="bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-500 text-white text-[10px] sm:text-xs font-bold py-1.5 px-4 flex justify-between items-center z-[60] border-b border-emerald-500 shadow-lg">
            <div class="flex gap-2 items-center">
                <span class="flex relative w-2 h-2">
                    <span class="inline-flex absolute w-full h-full bg-emerald-300 rounded-full opacity-75 animate-ping"></span>
                    <span class="inline-flex relative w-2 h-2 bg-white rounded-full"></span>
                </span>
                <span class="tracking-widest uppercase">Subscriber {{ user.get_subscription_display }} with complimentary access</span>
            </div>
        </div>
    {% endif %}
    ```
- **Verify**:
  - Perform a sanity test compilation or template load to confirm syntax correctness.

### Step 2: Add Pytest Unit Tests to Validate the Ribbon Rendering
- **Files**:
  - `app/Account/tests/test_demo_lockout.py`
- **Change**:
  - Add test cases to the `TestDemoLockout` class that:
    1. Verify the complimentary access ribbon renders for an authenticated non-demo user (`self.paid_user`) and dynamically displays their subscription tier display name.
    2. Verify the complimentary access ribbon is NOT visible for an authenticated demo user (`self.active_demo_user`).
    3. Verify the complimentary access ribbon is NOT visible for an anonymous/unauthenticated user.
- **Verify**:
  - Run the test suite:
    ```bash
    .venv\Scripts\python.exe -m pytest app/Account/tests/test_demo_lockout.py -v
    ```
  - Confirm all tests pass with no errors.

## Risks & mitigations
- **Risk**: The notice overlaps or displaces other page elements.
  - *Mitigation*: The nav container is already a flex-col box with appropriate sticky styling. By matching the height and style of the existing Demo Ribbon, we ensure layout flows correctly without causing overlapping or displacement issues.
- **Risk**: Missing translation or empty display for certain custom/new subscription tiers.
  - *Mitigation*: `get_subscription_display` automatically falls back gracefully or retrieves the mapped display name from choices in `Subscription` class.

## Rollback plan
- Revert the changes to `app/templates/nav.html` and `app/Account/tests/test_demo_lockout.py` using git:
  ```bash
  git checkout app/templates/nav.html app/Account/tests/test_demo_lockout.py
  ```
