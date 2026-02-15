# Module 4 - Testing and Documentation Experiment Assignment

**Author:** Zicheng Han

Grad Café Analytics with automated tests, Sphinx documentation, and CI/CD.

## Project Structure

```
module_4/
├── src/               # Application code (Flask, ETL/DB, queries)
├── tests/             # Pytest suite
├── docs/              # Sphinx documentation source
├── .github/           # GitHub Actions workflows
├── pytest.ini         # Test configuration and markers
├── requirements.txt   # Project dependencies
└── README.md          # This file
```

## Setup

1. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Set the `DATABASE_URL` environment variable for local development with a real database:
```bash
export DATABASE_URL=postgresql://user:pass@host:5432/gradcafe
```
*Note: Tests will automatically use a mock backend if this variable is not set.*

## Running the Application

```bash
python -m src.flask_app
# Access at http://localhost:8080
```

## Running Tests

Run the full test suite (100% coverage required):

```bash
pytest -m "web or buttons or analysis or db or integration"
```

Generate coverage report:
```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=100
```

### Markers
- `web`: Flask route/page tests
- `buttons`: Button endpoints & busy-state behavior
- `analysis`: Analysis formatting/rounding
- `db`: Database schema/inserts/selects
- `integration`: End-to-end flows

## Documentation

- **Local Build**:
  ```bash
  sphinx-build -b html docs/source docs/build
  ```
- **Published Docs**: [Link to GitHub Pages]

## CI/CD

The GitHub Actions workflow (`.github/workflows/tests.yml`) performs:
1. **Tests**: Runs `pytest` against a PostgreSQL service container.
2. **Docs**: Builds and deploys Sphinx documentation to GitHub Pages (on `main` branch).

