# Cost Management Module

## Overview
The Cost Management module provides a comprehensive system for tracking and managing costs associated with bills in your construction projects.

## Features

### 1. Project Cost Tree View
- **URL**: `/cost/project/<project_pk>/`
- **View**: `ProjectCostTreeView`
- **Description**: Displays a hierarchical tree view of all costs organized by Structure → Bill
- **Features**:
  - Shows total costs per bill
  - Shows total costs per structure
  - Displays grand total for the entire project
  - Click on any bill to view detailed costs

### 2. Bill Cost Detail View
- **URL**: `/cost/project/<project_pk>/bill/<bill_pk>/`
- **View**: `BillCostDetailView`
- **Description**: Shows all costs for a specific bill in a filterable table
- **Features**:
  - Paginated table (20 items per page)
  - Search by description
  - Filter by date range (from/to)
  - Shows total amount (excl. VAT)
  - Shows total amount (incl. VAT)
  - Displays VAT status for each cost

### 3. Add Cost View
- **URL**: `/cost/project/<project_pk>/bill/<bill_pk>/add/`
- **View**: `BillCostCreateView`
- **Description**: Form to add new costs to a bill
- **Features**:
  - Date picker
  - Description field
  - Amount field (excl. VAT)
  - VAT checkbox (automatically calculates 15% VAT)
  - Auto-calculates total amount

### 4. Edit Cost View
- **URL**: `/cost/project/<project_pk>/bill/<bill_pk>/cost/<cost_pk>/edit/`
- **View**: `BillCostUpdateView`
- **Description**: Form to edit an existing cost
- **Features**:
  - Pre-populated form with existing cost data
  - Same fields as Add Cost view
  - Validates that cost belongs to the correct project
  - Accessible via "Edit" link in the costs table

## Security

All views are protected by the `ProjectAccessMixin` which:
1. Requires user authentication (`LoginRequiredMixin`)
2. Verifies the user owns the project (`project.account == request.user`)
3. Redirects unauthorized users with an error message
4. Validates that bills belong to the correct project

## Models

### Cost Model
```python
class Cost(BaseModel):
    bill = ForeignKey(Bill, related_name="costs")
    date = DateField()
    description = CharField(max_length=100)
    amount = DecimalField(max_digits=10, decimal_places=2)
    vat = BooleanField(default=False)
    total = DecimalField(max_digits=10, decimal_places=2)
```

**Inherits from BaseModel**:
- `created_at`
- `updated_at`
- `deleted`
- `soft_delete()` method
- `restore()` method
- `is_deleted` property

## Forms

### CostForm
- Automatically calculates `total` field based on `amount` and `vat`
- If VAT is checked: `total = amount * 1.15`
- If VAT is unchecked: `total = amount`

## Usage

### Accessing from Project Detail
Add a link in your project detail template:
```html
<a href="{% url 'cost:project-cost-tree' project.pk %}">
    Manage Costs
</a>
```

### Navigation Flow
1. Project Detail → Cost Tree View
2. Cost Tree View → Bill Cost Detail (click on any bill)
3. Bill Cost Detail → Add Cost (click "Add Cost" button)
4. Bill Cost Detail → Edit Cost (click "Edit" link on any cost row)
5. After adding/editing cost → Redirects back to Bill Cost Detail

## Database Migration

Run migrations to create the Cost table:
```bash
.venv\Scripts\python.exe manage.py makemigrations
.venv\Scripts\python.exe manage.py migrate
```

## Admin Registration

To manage costs in Django admin, create `admin.py`:
```python
from django.contrib import admin
from .models import Cost

@admin.register(Cost)
class CostAdmin(admin.ModelAdmin):
    list_display = ['description', 'bill', 'date', 'amount', 'vat', 'total']
    list_filter = ['vat', 'date', 'bill__structure']
    search_fields = ['description', 'bill__name']
    date_hierarchy = 'date'
```

## Testing

Create tests in `app/Cost/tests/` directory following the project's testing patterns using factory_boy.

## Future Enhancements

Potential features to add:
- Delete cost functionality (soft delete)
- Export costs to CSV/Excel
- Cost categories/types
- Attach receipts/invoices to costs
- Cost approval workflow
- Budget vs actual cost comparison
- Cost forecasting
