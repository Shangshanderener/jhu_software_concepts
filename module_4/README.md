# Module 4 - Testing and Documentation Experiment Assignment

**Author:** Zicheng Han

Grad Café Analytics with automated tests and Sphinx documentation.

## Setup

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (e.g. `postgresql://user:pass@host:5432/gradcafe`)
- Fallback: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

## Run Application

```bash

export DATABASE_URL=postgresql://...
python -m src.flask_app
# or: flask --app src.flask_app run
```

## Run Tests

```bash

export DATABASE_URL=postgresql://...
pytest -m "web or buttons or analysis or db or integration"
```

With coverage:
```bash
pytest -m "web or buttons or analysis or db or integration" --cov=src --cov-report=term-missing --cov-fail-under=100
```

## Documentation

See [docs](docs/) for Sphinx documentation. Published at: [Read the Docs link - add after publishing]

## CI

GitHub Actions workflow runs tests on push/PR. See `.github/workflows/tests.yml`.

## Deliverables Notes

- **CI Success Image**: Please add `actions_success.png` to this directory after a successful run.
- **ReadTheDocs**: [Insert Link Here]
