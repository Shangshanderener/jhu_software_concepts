"""Test main blocks using runpy."""

import runpy
import sys
from unittest.mock import patch, MagicMock
import unittest.mock
import pytest

@pytest.mark.web
def test_flask_app_main():
    """Cover flask_app.py if __name__ == '__main__' block."""
    # Mock create_app and app.run
    with patch('src.flask_app.create_app') as mock_create:
        mock_app = MagicMock()
        mock_create.return_value = mock_app
        
        # We also need to mock app.run if it's called on the imported app object
        # The script does: app = create_app(); if main: main() -> app.run()
        # We need to mock 'src.flask_app.app' if possible, or just mock the run method on the instance
        
        # Since we use runpy, it executes the file.
        # We need to patch 'flask.Flask.run' because the app object is created inside.
        with patch('flask.Flask.run'):
             runpy.run_module('src.flask_app', run_name='__main__')

@pytest.mark.db
def test_load_data_main():
    """Cover load_data.py if __name__ == '__main__' block."""
    mock_psycopg = MagicMock()
    mock_conn = mock_psycopg.connect.return_value
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value
    mock_conn.__enter__.return_value = mock_conn
    
    with patch.dict(sys.modules, {'psycopg': mock_psycopg}), \
         patch('sys.argv', ['load_data.py', 'dummy.json']), \
         patch('builtins.open', unittest.mock.mock_open(read_data='[]')), \
         patch('json.load', return_value=[{}]):
         
         runpy.run_module('src.load_data', run_name='__main__')

@pytest.mark.db
def test_query_data_main():
    """Cover query_data.py if __name__ == '__main__' block."""
    # We patch sys.modules to mock psycopg completely BEFORE runpy imports it
    mock_psycopg = MagicMock()
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
    
    with patch.dict(sys.modules, {'psycopg': mock_psycopg}):
        runpy.run_module('src.query_data', run_name='__main__')

@pytest.mark.db
def test_query_data_main_mismatch():
    """Cover mismatch branch (lines 395)."""
    mock_psycopg = MagicMock()
    mock_conn = mock_psycopg.connect.return_value
    mock_cur = mock_conn.cursor.return_value.__enter__.return_value
    mock_conn.__enter__.return_value = mock_conn
    
    # Q8 (idx 7) != Q9 (idx 8)
    # Sequence: Q1..Q7, Q8, Q9, Q8(again), Q10, Q11
    side_effect = [[(10,)]]*7 + [[(3,)], [(4,)], [(3,)]] + [[(10,)]]*2
    # Adjust for return types of Q10/Q11 (list of tuples) to avoid index error
    # Q1..Q7: single value
    # Q8, Q9, Q8: single value
    # Q10: list of tuples with 4 elements
    # Q11: list of tuples with 4 elements
    side_effect = [
        [(10,)], [(10.0,)], [(3.5, 300, 150, 3.5)], [(3.5,)], [(10.0,)], [(3.5,)], [(10,)], # 1-7
        [(3,)], # Q8
        [(4,)], # Q9 (Different!)
        [(3,)], # Q8 (again)
        [('Uni', 20, 10, 50.0)], # Q10
        [('PhD', 10, 3.5, 50.0)] # Q11
    ]
    mock_cur.fetchall.side_effect = side_effect
    
    with patch.dict(sys.modules, {'psycopg': mock_psycopg}):
        runpy.run_module('src.query_data', run_name='__main__')
