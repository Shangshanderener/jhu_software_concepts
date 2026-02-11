"""Analysis labels and percentage formatting tests."""

import re

import pytest
from bs4 import BeautifulSoup


@pytest.mark.analysis
def test_page_has_answer_labels(client):
    """Page includes 'Answer' labels for rendered analysis."""
    resp = client.get('/analysis')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert 'Answer:' in text
    # Multiple Answer labels (one per question)
    assert text.count('Answer:') >= 1


@pytest.mark.analysis
def test_percentages_formatted_with_two_decimals(client):
    """Any percentage on page is formatted with two decimals (e.g., 39.28%)."""
    resp = client.get('/analysis')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    # Regex: optional digits, decimal point, exactly 2 digits, percent sign
    # Covers: 39.28%, 0.00%, 100.00%
    two_decimal_pct = re.compile(r'\d*\.\d{2}%')
    # Find all percentage-like patterns
    pct_matches = re.findall(r'[\d.]+%', text)
    for m in pct_matches:
        if '%' in m:
            # Must match two-decimal format
            assert two_decimal_pct.search(m) or re.match(r'^\d+\.\d{2}%$', m), \
                f"Percentage '{m}' should have two decimal places"
    # Page should render at least some percentages (q2, q5, q10, q11)
    assert '%' in text
