Operational Notes
=================

Busy State Policy
-----------------

The application enforces a "busy gating" mechanism to prevent concurrent data operations that could lead to race conditions or resource exhaustion.

- **Pull Data**: When a data pull is initiated (via `POST /api/pull-data`), the application sets a global `is_running` flag. Any subsequent requests to `/api/pull-data` or `/api/update-analysis` while this flag is true will receive a ``409 Conflict`` response with ``{"busy": true}``.
- **Update Analysis**: Similarly, updating the analysis is blocked if a pull is in progress.

**Implementation**: The state is managed using a thread-safe `scraping_state` dictionary protected by a `threading.Lock`.

Idempotency Strategy
--------------------

To ensure data consistency and prevent duplicate entries, the application implements an idempotency strategy:

1. **Unique Key**: The ``url`` field in the ``applicants`` table is defined as ``UNIQUE``.
2. **Insert Logic**: The data loading process uses ``INSERT ... ON CONFLICT (url) DO NOTHING``.
3. **Behavior**: If a pull operation fetches an entry that already exists in the database (same URL), the database silently skips the insertion. This allows safe re-running of the scraper without duplicating data.

Uniqueness Keys
---------------

- **Primary Key**: ``p_id`` (SERIAL) - Internal database ID.
- **Business Key**: ``url`` (TEXT) - The direct link to the Grad Cafe entry. This is used to enforce uniqueness.
