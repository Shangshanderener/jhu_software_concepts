import os
import unittest
import pytest
from unittest.mock import patch, MagicMock
from src import query_data

@pytest.mark.db
class TestQueryDataConnection(unittest.TestCase):
    """Test the database connection logic in query_data.py."""

    @patch('src.query_data.psycopg.connect')
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@host:5432/db'}, clear=True)
    def test_get_connection_with_env_var(self, mock_connect):
        """Test get_connection uses DATABASE_URL if present."""
        query_data.get_connection()
        mock_connect.assert_called_with('postgresql://user:pass@host:5432/db')

    @patch('src.query_data.psycopg.connect')
    @patch.dict(os.environ, {}, clear=True)
    def test_get_connection_fallback(self, mock_connect):
        """Test get_connection falls back to individual params if DATABASE_URL is missing."""
        # Ensure DATABASE_URL is not set (redundant check for safety)
        os.environ.pop('DATABASE_URL', None)
            
        query_data.get_connection()
        
        # Verify it calls with default fallback values
        mock_connect.assert_called_with(
            dbname='gradcafe',
            user='postgres',
            password='',
            host='localhost',
            port='5432'
        )

    @patch('src.query_data.psycopg.connect')
    @patch.dict(os.environ, {
        'DB_NAME': 'custom_db',
        'DB_USER': 'custom_user',
        'DB_PASSWORD': 'custom_password',
        'DB_HOST': 'custom_host',
        'DB_PORT': '5433'
    }, clear=True)
    def test_get_connection_fallback_custom(self, mock_connect):
        """Test get_connection fallback uses provided env vars."""
        # Ensure DATABASE_URL is not set
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
            
        query_data.get_connection()
        
        mock_connect.assert_called_with(
            dbname='custom_db',
            user='custom_user',
            password='custom_password',
            host='custom_host',
            port='5433'
        )
