#!/usr/bin/env python3
"""
clean.py - Data cleaning module for Grad Cafe applicant data.

This module provides functions to clean and standardize scraped data,
removing HTML remnants and ensuring consistent formatting.

"""

import json
import re


def _clean_text(text):
    """
    Clean text by removing extra whitespace and HTML remnants.
    
    Args:
        text: Raw text string
        
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
        
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def clean_data(raw_data):
    """
    Clean and standardize scraped applicant data.
    
    Args:
        raw_data: List of raw applicant dictionaries
        
    Returns:
        List of cleaned applicant dictionaries
    """
    cleaned = []
    
    for entry in raw_data:
        if not entry:
            continue
            
        cleaned_entry = {}
        
        # Clean program name
        cleaned_entry['program'] = _clean_text(entry.get('program', ''))
        
        # Clean comments
        cleaned_entry['comments'] = _clean_text(entry.get('comments', ''))
        
        # Clean date added
        date_added = entry.get('date_added', '')
        cleaned_entry['date_added'] = _clean_text(date_added)
        
        # URL (should be clean already)
        cleaned_entry['url'] = entry.get('url', '')
        
        # Status - keep as combined string for compatibility
        status_raw = entry.get('status', '')
        cleaned_entry['status'] = _clean_text(status_raw)
        
        # Term
        term = entry.get('term', '')
        cleaned_entry['term'] = _clean_text(term) if term else ''
        
        # US/International
        us_int = entry.get('US/International', '')
        cleaned_entry['US/International'] = us_int if us_int else ''
        
        # Degree
        degree = entry.get('Degree', '')
        cleaned_entry['Degree'] = _clean_text(degree) if degree else ''
        
        # GPA - keep as string for JSON compatibility with sample format
        gpa = entry.get('GPA', '')
        cleaned_entry['GPA'] = gpa if gpa else ''
        
        # GRE scores - keep as strings for JSON compatibility
        gre = entry.get('GRE', '')
        if gre:
            cleaned_entry['GRE'] = gre
            
        gre_v = entry.get('GRE_V', '')
        if gre_v:
            cleaned_entry['GRE_V'] = gre_v
            
        gre_aw = entry.get('GRE_AW', '')
        if gre_aw:
            cleaned_entry['GRE_AW'] = gre_aw
        
        cleaned.append(cleaned_entry)
        
    return cleaned


def save_data(data, filename):
    """
    Save data to a JSON file.
    
    Args:
        data: List of applicant dictionaries
        filename: Output filename
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} entries to {filename}")


def load_data(filename):
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
    
    parser = argparse.ArgumentParser(description="Clean Grad Cafe applicant data")
    parser.add_argument('--input', type=str, default='applicant_data.json',
                        help='Input JSON file (default: applicant_data.json)')
    parser.add_argument('--output', type=str, default='cleaned_applicant_data.json',
                        help='Output JSON file (default: cleaned_applicant_data.json)')
    
    args = parser.parse_args()
    
    # Load raw data
    print(f"Loading data from {args.input}...")
    raw = load_data(args.input)
    print(f"Loaded {len(raw)} entries")
    
    # Clean data
    print("Cleaning data...")
    cleaned = clean_data(raw)
    
    # Save cleaned data
    save_data(cleaned, args.output)
