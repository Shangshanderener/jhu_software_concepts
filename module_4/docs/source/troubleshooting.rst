Troubleshooting
===============

Common Issues
-------------

**1. "Database Error" on Analysis Page**

*   **Symptom**: The page shows "Database Error" or returns 500.
*   **Cause**: The application cannot connect to the PostgreSQL database.
*   **Fix**:
    *   Ensure PostgreSQL is running.
    *   Check that ``DATABASE_URL`` environment variable is set correctly.
    *   Verify credentials in the connection string.

**2. "Scraping failed" Message**

*   **Symptom**: The status banner shows "Scraping failed".
*   **Cause**: The background scraper process exited with a non-zero code.
*   **Fix**:
    *   Check console logs for detailed error messages.
    *   Ensure network connectivity (if scraping real site).
    *   Ensure ``module_2/scrape.py`` and dependencies are installed.

**3. "Busy" Response (409)**

*   **Symptom**: "Pull Data" or "Update Analysis" buttons are disabled or return errors.
*   **Cause**: A scraping operation is already in progress.
*   **Fix**:
    *   Wait for the current operation to finish.
    *   If stuck (e.g., app crashed during scrape), restart the Flask application to reset the state.

**4. Tests Failing**

*   **Symptom**: ``pytest`` reports failures.
*   **Fix**:
    *   Ensure ``DATABASE_URL`` is set for integration/DB tests.
    *   Check that no other process is holding a lock on the DB (though tests usually use separate tables or are fast).
    *   Verify Python environment (``venv`` active).

CI/CD Issues
------------

*   **GitHub Actions Fails**: Check the "Run Tests" step output. Verify that the PostgreSQL service container started successfully.
