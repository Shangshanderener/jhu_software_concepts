"""Database schema, inserts, and query tests."""

import os
import tempfile

import pytest
import psycopg

from src import load_data, query_data
import unittest.mock


def _get_connection():
    """Get DB connection for tests."""
    url = os.environ.get('DATABASE_URL')
    if not url:
        pytest.skip('DATABASE_URL not set; skipping DB tests')
    return psycopg.connect(url)


def _ensure_table(conn):
    """Ensure applicants table exists."""
    with conn.cursor() as cur:
        load_data.create_table(cur)
    conn.commit()


def _count_rows(conn):
    """Count rows in applicants table."""
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM applicants')
        return cur.fetchone()[0]


def _truncate(conn):
    """Truncate applicants table."""
    with conn.cursor() as cur:
        cur.execute('TRUNCATE TABLE applicants RESTART IDENTITY')
    conn.commit()


def _fake_records():
    """Return fake applicant records for testing."""
    return [
        {
            'program': 'Computer Science, MIT',
            'comments': 'test',
            'date_added': 'January 15, 2026',
            'url': 'https://example.com/entry1',
            'status': 'Accepted',
            'term': 'Fall 2026',
            'US/International': 'American',
            'GPA': '3.9',
            'GRE': '',
            'GRE_V': '',
            'GRE_AW': '',
            'Degree': 'Masters',
            'llm-generated-program': 'Computer Science',
            'llm-generated-university': 'MIT',
        },
        {
            'program': 'CS, Stanford',
            'comments': 'test2',
            'date_added': 'January 20, 2026',
            'url': 'https://example.com/entry2',
            'status': 'Rejected',
            'term': 'Fall 2026',
            'US/International': 'International',
            'GPA': '',
            'GRE': '320',
            'GRE_V': '160',
            'GRE_AW': '4.0',
            'Degree': 'PhD',
            'llm-generated-program': 'Computer Science',
            'llm-generated-university': 'Stanford',
        },
    ]


@pytest.mark.db
def test_insert_on_pull_target_table_empty_before(client_with_fake_loader):
    """Before pull, target table can be empty; after POST /pull-data new rows exist."""
    url = os.environ.get('DATABASE_URL')
    if not url:
        pytest.skip('DATABASE_URL not set')
    conn = psycopg.connect(url)
    try:
        _ensure_table(conn)
        _truncate(conn)
        assert _count_rows(conn) == 0
    finally:
        conn.close()

    # Use app with loader that actually inserts
    import json
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(_fake_records(), f)
        data_file = f.name
    try:
        def loader():
            conn = _get_connection()
            try:
                with conn.cursor() as cur:
                    load_data.create_table(cur)
                    load_data.load_data(cur, _fake_records())
                conn.commit()
            finally:
                conn.close()
        from src.flask_app import create_app
        app = create_app(scraper_loader_fn=loader)
        c = app.test_client()
        resp = c.post('/api/pull-data')
        assert resp.status_code == 200
        import time
        time.sleep(0.3)  # Wait for loader thread
        conn2 = _get_connection()
        try:
            count = _count_rows(conn2)
            assert count >= 2
        finally:
            conn2.close()
    finally:
        os.unlink(data_file)


@pytest.mark.db
def test_idempotency_duplicate_pulls_no_duplicates():
    """Duplicate rows do not create duplicates (uniqueness on url)."""
    url = os.environ.get('DATABASE_URL')
    if not url:
        pytest.skip('DATABASE_URL not set')
    conn = _get_connection()
    try:
        _ensure_table(conn)
        _truncate(conn)
        with conn.cursor() as cur:
            load_data.load_data(cur, _fake_records())
        conn.commit()
        count1 = _count_rows(conn)
        with conn.cursor() as cur:
            load_data.load_data(cur, _fake_records())
        conn.commit()
        count2 = _count_rows(conn)
        assert count1 == count2
    finally:
        conn.close()


@pytest.mark.db
def test_query_function_returns_expected_keys():
    """Query function returns dict with expected keys (Module-3 required fields)."""
    # Mock get_all_results to avoid DB connection, just test the key structure
    # But wait, the test wants to test the actual function logic? 
    # The original test called query_data.get_all_results() which calls q1...q11.
    # We should mock execute_query inside it if we want to test the orchestration.
    
    with unittest.mock.patch('src.query_data.execute_query') as mock_exec:
        # We need to provide return values for all 11 queries
        # returns list of tuples
        mock_exec.side_effect = [
             [(10,)], # q1
            [(25.0,)], # q2
            [(3.8, 320, 160, 4.0)], # q3
            [(3.7,)], # q4
            [(40.0,)], # q5
            [(3.9,)], # q6
            [(5,)], # q7
            [(3,)], # q8
            [(3,)], # q9
            [('MIT', 50, 25, 50.0)], # q10
            [('PhD', 100, 3.8, 20.0)], # q11
        ]
        
        expected = {'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9', 'q10', 'q11'}
        result = query_data.get_all_results()
        assert isinstance(result, dict)
        assert expected.issubset(set(result.keys()))
