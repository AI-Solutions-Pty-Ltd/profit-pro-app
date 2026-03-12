# Profit Pro - Django Application

A comprehensive Django-based application for managing construction projects, bills of quantities, payment certificates, and ledger transactions.

## Prerequisites

- Python 3.13+
- Node.js (for Tailwind CSS compilation)
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd profit-pro-app
```

### 2. Set Up Python Virtual Environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Configure Environment Variables

Copy the `.env.template` file to create your `.env` file:

```bash
cp .env.template .env
```

Edit the `.env` file with your configuration:

```env
# Django Settings
SITE_NAME=SEDGE BUILD
DJANGO_SETTINGS_MODULE=settings.local

# Static and Media Files Settings
STATIC_URL=/static/
STATIC_ROOT=staticfiles

# Database Settings (SQLite for development)
DB_TYPE=sqlite
DB=db.sqlite3
DB_HOST=
DB_USER=
DB_USER_PWD=

# Email Settings (optional for development)
USE_EMAIL=False
DEFAULT_FROM_EMAIL=
ADMIN_EMAIL=
DEFAULT_EMAIL_HOST=
EMAIL_HOST=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
```

### 4. Install Python Dependencies

```bash
# For local development
pip install -r requirements/local.txt

# For production
pip install -r requirements/prod.txt
```

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Create a Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 7. Install Frontend Dependencies (Tailwind CSS)

```bash
cd app/theme/static_src
npm install
cd ../../..
```

### 8. Run the Development Server

**Terminal 1 - Django Server:**

```bash
python manage.py runserver
```

**Terminal 2 - Tailwind CSS Watch (optional, for CSS changes):**

```bash
cd app/theme/static_src
npm run dev
```

### 9. Access the Application

- **Application:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin

## Project Structure

```
profit-pro-app/
├── app/                          # Django applications
│   ├── Account/                  # User account management
│   ├── BillOfQuantities/         # BOQ, payment certificates, ledgers
│   ├── Company/                  # Company management
│   ├── Cost/                     # Cost tracking
│   ├── Project/                  # Project management
│   ├── core/                     # Core utilities and base models
│   └── theme/                    # Tailwind CSS theme
├── requirements/                 # Python dependencies
│   ├── base.txt                  # Base requirements
│   ├── local.txt                 # Development requirements
│   ├── prod.txt                  # Production requirements
│   └── pdf.txt                   # PDF generation requirements
├── settings/                     # Django settings
│   ├── base.py                   # Base settings
│   ├── local.py                  # Development settings
│   ├── test.py                   # Test settings
│   └── prod.py                   # Production settings
├── .env.template                 # Environment variables template
├── .env                          # Your environment variables (not in git)
├── manage.py                     # Django management script
└── README.md                     # This file
```

## Environment Variables Reference

### Required Settings

| Variable                 | Description            | Example                |
| ------------------------ | ---------------------- | ---------------------- |
| `SITE_NAME`              | Name of your site      | `SEDGE BUILD`          |
| `DJANGO_SETTINGS_MODULE` | Django settings module | `settings.local`       |
| `DB_TYPE`                | Database type          | `sqlite` or `postgres` |
| `DB`                     | Database name/path     | `db.sqlite3`           |

### Optional Settings

| Variable        | Description                | Default     |
| --------------- | -------------------------- | ----------- |
| `DB_HOST`       | Database host              | `localhost` |
| `DB_USER`       | Database username          | -           |
| `DB_USER_PWD`   | Database password          | -           |
| `USE_EMAIL`     | Enable email functionality | `False`     |
| `EMAIL_HOST`    | SMTP server                | -           |
| `EMAIL_PORT`    | SMTP port                  | `587`       |
| `EMAIL_USE_TLS` | Use TLS encryption         | `True`      |

## Development Workflow

### Running Tests

```bash
# Run all tests
.venv\Scripts\python.exe -m pytest

# Run specific test file
.venv\Scripts\python.exe -m pytest app/Project/tests/test_models.py -v

# Run with coverage
.venv\Scripts\python.exe -m pytest --cov=app --cov-report=html
```

### Code Quality

```bash
# Lint code
.venv\Scripts\python.exe -m ruff check .

# Format code
.venv\Scripts\python.exe -m ruff format .
```

### Database Management

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development only)
python manage.py flush
```

### Static Files

```bash
# Collect static files (production)
python manage.py collectstatic --noinput
```

## Common Issues

### Virtual Environment Not Activating

**Windows:**
If you get an execution policy error, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Database Errors

If you encounter database errors, try:

```bash
# Delete the database file (development only)
rm db.sqlite3

# Delete migration files (be careful!)
# Then recreate migrations and migrate
python manage.py makemigrations
python manage.py migrate
```

### Static Files Not Loading

Ensure Tailwind CSS is compiled:

```bash
cd app/theme/static_src
npm run build
```

## Production Deployment

1. Set `DJANGO_SETTINGS_MODULE=settings.prod` in `.env`
2. Configure production database (PostgreSQL recommended)
3. Set `DEBUG=False`
4. Configure allowed hosts
5. Set up proper email settings
6. Run `python manage.py collectstatic`
7. Use a production WSGI server (gunicorn, uwsgi)
8. Set up reverse proxy (nginx, Apache)

## Contributing

1. Create a new branch for your feature
2. Write tests for new functionality
3. Ensure all tests pass
4. Follow the existing code style (use ruff)
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions, please contact [your contact information].
