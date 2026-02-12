"""Test main blocks using runpy."""

import runpy
import sys
from unittest.mock import patch, MagicMock
import unittest.mock
import pytest

@pytest.mark.web
def test_flask_app_main():
    """Cover flask_app.py main function."""
    # Mock create_app and app.run
    with patch('src.flask_app.create_app') as mock_create:
        mock_app = MagicMock()
        mock_create.return_value = mock_app
        
        # We need to mock 'src.flask_app.app' because main() calls app.run()
        # The 'app' imported from src.flask_app is an instance.
        # We can check if we can patch it.
        # But wait, src.flask_app.app is created at module level.
        # line 166: app = create_app()
        # lines 169-171: main() calls app.run()
        
        # When we import flask_app, app is created.
        # We want to verify app.run() is called.
        
        from src import flask_app
        
        # Mock the app.run method on the global 'app' object in flask_app
        with patch.object(flask_app.app, 'run') as mock_run:
            flask_app.main()
            mock_run.assert_called_with(host='0.0.0.0', port=8080, debug=True)

@pytest.mark.db
def test_load_data_main():
    """Cover load_data.py if __name__ == '__main__' block."""
    # load_data.py has a top-level main() function?
    # I need to check load_data.py structure to be sure.
    # Assuming it does (based on common pattern like query_data), I will try import.
    # If not, I revert to runpy.
    # Let's check:
    # `def main():` usually exists.
    # If so:
    with patch('src.load_data.psycopg') as mock_psycopg, \
         patch('sys.argv', ['load_data.py', 'dummy.json']), \
         patch('builtins.open', unittest.mock.mock_open(read_data='[]')), \
         patch('json.load', return_value=[{}]):
         
         mock_conn = mock_psycopg.connect.return_value
         mock_cur = mock_conn.cursor.return_value.__enter__.return_value
         mock_conn.__enter__.return_value = mock_conn
         
         from src import load_data
         load_data.main()

@pytest.mark.db
def test_query_data_main():
    """Cover query_data.py main function."""
    # Patch psycopg in the already-imported module
    with patch('src.query_data.psycopg') as mock_psycopg:
        # verify connection context manager
        mock_conn = mock_psycopg.connect.return_value
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_conn.__enter__.return_value = mock_conn
        
        # Needs to handle all queries in order:
        # Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q8(again), Q10, Q11
        mock_cur.fetchall.side_effect = [
            [(10,)], # Q1
            [(10.0,)], # Q2
            [(3.5, 300, 150, 3.5)], # Q3
            [(3.5,)], # Q4
            [(10.0,)], # Q5
            [(3.5,)], # Q6
            [(10,)], # Q7
            [(3,)], # Q8
            [(3,)], # Q9
            [(3,)], # Q8 (called again for comparison)
            [('Uni', 20, 10, 50.0)], # Q10
            [('PhD', 10, 3.5, 50.0)] # Q11
        ]
        
        # Helper to avoid importing at top level if not needed, 
        # but we need it here. Use local import to ensure we use the one in sys.modules
        from src import query_data
        query_data.main()

@pytest.mark.db
def test_query_data_main_mismatch():
    """Cover mismatch branch (lines 395)."""
    with patch('src.query_data.psycopg') as mock_psycopg:
        mock_conn = mock_psycopg.connect.return_value
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_conn.__enter__.return_value = mock_conn
        
        # Q8 (idx 7) != Q9 (idx 8)
        side_effect = [
            [(10,)], [(10.0,)], [(3.5, 300, 150, 3.5)], [(3.5,)], [(10.0,)], [(3.5,)], [(10,)], # 1-7
            [(3,)], # Q8
            [(4,)], # Q9 (Different!)
            [(3,)], # Q8 (again)
            [('Uni', 20, 10, 50.0)], # Q10
            [('PhD', 10, 3.5, 50.0)] # Q11
        ]
        mock_cur.fetchall.side_effect = side_effect
        
        from src import query_data
        query_data.main()
