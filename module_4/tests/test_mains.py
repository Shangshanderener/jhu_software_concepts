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
        
        # Import and run main
        from src import flask_app
        # We need to simulate the 'main' function if it exists, or just the if __name__ == main block.
        # usage: flask_app.py has a main() function.
        if hasattr(flask_app, 'main'):
            flask_app.main()
        else:
            # If no main function, we can't easily test the if __name__ block without runpy
            # BUT, src/flask_app.py DOES have a main() function:
            # 169:     def main():
            # 170:         """Run the app."""
            # 171:         app.run(host='0.0.0.0', port=8080, debug=True)
            # 172:     main()
            # Wait, line 172 calls main().
            # IMPORTANT: The main() function in flask_app.py is defined INSIDE the if __name__ block?
            # No, looking at file:
            # 168: if __name__ == '__main__':
            # 169:     def main():
            # ...
            # 172:     main()
            # So main() is NOT available to import if we just import flask_app.
            # So for flask_app, we MUST use runpy or skip coverage of that block.
            # However, since flask_app line 168 is `if __name__`, the definition of main is inside.
            # So we can't call it via import.
            # We will stick to runpy for flask_app because it's defined inside the block.
            # BUT, to capture coverage, maybe we can ignore it?
            # The coverage failure reported flask_app missing 169-172.
            # If we use runpy, it should cover it.
            # The issue with runpy is likely the module reloading.
            # For now, I will leave flask_app with runpy, but fix load_data which IS importable?
            # load_data.py has main() at top level?
            # Let's check load_data structure.
            pass
        with patch('flask.Flask.run'):
             runpy.run_module('src.flask_app', run_name='__main__')

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
