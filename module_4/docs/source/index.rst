Grad Cafe Analytics
===================

Overview
--------

Grad Cafe Analytics is a web application that scrapes admission data from The Grad Cafe,
cleans and standardizes it, loads it into PostgreSQL, and presents analysis results.

Setup
-----

Requirements: Python 3.11+, PostgreSQL

Install dependencies:

.. code-block:: bash

   pip install -r requirements.txt

Environment variables:

- **DATABASE_URL**: PostgreSQL connection string (e.g. ``postgresql://user:pass@host:5432/gradcafe``)
- Fallback: ``DB_NAME``, ``DB_USER``, ``DB_PASSWORD``, ``DB_HOST``, ``DB_PORT``

Run the application:

.. code-block:: bash

   export DATABASE_URL=postgresql://...
   python -m src.flask_app

How to Run Tests
----------------

.. code-block:: bash

   cd module_4
   export DATABASE_URL=postgresql://...
   pytest -m "web or buttons or analysis or db or integration"

With coverage (100% required):

.. code-block:: bash

   pytest -m "web or buttons or analysis or db or integration" --cov=src --cov-report=term-missing --cov-fail-under=100

Pytest markers: ``web``, ``buttons``, ``analysis``, ``db``, ``integration``.

Architecture
------------

- **Web (Flask)**: Serves the Analysis page with "Pull Data" and "Update Analysis" buttons.
  Routes: ``/``, ``/analysis``, ``/api/pull-data``, ``/api/update-analysis``, ``/api/scrape-status``.

- **ETL**: Scrape (module_2/scrape.py) → Clean (module_2/clean.py) → LLM standardize (module_2/llm_hosting) → Load (load_data.py).

- **DB**: PostgreSQL with ``applicants`` table. Query module (query_data.py) provides analysis results.

API Reference
-------------

.. toctree::
   :maxdepth: 2

   modules/scrape
   modules/clean
   modules/load_data
   modules/query_data
   modules/flask_app

Testing Guide
-------------

- **Markers**: All tests use one of ``web``, ``buttons``, ``analysis``, ``db``, ``integration``.
- **Selectors**: UI tests use ``data-testid="pull-data-btn"`` and ``data-testid="update-analysis-btn"``.
- **Fixtures**: ``conftest.py`` provides ``app``, ``client``, ``fake_scraper_loader``, ``app_with_fake_loader``.
- **DB tests**: Require ``DATABASE_URL``; use fake data and skip when not set.
