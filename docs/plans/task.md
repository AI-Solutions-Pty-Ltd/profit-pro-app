| Task | Status | Description |
| :--- | :--- | :--- |
| **Step 1: Remove project_discipline field** | [x] | Remove `project_discipline` from the `fields` list in `BasicProjectCreateForm` inside `app/Project/projects/project_forms.py`. |
| **Step 2: Run pytest validation** | [x] | Run the Django test suite (`pytest`) to verify all tests continue to pass. |
| **Step 3: Update knowledge graph** | [x] | Run `graphify update .` to keep the AST graph structure synchronized. |
