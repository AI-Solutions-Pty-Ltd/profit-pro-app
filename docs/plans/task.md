| Task | Status | Description |
| :--- | :--- | :--- |
| **Step 1: Add `FULL_ACCESS` to `Subscription` Choice Enum** | [x] | Add FULL_ACCESS choice to Subscription TextChoices in subscription_config.py |
| **Step 2: Configure Limits for the `FULL_ACCESS` Tier** | [x] | Map limits for FULL_ACCESS in SubscriptionConfig.LIMITS in subscription_config.py |
| **Step 3: Implement Bypass Checks in `Account` Model** | [x] | Refactor has_subscription_tier and has_demo_permission in models.py |
| **Step 4: Generate and Apply Database Migration** | [x] | Run makemigrations and migrate to update Subscription choices in DB |
| **Step 5: Write and Run Unit Tests for `FULL_ACCESS` Tier** | [x] | Implement TestFullAccessTier in test_demo_tier.py and run pytest |
| **Step 6: Verify Full System Suite Passes** | [x] | Run the complete project test suite to verify no regressions |
