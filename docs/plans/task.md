| Task | Status | Description |
|---|---|---|
| 1. Fix required date fields on models | [x] | Add `blank=True` to `start_date` and `end_date` in Category, SubCategory, and Group models |
| 2. Generate and apply migrations | [x] | Run makemigrations and migrate to update model state |
| 3. Set `required=False` in Forms | [x] | Explicitly set `required=False` for date fields in CategoryForm, SubCategoryForm, and GroupForm |
| 4. Verify category creation | [x] | Run pytest and verify creation is successful |
