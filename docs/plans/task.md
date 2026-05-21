| Task | Status | Description |
| :--- | :--- | :--- |
| **Brainstorming Task 1: Explore project context** | [x] | Analyze how base.html, views, and routing are structured to render the popup globally |
| **Brainstorming Task 2: Ask clarifying questions** | [x] | Address one clarifying question at a time regarding profile URL and page exclusions |
| **Brainstorming Task 3: Propose 2-3 approaches** | [x] | Formulate 2-3 approaches for global popup rendering vs page exclusions |
| **Brainstorming Task 4: Present design** | [x] | Present the final design sections to the user for feedback and approval |
| **Brainstorming Task 5: Write design doc** | [x] | Write and save design doc to docs/plans/ |
| **Brainstorming Task 6: Transition to implementation** | [x] | Invoke writing-plans skill to write the implementation plan |
| **Implementation Task 1: Context Processor Setup** | [x] | Implement global welcome logic with page exclusions in custom_context_processor |
| **Implementation Task 2: Core Views Cleanup** | [x] | Remove redundant local context variable from HomeView.get_context_data |
| **Implementation Task 3: Template Relocation** | [x] | Relocate modal HTML/JS from home.html to layout.html with updated cards & CTA |
| **Implementation Task 4: Test Refactoring** | [x] | Update and expand test suite to assert global logic and exclusions |
| **Implementation Task 5: Verification & Styling** | [/] | Run pytest, ruff check, and graphify update to verify complete correctness |
