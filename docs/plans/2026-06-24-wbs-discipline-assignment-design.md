# Design Document: WBS Level Discipline Assignment

## Goal
Add functionality to assign disciplines to WBS Levels (L1/Category, L2/SubCategory, and L3/Group) from the existing project discipline register, and display them as visual tags/cards on the WBS cards.

## Approach
1. **Database Schema**: Added Many-to-Many relationships on `Category`, `SubCategory`, and `Group` pointing to `Discipline`.
2. **API Endpoints**: Added POST views (`CategoryDisciplinesUpdateView`, `SubCategoryDisciplinesUpdateView`, `GroupDisciplinesUpdateView`) in `app/Project/projects/category_views.py` and routed them in `app/Project/projects/category_urls.py`.
3. **Modals**: Added L1, L2, L3 discipline selection modal templates listing project disciplines as checkboxes.
4. **UI Cards Display**: Rendered assigned disciplines as visual color-themed cards/chips under each WBS Level title.
5. **Prefetch Optimization**: Prefetched `disciplines` relationships in `ScopePlanningView` query to prevent N+1 queries.

## Testing & Verification
- Unit tests written in `app/Planning/tests/test_scope_planning.py` to assert correct M2M relations, view context, and API update operations.
- Checked using Django system check.
