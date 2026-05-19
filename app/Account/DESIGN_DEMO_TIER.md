# Design: Demo Tier & Expiration System

## Understanding Summary
- **What**: A new `DEMO_TIER` subscription level with a mandatory expiration date.
- **Why**: To provide prospective users with a full-featured trial of the Business and Project Management modules.
- **Access**: Mirrors the `BUSINESS_MANAGEMENT` tier (including its children like Site Management).
- **Enforcement**: Access is strictly blocked once the current time exceeds the `subscription_expires_at` date.

## Data Model Changes
### Account Model (`app.Account.models.Account`)
- **New Field**: `subscription_expires_at` (DateTimeField, nullable).
- **Logic Update**: `has_subscription_tier` is modified to check if the user is in `DEMO_TIER` and if the subscription has expired. If expired, it returns `False`, triggering the `SubscriptionRequiredMixin` failure.

## UI Specifications
### Demo Ribbon (`app.templates.nav.html`)
- **Position**: Sticky, at the very top of the viewport (z-index 60).
- **Colors**: Indigo background (`bg-indigo-600`), white text.
- **Content**:
  - **Status**: "🚀 Demo Account Active"
  - **Countdown**: "Time Remaining: [X days, Y hours]"
  - **Call to Action**: "Buy Now" button linking to `https://sedgepro.co.za/#prelaunch-promotion`.
- **Visibility**: Only visible to users where `subscription == DEMO_TIER`.

## Decision Log
| Decision | Alternative | Rationale |
| :--- | :--- | :--- |
| **Integrated Enum** | Separate Boolean Flag | Using the existing `Subscription` enum allows us to leverage all current mixins and template filters without modification. |
| **Block on Expiry** | Auto-revert to Free | Blocking access provides a clear signal to the user that the trial has ended and encourages conversion. |
| **Sticky Ribbon** | Content Banner | A sticky ribbon ensures the user always has a clear path to purchase regardless of which dashboard they are viewing. |
