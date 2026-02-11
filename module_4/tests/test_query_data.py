"""Unit tests for query_data.py with mocking."""

from unittest.mock import MagicMock, patch
import pytest
from src import query_data

@pytest.fixture
def mock_db_execution():
    """Fixture to mock execute_query and return specific results."""
    with patch('src.query_data.execute_query') as mock_exec:
        yield mock_exec

@pytest.mark.db
def test_get_connection_env():
    with patch.dict('os.environ', {'DATABASE_URL': 'postgres://fake'}):
        with patch('psycopg.connect') as mock_connect:
            query_data.get_connection()
            mock_connect.assert_called_with('postgres://fake')

@pytest.mark.db
def test_execute_query():
    with patch('psycopg.connect') as mock_connect:
        mock_cur = mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = [('res',)]
        
        res = query_data.execute_query("SELECT 1")
        assert res == [('res',)]
        mock_cur.execute.assert_called_with("SELECT 1", None)

@pytest.mark.db
def test_q1_fall_2026_count(mock_db_execution):
    mock_db_execution.return_value = [(10,)]
    assert query_data.q1_fall_2026_count() == 10
    
    mock_db_execution.return_value = []
    assert query_data.q1_fall_2026_count() == 0

@pytest.mark.db
def test_q2_international_percentage(mock_db_execution):
    mock_db_execution.return_value = [(25.5,)]
    assert query_data.q2_international_percentage() == 25.5
    
    mock_db_execution.return_value = []
    assert query_data.q2_international_percentage() == 0

@pytest.mark.db
def test_q3_average_scores(mock_db_execution):
    mock_db_execution.return_value = [(3.8, 320, 160, 4.0)]
    res = query_data.q3_average_scores()
    assert res['avg_gpa'] == 3.8
    assert res['avg_gre'] == 320
    
    mock_db_execution.return_value = []
    assert query_data.q3_average_scores() is None

@pytest.mark.db
def test_q4_american_fall_2026_gpa(mock_db_execution):
    mock_db_execution.return_value = [(3.7,)]
    assert query_data.q4_american_fall_2026_gpa() == 3.7
    
    mock_db_execution.return_value = []
    assert query_data.q4_american_fall_2026_gpa() is None

@pytest.mark.db
def test_q5_fall_2025_acceptance_rate(mock_db_execution):
    mock_db_execution.return_value = [(40.0,)]
    assert query_data.q5_fall_2025_acceptance_rate() == 40.0
    
    mock_db_execution.return_value = []
    assert query_data.q5_fall_2025_acceptance_rate() == 0

@pytest.mark.db
def test_q6_fall_2026_accepted_gpa(mock_db_execution):
    mock_db_execution.return_value = [(3.9,)]
    assert query_data.q6_fall_2026_accepted_gpa() == 3.9
    
    mock_db_execution.return_value = []
    assert query_data.q6_fall_2026_accepted_gpa() is None

@pytest.mark.db
def test_q7_jhu_masters_cs_count(mock_db_execution):
    mock_db_execution.return_value = [(5,)]
    assert query_data.q7_jhu_masters_cs_count() == 5
    
    mock_db_execution.return_value = []
    assert query_data.q7_jhu_masters_cs_count() == 0

@pytest.mark.db
def test_q8_elite_phd_cs_2026_accepts(mock_db_execution):
    mock_db_execution.return_value = [(3,)]
    assert query_data.q8_elite_phd_cs_2026_accepts() == 3
    
    mock_db_execution.return_value = []
    assert query_data.q8_elite_phd_cs_2026_accepts() == 0

@pytest.mark.db
def test_q9_elite_phd_cs_2026_llm_accepts(mock_db_execution):
    mock_db_execution.return_value = [(3,)]
    assert query_data.q9_elite_phd_cs_2026_llm_accepts() == 3
    
    mock_db_execution.return_value = []
    assert query_data.q9_elite_phd_cs_2026_llm_accepts() == 0

@pytest.mark.db
def test_q10_top_universities(mock_db_execution):
    result = [('MIT', 50, 25, 50.0)]
    mock_db_execution.return_value = result
    assert query_data.q10_top_universities_by_acceptance_rate() == result

@pytest.mark.db
def test_q11_stats_by_degree(mock_db_execution):
    result = [('PhD', 100, 3.8, 20.0)]
    mock_db_execution.return_value = result
    assert query_data.q11_stats_by_degree_type() == result

@pytest.mark.db
def test_get_all_results():
    # Helper to return a mock for each call
    # We have 11 calls.
    # q1, q2 -> scalar inside list of tuple
    # q3 -> tuple inside list
    # q4, q5, q6, q7, q8, q9 -> scalar inside list of tuple
    # q10, q11 -> list of tuples
    
    responses = [
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
    
    with patch('src.query_data.execute_query', side_effect=responses):
        results = query_data.get_all_results()
        assert results['q1'] == 10
        assert results['q2'] == 25.0
        assert results['q3']['avg_gpa'] == 3.8
        assert results['q10'][0][0] == 'MIT'
