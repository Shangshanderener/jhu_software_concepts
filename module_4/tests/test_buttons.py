"""Button endpoints and busy-state behavior tests."""

import threading
import time

import pytest


@pytest.mark.buttons
def test_post_pull_data_returns_200(client_with_fake_loader, fake_scraper_loader):
    """POST /api/pull-data returns 200 when not busy and triggers loader."""
    client = client_with_fake_loader
    resp = client.post('/api/pull-data')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('ok') is True
    # Give background thread a moment to run
    time.sleep(0.2)
    assert fake_scraper_loader.called['count'] >= 1


@pytest.mark.buttons
def test_post_update_analysis_returns_200_when_not_busy(client):
    """POST /api/update-analysis returns 200 when not busy."""
    resp = client.post('/api/update-analysis')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('ok') is True
    assert data.get('success') is True


@pytest.mark.buttons
def test_post_update_analysis_returns_409_when_busy(client_with_fake_loader, fake_scraper_loader):
    """When pull is in progress, POST /api/update-analysis returns 409."""
    def slow_loader():
        time.sleep(0.5)
    app = __import__('src.flask_app', fromlist=['create_app']).create_app(scraper_loader_fn=slow_loader)
    c = app.test_client()
    # Start pull in background
    t = threading.Thread(target=lambda: c.post('/api/pull-data'))
    t.start()
    time.sleep(0.1)
    resp = c.post('/api/update-analysis')
    t.join()
    assert resp.status_code == 409
    data = resp.get_json()
    assert data.get('busy') is True


@pytest.mark.buttons
def test_post_pull_data_returns_409_when_busy(client_with_fake_loader, fake_scraper_loader):
    """When busy, POST /api/pull-data returns 409."""
    def slow_loader():
        time.sleep(0.5)
    app = __import__('src.flask_app', fromlist=['create_app']).create_app(scraper_loader_fn=slow_loader)
    c = app.test_client()
    t = threading.Thread(target=lambda: c.post('/api/pull-data'))
    t.start()
    time.sleep(0.05)
    resp = c.post('/api/pull-data')
    t.join()
    assert resp.status_code == 409
    data = resp.get_json()
    assert data.get('busy') is True
