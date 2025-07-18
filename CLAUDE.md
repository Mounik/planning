# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

Install dependencies and run the application:

- `uv sync --dev` - Install all dependencies
- `uv run python main.py` - Start the application
- `uv run black src/` - Format code with black
- `uv run flake8 src/` - Check code style
- `uv run mypy src/planning_pro` - Type checking

## Project Architecture

This is a Flask-based time management application with server-side rendered HTML templates:

### Backend (Python/Flask)
- **Core App**: `src/planning_pro/app.py` - Main Flask application with routes
- **Models**: `src/planning_pro/models.py` - Data models with SQLite storage
- **Database**: `src/planning_pro/database.py` - SQLite database manager
- **Config**: `src/planning_pro/config.py` - Application configuration
- **Salary Calculator**: `src/planning_pro/salary_calculator.py` - Advanced salary calculations
- **Net Salary Calculator**: `src/planning_pro/net_salary_calculator.py` - Net salary estimation
- **PDF Generator**: `src/planning_pro/pdf_generator.py` - PDF generation for timesheets
- **Security**: `src/planning_pro/security.py` - Security utilities and helpers

### Frontend (HTML Templates)
- **Templates**: `templates/` - Jinja2 HTML templates

### Data Storage
- Uses SQLite database in `data/planning.db` for persistence
- Schema includes: users, plannings, jours_travail, creneaux_travail, feuilles_heures, jours_travailles, creneaux_feuille
- Database operations handled via `database.py` module

### Key Models
- **User**: Authentication with bcrypt, Flask-Login integration
- **Planning**: Work schedules with time slots and hourly rates
- **FeuilleDHeures**: Time sheets converted from plannings with salary calculations
- **CreneauTravail**: Work time slots with start/end times
- **JourTravaille**: Work days containing multiple time slots

### Application Flow
1. Users authenticate via Flask-Login
2. Create work plannings with time slots
3. Convert plannings to time sheets for salary calculation
4. Calculate normal hours, overtime, and total pay

## Entry Points

- `main.py` - Development entry point (runs Flask app with debug mode)
- `run_prod.py` - Production entry point (runs Flask app with Gunicorn)

## Testing

Comprehensive test suite implemented with pytest:

### Test Structure
- **tests/conftest.py** - Test configuration and fixtures
- **tests/test_models.py** - Unit tests for data models
- **tests/test_api.py** - API endpoint tests
- **tests/test_security.py** - Security validation tests
- **tests/test_salary_calculator.py** - Salary calculation tests
- **tests/test_integration.py** - Integration workflow tests

### Test Categories
- **Unit tests** - Individual components (models, calculators, security)
- **API tests** - All endpoints with authentication and validation
- **Integration tests** - Complete user workflows
- **Security tests** - Input validation, sanitization, schema validation

### Running Tests
```bash
# All tests
uv run pytest tests/

# With coverage
uv run pytest tests/ --cov

# By category
uv run pytest tests/ -m unit          # Unit tests only
uv run pytest tests/ -m integration   # Integration tests only
uv run pytest tests/ -m security      # Security tests only
uv run pytest tests/ -m api           # API tests only

# Coverage requirements
uv run pytest tests/ --cov --cov-fail-under=80
```

### Test Coverage
- Models: User, Planning, CreneauTravail, JourTravaille, FeuilleDHeures
- APIs: Authentication, Planning CRUD, Feuille heures, Contracts
- Security: Input validation, password hashing, data sanitization
- Calculators: Salary calculations for all contract types (20h, 25h, 30h, 35h, 39h)
- Integration: Complete user workflows from registration to salary calculation

## Code Style

- Python: Uses black for formatting, flake8 for linting, mypy for type checking
- HTML Templates: Uses Jinja2 templating engine
- All formatting and linting must pass before commits

## CI/CD Pipeline

GitHub Actions workflow (.github/workflows/ci.yml) provides:

### Automated Testing
- **Multi-Python versions** - Tests on Python 3.8, 3.9, 3.10, 3.11
- **Code quality** - Black formatting, flake8 linting, mypy type checking
- **Test execution** - Full pytest suite with coverage reporting
- **Security scanning** - Safety vulnerability checks, Bandit security analysis

### Pipeline Stages
1. **Test** - Unit tests, integration tests, coverage analysis
2. **Security** - Vulnerability scanning, security code analysis
3. **Build** - Application build verification, artifact creation
4. **Integration** - Application startup tests, endpoint validation
5. **Performance** - Basic load testing with Apache Bench

### Quality Gates
- **Test coverage** - Minimum 80% code coverage required
- **Security** - No high-severity vulnerabilities allowed
- **Code quality** - All linting and formatting checks must pass
- **Type safety** - MyPy type checking must pass

### Artifacts
- **Build packages** - Application deployment artifacts
- **Security reports** - Vulnerability and security scan results
- **Coverage reports** - Test coverage analysis with Codecov integration