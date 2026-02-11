"""Unit tests for load_data.py."""

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from src import load_data


@pytest.mark.db
def test_parse_date():
    assert load_data.parse_date("January 30, 2026") == datetime(2026, 1, 30)
    assert load_data.parse_date("InvalidDate") is None
    assert load_data.parse_date(None) is None


@pytest.mark.db
def test_parse_float():
    assert load_data.parse_float("GPA 3.9") == 3.9
    assert load_data.parse_float("159") == 159.0
    assert load_data.parse_float("No number") is None
    assert load_data.parse_float(None) is None


@pytest.mark.db
def test_parse_decision():
    assert load_data.parse_decision("Accepted on 15 Jan") == "Accepted"
    assert load_data.parse_decision("Rejected via email") == "Rejected"
    assert load_data.parse_decision("Interview invite") == "Interview"
    assert load_data.parse_decision("Wait listed") == "Waitlisted"
    assert load_data.parse_decision("OtherStatus") == "OtherStatus"
    assert load_data.parse_decision(None) is None


@pytest.mark.db
def test_parse_decision_date():
    # Test valid dates
    d = load_data.parse_decision_date("Accepted on 29 Jan", "Fall 2026")
    assert d.day == 29 and d.month == 1 and d.year == 2026

    # Test month full name
    d = load_data.parse_decision_date("Rejected on 15 February", "Fall 2025")
    assert d.day == 15 and d.month == 2 and d.year == 2025
    
    # Test invalid format
    assert load_data.parse_decision_date("No date here", "Fall 2026") is None
    assert load_data.parse_decision_date(None, None) is None


@pytest.mark.db
def test_extract_university():
    assert load_data.extract_university("CS, MIT") == "MIT"
    assert load_data.extract_university("CS, University of Washington, Seattle") == "University of Washington, Seattle"
    assert load_data.extract_university("JustProgram") is None
    assert load_data.extract_university(None) is None


@pytest.mark.db
def test_extract_program():
    assert load_data.extract_program("CS, MIT") == "CS"
    assert load_data.extract_program("JustProgram") == "JustProgram"
    assert load_data.extract_program(None) is None


@pytest.mark.db
def test_get_is_american():
    assert load_data.get_is_american("American") == "American"
    assert load_data.get_is_american("International") == "International"
    assert load_data.get_is_american("Other") == "Other"
    assert load_data.get_is_american(None) == "Other"


@pytest.mark.db
def test_create_table():
    mock_cur = MagicMock()
    load_data.create_table(mock_cur)
    mock_cur.execute.assert_called_once()
    assert "CREATE TABLE IF NOT EXISTS applicants" in mock_cur.execute.call_args[0][0]


@pytest.mark.db
def test_load_data_logic():
    mock_cur = MagicMock()
    data = [{
        'program': 'CS, MIT',
        'comments': 'test',
        'date_added': 'January 15, 2026',
        'url': 'http://example.com',
        'status': 'Accepted',
        'term': 'Fall 2026',
        'US/International': 'American',
        'GPA': '3.9',
        'GRE': '320',
        'GRE_V': '160',
        'GRE_AW': '4.0',
        'Degree': 'PhD',
        'llm-generated-program': 'CS',
        'llm-generated-university': 'MIT',
    }]
    count = load_data.load_data(mock_cur, data)
    assert count == 1
    mock_cur.execute.assert_called_once()
    sql = mock_cur.execute.call_args[0][0]
    logging_args = mock_cur.execute.call_args[0][1]
    assert "INSERT INTO applicants" in sql
    assert logging_args[0] == 'CS, MIT'  # program
    assert logging_args[6] == 'American'  # us_or_international


@pytest.mark.db
def test_main_functionality():
    # Mock sys.argv, os.path, open, json.load, psycopg.connect
    with patch.object(sys, 'argv', ['script_name', 'dummy.json']), \
         patch('builtins.open'), \
         patch('json.load', return_value=[{}]), \
         patch('psycopg.connect') as mock_connect:
        
        mock_conn = mock_connect.return_value
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        
        load_data.main()
        
        mock_connect.assert_called()
        mock_cur.execute.assert_called()  # create_table and insert
        mock_conn.commit.assert_called()
        mock_conn.close.assert_called()

@pytest.mark.db
def test_get_connection_uses_env():
    with patch.dict('os.environ', {'DATABASE_URL': 'postgres://fake'}):
         with patch('psycopg.connect') as mock_connect:
             load_data.get_connection()
             mock_connect.assert_called_with('postgres://fake')

@pytest.mark.db
def test_get_connection_uses_defaults():
    with patch.dict('os.environ', {}, clear=True):
         with patch('psycopg.connect') as mock_connect:
             load_data.get_connection()
             _, kwargs = mock_connect.call_args
             assert kwargs.get('dbname') == 'gradcafe'
