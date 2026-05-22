| Task | Status | Description |
| :--- | :--- | :--- |
| **Step 1: Implement Company.ensure_demo_companies() classmethod** | [x] | Add duplicates-proof class method to seed target companies |
| **Step 2: Hook up seeding to the create_demo_user command** | [x] | Integrate ensure_demo_companies inside manage.py create_demo_user |
| **Step 3: Conditionally filter querysets in project setup Forms** | [x] | Expand dropdown querysets for clients, contractors, and lead consultants |
| **Step 4: Include demo companies in portfolio filter dropdowns** | [x] | Update ProjectFilterForm initialization to union demo companies |
| **Step 5: Add comprehensive pytest unit tests** | [x] | Create test suite test_demo_companies.py to verify visibility and isolation |
| **Step 6: Verify and run Graphify update** | [x] | Run all pytest suites and graphify update to finalize |
