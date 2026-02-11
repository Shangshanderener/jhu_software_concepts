"""End-to-end integration tests."""

import os
import time

import pytest
import psycopg
from bs4 import BeautifulSoup

from src.flask_app import create_app
from src import load_data, query_data


def _fake_records():
    return [
        {
            'program': 'Computer Science, MIT',
            'comments': 'e2e',
            'date_added': 'January 15, 2026',
            'url': 'https://example.com/e2e1',
            'status': 'Accepted',
            'term': 'Fall 2026',
            'US/International': 'American',
            'GPA': '3.85',
            'GRE': '325',
            'GRE_V': '165',
            'GRE_AW': '4.5',
            'Degree': 'PhD',
            'llm-generated-program': 'Computer Science',
            'llm-generated-university': 'MIT',
        },
    ]


@pytest.mark.integration
def test_e2e_pull_update_render(client):
    """End-to-end: pull -> update -> render shows updated analysis with correct formatting."""
    url = os.environ.get('DATABASE_URL')
    if not url:
        pytest.skip('DATABASE_URL not set')
    conn = psycopg.connect(url)
    try:
        load_data.create_table(conn.cursor())
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()

    def fake_loader():
        conn = psycopg.connect(os.environ['DATABASE_URL'])
        try:
            with conn.cursor() as cur:
                load_data.load_data(cur, _fake_records())
            conn.commit()
        finally:
            conn.close()

    app = create_app(scraper_loader_fn=fake_loader)
    c = app.test_client()

    resp_pull = c.post('/api/pull-data')
    assert resp_pull.status_code == 200
    
    # Poll for scraping completion
    max_retries = 20
    for _ in range(max_retries):
        time.sleep(0.5)
        status = c.get('/api/scrape-status').get_json()
        if not status['is_running']:
            break
    else:
        pytest.fail("Scraping did not complete in time")

    resp_update = c.post('/api/update-analysis')
    assert resp_update.status_code == 200

    resp_page = c.get('/analysis')
    assert resp_page.status_code == 200
    text = resp_page.get_data(as_text=True)
    
    # Debug output if assertion fails
    if 'Answer:' not in text:
        print("\n=== PAGE CONTENT DEBUG ===")
        print(text)
        print("==========================\n")
        
    assert 'Answer:' in text
    assert 'Analysis' in text
    # Percentages with two decimals
    import re
    assert re.search(r'\d+\.\d{2}%', text) or '0.00%' in text


@pytest.mark.integration
def test_multiple_pulls_overlapping_data_consistency():
    """Running POST /pull-data twice with overlapping data remains consistent."""
    url = os.environ.get('DATABASE_URL')
    if not url:
        pytest.skip('DATABASE_URL not set')
    conn = psycopg.connect(url)
    try:
        load_data.create_table(conn.cursor())
        conn.commit()
        with conn.cursor() as cur:
            cur.execute('TRUNCATE TABLE applicants RESTART IDENTITY')
        conn.commit()
        with conn.cursor() as cur:
            load_data.load_data(cur, _fake_records())
        conn.commit()
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM applicants')
            n1 = cur.fetchone()[0]
        with conn.cursor() as cur:
            load_data.load_data(cur, _fake_records())
        conn.commit()
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM applicants')
            n2 = cur.fetchone()[0]
        assert n1 == n2
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()
