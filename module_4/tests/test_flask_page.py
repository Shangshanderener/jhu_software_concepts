"""Flask app and page rendering tests."""

import pytest
from bs4 import BeautifulSoup


@pytest.mark.web
def test_app_factory_creates_app(app):
    """Test that create_app returns a Flask app with required routes."""
    assert app is not None
    rules = [r.rule for r in app.url_map.iter_rules()]
    assert '/' in rules
    assert '/analysis' in rules
    assert '/api/pull-data' in rules
    assert '/api/update-analysis' in rules
    assert '/api/scrape-status' in rules


@pytest.mark.web
def test_get_analysis_status_200(client):
    """GET /analysis returns status 200."""
    resp = client.get('/analysis')
    assert resp.status_code == 200


@pytest.mark.web
def test_get_root_also_serves_analysis(client):
    """GET / returns 200 (root also serves analysis page)."""
    resp = client.get('/')
    assert resp.status_code == 200


@pytest.mark.web
def test_page_contains_pull_data_button(client):
    """Page contains 'Pull Data' button."""
    resp = client.get('/analysis')
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.data, 'html.parser')
    pull_btn = soup.find(attrs={'data-testid': 'pull-data-btn'})
    assert pull_btn is not None
    assert 'Pull Data' in pull_btn.get_text()


@pytest.mark.web
def test_page_contains_update_analysis_button(client):
    """Page contains 'Update Analysis' button."""
    resp = client.get('/analysis')
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.data, 'html.parser')
    update_btn = soup.find(attrs={'data-testid': 'update-analysis-btn'})
    assert update_btn is not None
    assert 'Update Analysis' in update_btn.get_text()


@pytest.mark.web
def test_page_contains_analysis_text(client):
    """Page text includes 'Analysis'."""
    resp = client.get('/analysis')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert 'Analysis' in text


@pytest.mark.web
def test_page_contains_answer_label(client):
    """Page includes at least one 'Answer:' label."""
    resp = client.get('/analysis')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert 'Answer:' in text
