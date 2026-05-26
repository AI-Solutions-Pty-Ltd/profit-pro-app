# Brainstorming: Complimentary Access Notice for Non-Demo Tiers

## Goal
Implement a premium, visually outstanding global notification/notice in the application indicating that the user is a `Subscriber {{tier}} with complimentary access` for all authenticated users who are **not** in the `DEMO_TIER`.

## Constraints
1. **Target Tiers**: Must render only for authenticated users whose subscription tier is **not** `DEMO_TIER`.
2. **Message Requirement**: Must explicitly contain `Subscriber {{tier}} with complimentary access`, where `{{tier}}` dynamically displays the user's subscription tier.
3. **No Breakage**: Must not disrupt the existing Demo Ribbon, the general banner, or any other elements in `nav.html`.
4. **Premium Styling**: Must align with modern web design principles, using sleek styling, appropriate color harmony, responsiveness, and premium micro-animations (e.g., matching or exceeding the polish of the Demo Ribbon).
5. **Robust Implementation**: Must use working implementation details (no placeholder text) and fit neatly into the Django template structure.

## Known context
1. **User Subscription Field**: `Account` model has a `subscription` field and is associated with `Subscription` choices enum defined in `app/Account/subscription_config.py`.
2. **Current Ribbon Logic**: `app/templates/nav.html` already has an authenticated check and a `DEMO_TIER` ribbon check.
3. **Base Layout**: `app/templates/layout.html` includes `nav.html` on line 28, making it a perfect global container for sticky page-top ribbons.
4. **Subscription Choices**:
   - `FREE_TIER = "FREE_TIER", "Free Tier"`
   - `BUSINESS_MANAGEMENT = "BUSINESS_MANAGEMENT", "Business Management Module"`
   - `PAYMENTS_AND_INVOICES = "PAYMENTS_AND_INVOICES", "Payments and Invoices"`
   - `PROFIT_AND_LOSS = "PROFIT_AND_LOSS", "Profit and Loss"`
   - `SITE_MANAGEMENT = "SITE_MANAGEMENT", "Project Management"`
   - `PROJECT_ESTIMATOR = "PROJECT_ESTIMATOR", "Project Estimator"`
   - `ADMINISTRATION = "ADMINISTRATION", "Administration"`
   - `DEMO_TIER = "DEMO_TIER", "Demo"`

## Risks
1. **UI Clutter**: Having multiple global banners (e.g. general banner, demo banner, and complimentary banner) might clutter the top area of the page.
2. **Styling Clashes**: Ad-hoc styling might clash with the current tailwind color schemes.
3. **Template Rendering Errors**: Using fields that do not exist or incorrect template variables (e.g., `user.subscription` vs `user.get_subscription_display`).

## Options (2?4)

### Option 1: Premium Emerald-to-Teal Top Ribbon in `nav.html` (Recommended)
Add a dedicated, sticky top ribbon in `app/templates/nav.html` styled with an elegant, modern emerald-to-teal gradient (`bg-gradient-to-r from-emerald-600 to-teal-500`) to highlight a polished, exclusive "complimentary access" status. It would sit above or below the navigation and only render if `user.is_authenticated` and `user.subscription != "DEMO_TIER"`.
- **Pros**: Clear, prominent, highly polished, consistent with the Demo Ribbon layout.
- **Cons**: Takes up a small amount of vertical screen space.

### Option 2: Dynamic Header/General Banner Integration
Incorporate the subscriber message directly into the existing secondary banner `You build the business, we handle the software` in `app/templates/nav.html`. If the user is logged in and not in the Demo tier, this general banner dynamically changes its text to the complimentary subscriber message and shifts to an elegant gradient.
- **Pros**: Extremely clean, zero additional vertical clutter since it repurposes existing space.
- **Cons**: Less prominent than a dedicated new alert ribbon.

### Option 3: Elegant Dashboard Banner / Toast
Add a beautifully animated sliding card/alert on dashboard load, or a persistent, gorgeous card in the Dashboard home views rather than a persistent global ribbon.
- **Pros**: Zero impact on global navigation space.
- **Cons**: Only visible on specific dashboards, not globally persistent.

## Recommendation
**Option 1** is highly recommended. A persistent global ribbon at the top of the viewport (similar to the Demo Ribbon) keeps this important account notice visible across the entire application without disrupting normal page content. By using a distinct, premium emerald/teal gradient (`bg-gradient-to-r from-emerald-500 to-teal-600`), we clearly distinguish it from the Indigo Demo Ribbon and give it an upscale, high-end feel.

## Acceptance criteria
1. For any authenticated user with a subscription NOT equal to `DEMO_TIER`, the notice is displayed at the top of the page.
2. For unauthenticated/anonymous users, no complimentary notice is displayed.
3. For users with subscription `DEMO_TIER`, the original Demo Ribbon is displayed, and the complimentary notice is NOT displayed.
4. The notice message correctly displays the subscription tier name dynamically (e.g., `Subscriber Free Tier with complimentary access` or `Subscriber Business Management Module with complimentary access`).
5. The visual presentation is highly premium and responsive, adapting nicely to mobile and desktop screens.
