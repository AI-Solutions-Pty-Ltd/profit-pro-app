# Test Factories Documentation

This project uses `factory_boy` for creating test data. Factories provide a flexible and maintainable way to generate test objects.

## Available Factories

### Account Factories (`app/Account/factories.py`)

#### `SuburbFactory`
Creates Suburb instances with auto-generated unique names and postcodes.

```python
from app.Account.factories import SuburbFactory

# Create with defaults
suburb = SuburbFactory()

# Create with specific values
suburb = SuburbFactory(suburb="Sandton", postcode="2196")
```

#### `TownFactory`
Creates Town instances with auto-generated unique names.

```python
from app.Account.factories import TownFactory

town = TownFactory()
town = TownFactory(town="Johannesburg")
```

#### `AccountFactory`
Creates regular user accounts with realistic fake data.

```python
from app.Account.factories import AccountFactory

# Create with defaults
user = AccountFactory()

# Create with specific values
user = AccountFactory(
    email="user@example.com",
    password="custompass",
    first_name="John",
    last_name="Doe"
)

# Password defaults to "testpass123" if not specified
```

#### `SuperuserFactory`
Creates superuser accounts (staff + superuser permissions).

```python
from app.Account.factories import SuperuserFactory

admin = SuperuserFactory()
admin = SuperuserFactory(email="admin@example.com", password="adminpass")
```

#### `CompanyAccountFactory`
Creates company-type accounts with appropriate ownership and identification settings.

```python
from app.Account.factories import CompanyAccountFactory

company = CompanyAccountFactory()
assert company.ownership == Account.Ownership.COMPANY
assert company.identification_type == Account.IdentificationType.COMPANY
```

#### `TenantAccountFactory`
Creates tenant-type accounts.

```python
from app.Account.factories import TenantAccountFactory

tenant = TenantAccountFactory()
assert tenant.ownership == Account.Ownership.TENANT
```

### Project Factories (`app/Project/factories.py`)

#### `ProjectFactory`
Creates Project instances with an associated account.

```python
from app.Project.factories import ProjectFactory
from app.Account.factories import AccountFactory

# Create with auto-generated account
project = ProjectFactory()

# Create with specific account
account = AccountFactory()
project = ProjectFactory(account=account, name="My Project")

# Create soft-deleted project
project = ProjectFactory(deleted=True)
```

## Using Factories in Tests

### Basic Usage

```python
from app.Account.factories import AccountFactory
from app.Project.factories import ProjectFactory

def test_project_creation():
    """Test creating a project."""
    project = ProjectFactory(name="Test Project")
    assert project.name == "Test Project"
    assert project.account is not None
```

### Creating Multiple Objects

```python
def test_multiple_projects():
    """Test creating multiple projects for one account."""
    account = AccountFactory()
    projects = ProjectFactory.create_batch(5, account=account)
    assert len(projects) == 5
    assert all(p.account == account for p in projects)
```

### Using with Fixtures

Factories are integrated into pytest fixtures in `app/conftest.py`:

```python
def test_with_fixture(user, project):
    """Test using fixtures that use factories."""
    assert user.email == "testuser@example.com"
    assert project.account == user
```

## Factory Features

### Auto-Generated Data

Factories use `factory.Faker` and `factory.Sequence` to generate realistic, unique data:

- **Emails**: `user0@example.com`, `user1@example.com`, etc.
- **Names**: Realistic first and last names via Faker
- **Phone numbers**: Valid South African format
- **Addresses**: Realistic addresses via Faker

### SubFactories

Factories can automatically create related objects:

```python
# This automatically creates an Account
project = ProjectFactory()
assert project.account is not None
```

### Overriding Defaults

You can override any factory attribute:

```python
user = AccountFactory(
    email="custom@example.com",
    ownership=Account.Ownership.COMPANY,
    is_staff=True
)
```

### Build vs Create

```python
# Build: creates object in memory (not saved to DB)
user = AccountFactory.build()

# Create: saves object to database (default)
user = AccountFactory.create()
user = AccountFactory()  # Same as create()
```

## Running Tests

```bash
# Run all tests
.venv\Scripts\python.exe -m pytest

# Run specific test file
.venv\Scripts\python.exe -m pytest app/Project/tests/test_models.py -v

# Run with coverage
.venv\Scripts\python.exe -m pytest --cov=app --cov-report=html

# Run specific test
.venv\Scripts\python.exe -m pytest app/Project/tests/test_models.py::TestProjectModel::test_project_creation -v
```

## Best Practices

1. **Use factories instead of manual object creation** - More maintainable and less boilerplate
2. **Override only what you need** - Let factories handle the rest
3. **Use `create_batch` for multiple objects** - More efficient than loops
4. **Create specific factories for common scenarios** - Like `CompanyAccountFactory`
5. **Keep factories simple** - Complex logic belongs in tests, not factories

## Type Hints Note

The type checker (ty) may show warnings about factory attributes (e.g., `ProjectFactory has no attribute 'id'`). This is expected behavior - factories return model instances at runtime, but the type checker sees the factory class. These warnings can be safely ignored as the tests will work correctly.
