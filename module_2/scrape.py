#!/usr/bin/env python3
"""
scrape.py - Web scraper for The Grad Cafe admission results.

This module uses urllib to fetch pages and BeautifulSoup to parse HTML,
extracting graduate school admission data for analysis.

"""

import json
import re
import time
import urllib.request
import urllib.error
from bs4 import BeautifulSoup


# Base URL for Grad Cafe survey results
BASE_URL = "https://www.thegradcafe.com/survey/"


def _fetch_page(page_num, retries=3):
    """
    Fetch a single page of results using urllib.
    
    Args:
        page_num: Page number to fetch (1-indexed)
        retries: Number of retry attempts on failure
        
    Returns:
        HTML content as string, or None on failure
    """
    url = f"{BASE_URL}?page={page_num}"
    
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'SuperHan/1.0 (Educational Research Bot)'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8')
                
        except urllib.error.URLError as e:
            print(f"  Attempt {attempt + 1}/{retries} failed for page {page_num}: {e}")
            if attempt < retries - 1:
                time.sleep(2)  # Wait before retry
                
    return None


def _extract_badges(badge_row):
    """
    Extract badge information (term, GPA, GRE, etc.) from a badge row.
    
    Args:
        badge_row: BeautifulSoup element containing badge divs
        
    Returns:
        Dictionary with extracted badge values
    """
    badges = {}
    
    if not badge_row:
        return badges
    
    # Find all badge-like divs
    badge_divs = badge_row.find_all('div', class_=re.compile(r'tw-rounded|tw-px-2'))
    
    for div in badge_divs:
        text = div.get_text(strip=True)
        
        if not text:
            continue
            
        # Term (e.g., "Fall 2024", "Spring 2025")
        if re.match(r'^(Fall|Spring|Summer|Winter)\s+\d{4}$', text, re.IGNORECASE):
            badges['term'] = text
            
        # US/International status
        elif text in ['American', 'International']:
            badges['US/International'] = text
            
        # GPA
        elif text.startswith('GPA'):
            badges['GPA'] = text
            
        # GRE Verbal
        elif re.match(r'^GRE\s*V\s*\d+', text, re.IGNORECASE):
            badges['GRE_V'] = text
            
        # GRE Analytical Writing
        elif re.match(r'^GRE\s*(AW|A)\s*[\d.]+', text, re.IGNORECASE):
            badges['GRE_AW'] = text
            
        # General GRE score
        elif re.match(r'^GRE\s*\d+', text, re.IGNORECASE):
            badges['GRE'] = text
            
    return badges


def _parse_entry(rows):
    """
    Parse a group of table rows representing one admission entry.
    
    Args:
        rows: List of BeautifulSoup tr elements for one entry
        
    Returns:
        Dictionary with applicant data, or None if parsing fails
    """
    if not rows or len(rows) == 0:
        return None
        
    primary_row = rows[0]
    cells = primary_row.find_all('td')
    
    if len(cells) < 4:
        return None
        
    entry = {}
    
    # Cell 0: University name
    uni_div = cells[0].find('div', class_=re.compile(r'tw-font-medium'))
    university = ""
    if uni_div:
        university = uni_div.get_text(strip=True)
            
    # Cell 1: Program and Degree (in spans)
    prog_cell = cells[1]
    program = ""
    
    # Find the div containing program info
    prog_div = prog_cell.find('div')
    if prog_div:
        spans = prog_div.find_all('span')
        if spans:
            # First span is program name
            program = spans[0].get_text(strip=True)
            # Second span (if exists) is degree
            if len(spans) > 1:
                entry['Degree'] = spans[1].get_text(strip=True)
        else:
            # No spans, get text directly
            program = prog_div.get_text(strip=True)
    
    # Combine program and university
    if program and university:
        entry['program'] = f"{program}, {university}"
    elif program:
        entry['program'] = program
    elif university:
        entry['program'] = university
    else:
        entry['program'] = ""
        
    # Cell 2: Date added
    if len(cells) > 2:
        date_text = cells[2].get_text(strip=True)
        entry['date_added'] = date_text
        
    # Cell 3: Status/Decision
    if len(cells) > 3:
        status_div = cells[3].find('div')
        if status_div:
            status_text = status_div.get_text(strip=True)
            entry['status'] = status_text
            
    # Cell 4: URL link (if exists)
    if len(cells) > 4:
        url_link = cells[4].find('a', href=re.compile(r'/result/\d+'))
        if url_link:
            result_id = url_link.get('href', '')
            entry['url'] = f"https://www.thegradcafe.com{result_id}"
            
    # If no URL found in cell 4, try to find it anywhere in the row
    if 'url' not in entry or not entry['url']:
        any_link = primary_row.find('a', href=re.compile(r'/result/\d+'))
        if any_link:
            result_id = any_link.get('href', '')
            entry['url'] = f"https://www.thegradcafe.com{result_id}"
        else:
            entry['url'] = ""
                
    # Process additional rows for badges and comments
    for i, row in enumerate(rows[1:], 1):
        # Check if this is a badge row or comment row
        comment_p = row.find('p', class_=re.compile(r'tw-text-gray.*tw-text-sm'))
        if comment_p:
            entry['comments'] = comment_p.get_text(strip=True)
        else:
            # Extract badges
            badges = _extract_badges(row)
            entry.update(badges)
                
    # Ensure comments field exists with consistent empty string for missing data
    if 'comments' not in entry:
        entry['comments'] = ''

    # Ensure GRE fields exist with consistent empty string for missing data
    for field in ['GRE', 'GRE_V', 'GRE_AW']:
        if field not in entry:
            entry[field] = ''
        
    return entry


