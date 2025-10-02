# Windsurf Rules for Profit Pro Django Application

## Project Overview
- Django web application for profit/project management
- Python 3.11+ with Django framework
- Uses PostgreSQL/SQLite for database
- Testing with pytest and factory_boy
- Code quality tools: ruff, ty (type checking)

## Code Style & Standards

### Python Style
- Follow PEP 8 conventions
- Use ruff for linting and formatting (configured in pyproject.toml)
- Line length: 88 characters (Black-compatible)
- Use type hints where appropriate
- Use docstrings for all classes and functions (Google style)

### Import Organization
```python
# Standard library imports
import os
from typing import Any

# Third-party imports
import pytest
from django.db import models

# First-party imports (app modules)
from app.Account.models import Account
from app.core.Utilities.models import BaseModel
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `AccountFactory`, `ProjectModel`)
- **Functions/Methods**: snake_case (e.g., `create_user`, `soft_delete`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_LENGTH`, `DEFAULT_TIMEOUT`)
- **Private methods**: Prefix with underscore (e.g., `_create`, `_validate`)

## Django Patterns

### Models
- All models should inherit from `BaseModel` (provides created_at, updated_at, deleted, soft_delete, restore)
- Use explicit `verbose_name` and `verbose_name_plural` in Meta
- Always define `__str__` method for readable representation
- Use `choices` with TextChoices for enum-like fields
- Add help_text to fields for documentation

```python
class MyModel(BaseModel):
    name = models.CharField(max_length=255, help_text="Model name")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "My Model"
        verbose_name_plural = "My Models"
        ordering = ["-created_at"]
```

### Soft Delete Pattern
- Use `soft_delete()` instead of `delete()` where appropriate
- Use `restore()` to undelete soft-deleted objects
- Check `is_deleted` property to verify deletion status

