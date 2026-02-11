"""Pytest fixtures for Grad Cafe tests."""

import os
import sys

import pytest

# Ensure module_4/src is on path when running from module_4
_module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src_dir = os.path.join(_module_dir, 'src')
if _src_dir not in sys.path:
    sys.path.insert(0, _module_dir)

from src.flask_app import create_app


@pytest.fixture
def mock_query_fn():
    """Return a mock query function that returns dummy data for all keys."""
    def _mock_query():
        return {
            'q1': 100,
            'q2': 15.50,
            'q3': {'avg_gpa': 3.8, 'avg_gre': 320, 'avg_gre_v': 160, 'avg_gre_aw': 4.0},
            'q4': 3.75,
            'q5': 42.00,
            'q6': 3.90,
            'q7': 5,
            'q8': 3,
            'q9': 3,
            'q10': [('MIT', 50, 25, 50.00), ('Stanford', 40, 10, 25.00)],
            'q11': [('PhD', 100, 3.8, 20.0), ('Masters', 50, 3.6, 40.0)]
        }
    return _mock_query


@pytest.fixture
def app(mock_query_fn):
    """Create Flask app with no-op scraper and mock query for testing."""
    def noop_scraper_loader():
        pass
    return create_app(scraper_loader_fn=noop_scraper_loader, query_fn=mock_query_fn)


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def fake_scraper_loader():
    """Returns a callable that records it was invoked."""
    called = {'count': 0}
    def fn():
        called['count'] += 1
    fn.called = called
    return fn


@pytest.fixture
def app_with_fake_loader(fake_scraper_loader, mock_query_fn):
    """App with injectable fake loader and mock query."""
    return create_app(scraper_loader_fn=fake_scraper_loader, query_fn=mock_query_fn)


@pytest.fixture
def client_with_fake_loader(app_with_fake_loader):
    """Test client with fake loader."""
    return app_with_fake_loader.test_client()