def _parse_page(html):
    """
    Parse a page of HTML to extract all admission entries.
    
    Args:
        html: Raw HTML content
        
    Returns:
        List of entry dictionaries
    """
    soup = BeautifulSoup(html, 'html.parser')
    entries = []
    
    # Find the results table
    table = soup.find('table')
    if not table:
        return entries
        
    tbody = table.find('tbody')
    if not tbody:
        return entries
        
    rows = tbody.find_all('tr')
    
    # Group rows by entry - each entry starts with a row containing 4+ td cells
    current_entry_rows = []
    
    for row in rows:
        cells = row.find_all('td')
        
        # Check if this is a primary row (has 4+ cells with substance)
        if len(cells) >= 4:
            # Save previous entry if exists
            if current_entry_rows:
                entry = _parse_entry(current_entry_rows)
                if entry:
                    entries.append(entry)
                    
            # Start new entry
            current_entry_rows = [row]
        else:
            # This is a continuation row (badges or comments)
            current_entry_rows.append(row)
            
    # Don't forget the last entry
    if current_entry_rows:
        entry = _parse_entry(current_entry_rows)
        if entry:
            entries.append(entry)
            
    return entries


def scrape_data(num_pages=1500, delay=1.0, start_page=1):
    """
    Scrape admission data from Grad Cafe.
    
    Args:
        num_pages: Number of pages to scrape (default 1500 for ~30,000 entries)
        delay: Delay between requests in seconds (be respectful)
        start_page: Page to start from (for resuming)
        
    Returns:
        List of applicant dictionaries
    """
    all_entries = []
    
    print(f"Starting scrape of {num_pages} pages from page {start_page}...")
    
    for page_num in range(start_page, start_page + num_pages):
        print(f"Fetching page {page_num}/{start_page + num_pages - 1}...", end=" ")
        
        html = _fetch_page(page_num)
        
        if html is None:
            print("FAILED - skipping")
            continue
            
        entries = _parse_page(html)
        all_entries.extend(entries)
        
        print(f"Got {len(entries)} entries (total: {len(all_entries)})")
        
        # Rate limiting
        # if page_num < start_page + num_pages - 1:
        #     time.sleep(delay)
            
    print(f"\nScraping complete! Total entries: {len(all_entries)}")
    return all_entries


def save_data(data, filename="applicant_data.json"):
    """
    Save data to a JSON file.
    
    Args:
        data: List of applicant dictionaries
        filename: Output filename
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} entries to {filename}")


def load_data(filename="applicant_data.json"):
    """
    Load data from a JSON file.
    
    Args:
        filename: Input filename
        
    Returns:
        List of applicant dictionaries
    """
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Grad Cafe admission results")
    parser.add_argument('--pages', type=int, default=1500, 
                        help='Number of pages to scrape (default: 1500)')
    parser.add_argument('--start', type=int, default=1,
                        help='Starting page number (default: 1)')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--output', type=str, default='applicant_data.json',
                        help='Output filename (default: applicant_data.json)')
    
    args = parser.parse_args()
    
    # Scrape the data
    data = scrape_data(num_pages=args.pages, delay=args.delay, start_page=args.start)
    
    # Save to file
    if data:
        save_data(data, args.output)