### User Model
- Custom user model is `Account` (not Django's default User)
- Email is used as USERNAME_FIELD (not username)
- Use `Account.objects.create_user()` for regular users
- Use `Account.objects.create_superuser()` for admins
- Primary contact (phone) is required

## Testing Guidelines

### Test Structure
- Place tests in `app/<app_name>/tests/` directory
- Name test files as `test_<feature>.py` (e.g., `test_models.py`, `test_views.py`)
- Use pytest (not Django's TestCase)
- Group tests in classes with `Test` prefix (e.g., `TestProjectModel`)
- Name test methods with `test_` prefix

### Factory Usage (IMPORTANT)
- **ALWAYS use factory_boy factories instead of manual object creation**
- Factories are located in `app/<app_name>/factories.py`
- Available factories:
  - `AccountFactory` - Regular users
  - `SuperuserFactory` - Admin users
  - `CompanyAccountFactory` - Company accounts
  - `TenantAccountFactory` - Tenant accounts
  - `SuburbFactory` - Suburbs
  - `TownFactory` - Towns
  - `ProjectFactory` - Projects

```python
# GOOD: Use factories
from app.Account.factories import AccountFactory
from app.Project.factories import ProjectFactory

def test_project_creation():
    project = ProjectFactory(name="Test Project")
    assert project.name == "Test Project"

# BAD: Don't manually create objects
def test_project_creation():
    account = Account.objects.create_user(
        email="test@example.com",
        password="pass",
        first_name="Test",
        primary_contact="+27821234567"
    )
    project = Project.objects.create(account=account, name="Test")
```

### Test Best Practices
- Each test should be independent (no shared state)
- Use descriptive test names that explain what is being tested
- Use fixtures from `app/conftest.py` when appropriate
- Test both success and failure cases
- Test edge cases and validation
- Use `pytest.raises()` for exception testing
- Use `@pytest.mark.django_db` if not using autouse fixture

### Test Coverage
- Aim for high test coverage (configured in pyproject.toml)
- Exclude migrations, __init__.py, and config files
- Run tests with: `.venv\Scripts\python.exe -m pytest`
- Run with coverage: `.venv\Scripts\python.exe -m pytest --cov=app --cov-report=html`

## Virtual Environment

### CRITICAL: Always Use .venv
- **ALWAYS check for .venv presence before running commands**
- **Create .venv if it doesn't exist**: `python -m venv .venv`
- **All commands must use .venv**: `.venv\Scripts\python.exe` or `.venv\Scripts\activate`
- Never run commands in global Python environment

```bash
# GOOD
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe manage.py runserver

# BAD
python -m pytest
python manage.py runserver
```

## File Organization

### App Structure
```
app/
├── <AppName>/
│   ├── __init__.py
│   ├── models.py          # Database models
│   ├── views.py           # View logic
│   ├── urls.py            # URL routing
│   ├── admin.py           # Admin interface
│   ├── apps.py            # App configuration
│   ├── factories.py       # Test factories (factory_boy)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_views.py
│   │   └── test_urls.py
│   └── migrations/
├── core/                  # Core utilities
│   └── Utilities/
│       └── models.py      # BaseModel
└── conftest.py           # Shared pytest fixtures
```

### Settings Structure
```
settings/
├── __init__.py
├── base.py               # Base settings
├── local.py              # Local development
├── test.py               # Test settings
└── prod.py               # Production settings
```

## Dependencies

### Requirements Files
- `requirements/base.txt` - Core dependencies
- `requirements/local.txt` - Development dependencies (includes base.txt)
- `requirements/prod.txt` - Production dependencies (includes base.txt)

### Key Dependencies
- Django (web framework)
- pytest, pytest-django (testing)
- factory-boy (test data generation)
- ruff (linting/formatting)
- django-phonenumber-field (phone validation)
- django-crispy-forms + crispy-tailwind (forms)

## Database

### Migrations
- Always create migrations after model changes: `python manage.py makemigrations`
- Review migrations before committing
- Never edit migrations manually unless absolutely necessary
- Run migrations: `python manage.py migrate`

### Queries
- Use select_related() for foreign keys
- Use prefetch_related() for many-to-many and reverse foreign keys
- Avoid N+1 queries
- Use .exists() instead of len(queryset) for existence checks

## Security

### Authentication
- Use Django's authentication system
- Custom user model is `Account`
- Email-based authentication (not username)
- Always hash passwords (use create_user, not create)

### Best Practices
- Never commit sensitive data (.env files)
- Use environment variables for secrets
- Validate all user input
- Use Django's CSRF protection
- Follow OWASP security guidelines

## Git Workflow

### Commits
- Write clear, descriptive commit messages
- Use conventional commits format when possible
- Commit related changes together
- Don't commit generated files (migrations are exception)

### Files to Ignore
- `.env` (environment variables)
- `__pycache__/`, `*.pyc`
- `.pytest_cache/`, `.coverage`, `htmlcov/`
- `db.sqlite3` (development database)
- `.venv/`, `venv/`
- `staticfiles/` (collected static files)

## Code Review Checklist

### Before Committing
- [ ] All tests pass
- [ ] Code follows style guidelines (ruff passes)
- [ ] Type hints added where appropriate
- [ ] Docstrings added for new functions/classes
- [ ] No commented-out code
- [ ] No debug print statements
- [ ] Migrations created if models changed
- [ ] No sensitive data in code

### For New Features
- [ ] Tests written (using factories)
- [ ] Documentation updated
- [ ] Edge cases considered
- [ ] Error handling implemented
- [ ] Validation added

## Common Patterns

### Creating New Models
1. Define model in `models.py` (inherit from BaseModel)
2. Create factory in `factories.py`
3. Create tests in `tests/test_models.py`
4. Register in `admin.py` if needed
5. Run `makemigrations` and `migrate`

### Creating New Tests
1. Import necessary factories
2. Create test class with `Test` prefix
3. Write test methods with `test_` prefix
4. Use factories for object creation
5. Assert expected behavior
6. Run tests to verify

### Adding New App
1. Create app: `python manage.py startapp <AppName>`
2. Add to `INSTALLED_APPS` in settings
3. Create `factories.py` for test data
4. Create `tests/` directory with `__init__.py`
5. Follow existing app structure

## Performance

### Database
- Use database indexes for frequently queried fields
- Avoid loading unnecessary data (use only(), defer())
- Use bulk operations for multiple inserts/updates
- Cache expensive queries when appropriate

### Templates
- Use template fragment caching
- Minimize database queries in templates
- Use static file compression

## Documentation

### Code Documentation
- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Document parameters, return values, and exceptions
- Keep docstrings up to date

### Project Documentation
- Update README.md for setup instructions
- Document API endpoints
- Keep FACTORIES_README.md updated for test factories
- Document environment variables

## Error Handling

### Exceptions
- Catch specific exceptions, not bare `except:`
- Log errors appropriately
- Return meaningful error messages to users
- Use Django's built-in exception classes

### Validation
- Validate at model level (clean() method)
- Validate at form level
- Provide clear validation error messages
- Test validation in unit tests

## Continuous Integration

### Pre-commit Checks
- Run tests: `pytest`
- Run linter: `ruff check .`
- Run formatter: `ruff format .`
- Check types: `ty check` (if configured)
- Check migrations: `python manage.py makemigrations --check --dry-run`

## IDE Configuration

### VS Code Settings
- Use workspace settings for project-specific config
- Configure Python interpreter to use .venv
- Enable pytest test discovery
- Configure ruff for linting

## Notes for AI Assistants

### When Creating Tests
- ALWAYS use factories from `app/<app_name>/factories.py`
- NEVER manually create objects with `Model.objects.create()`
- Import factories at the top of test files
- Use descriptive test names
- Test one thing per test method

### When Modifying Code
- Check existing patterns before implementing
- Follow the established project structure
- Use BaseModel for new models
- Add factories for new models
- Write tests for new functionality

### When Running Commands
- ALWAYS verify .venv exists first
- ALWAYS use `.venv\Scripts\python.exe` for commands
- NEVER run commands in global Python environment
- Check current working directory is project root
