| Task | Status | Description |
| :--- | :--- | :--- |
| **Step 1: Update Default Subscription in `Account` Model** | [x] | Update Account.subscription default to FULL_ACCESS in models.py |
| **Step 2: Generate and Apply Database Migration** | [x] | Run makemigrations and migrate to update default value in DB |
| **Step 3: Update Factories Documentation/Comments** | [x] | Update factories.py comments/defaults to FULL_ACCESS |
| **Step 4: Update and Rename Subscription Default Test** | [/] | Rename and update test_default_subscription_is_demo to test_default_subscription_is_full_access in test_models.py |
| **Step 5: Audit and Verify Entire Account Test Suite** | [ ] | Run pytest app/Account/tests/ to verify zero regressions |
