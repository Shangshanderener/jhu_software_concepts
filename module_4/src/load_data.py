#!/usr/bin/env python3
"""
load_data.py - Load Grad Cafe data into PostgreSQL database.

This script loads the LLM-extended applicant data into a PostgreSQL database
for analysis. Uses DATABASE_URL environment variable when set.
Idempotent: duplicate URLs are skipped via ON CONFLICT DO NOTHING.
"""

import json
import os
import re
import sys
import psycopg
from datetime import datetime

# Path to the LLM-extended data file (relative to script dir when used as script)
DATA_FILE = 'module_2/llm_extend_applicant_data.json'


def get_connection():
    """Get DB connection using DATABASE_URL or fallback env vars."""
    url = os.environ.get('DATABASE_URL')
    if url:
        return psycopg.connect(url)
    return psycopg.connect(
        dbname=os.environ.get('DB_NAME', 'gradcafe'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', ''),
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432')
    )


def parse_date(date_str):
    """Parse date string to datetime object."""
    if not date_str:
        return None
    try:
        # Format: "January 30, 2026"
        return datetime.strptime(date_str, "%B %d, %Y")
    except ValueError:
        return None


def parse_float(value_str, prefix=''):
    """Extract float value from string like 'GPA 3.9' or 'GRE V 159'."""
    if not value_str:
        return None
    # Remove prefix and extract number
    pattern = r'[\d.]+'
    match = re.search(pattern, value_str)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def parse_decision(status_str):
    """Extract decision type from status string like 'Accepted on 29 Jan'."""
    if not status_str:
        return None
    status_lower = status_str.lower()
    if 'accepted' in status_lower:
        return 'Accepted'
    elif 'rejected' in status_lower:
        return 'Rejected'
    elif 'interview' in status_lower:
        return 'Interview'
    elif 'wait' in status_lower:
        return 'Waitlisted'
    return status_str.split(' ')[0] if status_str else None


def parse_decision_date(status_str, term_str):
    """Extract decision date from status string."""
    if not status_str:
        return None
    # Pattern like "Accepted on 29 Jan"
    match = re.search(r'on (\d{1,2}) (\w+)', status_str)
    if match:
        day = match.group(1)
        month = match.group(2)
        # Try to get year from term
        year = 2026  # default
        if term_str:
            year_match = re.search(r'(\d{4})', term_str)
            if year_match:
                try:
                    year = int(year_match.group(1))
                except ValueError:
                    pass
        try:
            # Try parsing with different month formats
            for fmt in ['%d %b %Y', '%d %B %Y']:
                try:
                    return datetime.strptime(f"{day} {month} {year}", fmt)
                except ValueError:
                    continue
        except:
            pass
    return None


def extract_university(program_str):
    """Extract university name from program string like 'Computer Science, MIT'."""
    if not program_str:
        return None
    parts = program_str.split(', ')
    if len(parts) >= 2:
        return ', '.join(parts[1:])  # Everything after first comma
    return None


def extract_program(program_str):
    """Extract program name from program string like 'Computer Science, MIT'."""
    if not program_str:
        return None
    parts = program_str.split(', ')
    return parts[0]


def get_is_american(us_int_str):
    """Convert US/International field to is_american text."""
    if not us_int_str:
        return 'Other'
    if us_int_str.lower() == 'american':
        return 'American'
    elif us_int_str.lower() == 'international':
        return 'International'
    return 'Other'


def create_table(cur):
    """Create the applicants table if it doesn't exist. url has UNIQUE for idempotency."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applicants (
            p_id SERIAL PRIMARY KEY,
            program TEXT,
            comments TEXT,
            date_added DATE,
            url TEXT UNIQUE,
            status TEXT,
            term TEXT,
            us_or_international TEXT,
            gpa FLOAT,
            gre FLOAT,
            gre_v FLOAT,
            gre_aw FLOAT,
            degree TEXT,
            llm_generated_program TEXT,
            llm_generated_university TEXT
        );
    """)


def load_data(cur, data):
    """Load data into the applicants table. Skips duplicates by url (idempotent)."""
    insert_query = """
        INSERT INTO applicants (
            program, comments, date_added, url, status, term,
            us_or_international, gpa, gre, gre_v, gre_aw, degree,
            llm_generated_program, llm_generated_university
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (url) DO NOTHING
    """
    
    count = 0
    for entry in data:
        # Parse fields - using correct JSON field names from module_2 scraping
        program = entry.get('program', '')
        comments = entry.get('comments', '')
        date_added = parse_date(entry.get('date_added', ''))
        url = entry.get('url', '')
        status = entry.get('status', '')
        term = entry.get('term', '')
        us_or_international = get_is_american(entry.get('US/International', ''))
        gpa = parse_float(entry.get('GPA', ''))
        gre = parse_float(entry.get('GRE', ''))
        gre_v = parse_float(entry.get('GRE_V', ''))
        gre_aw = parse_float(entry.get('GRE_AW', ''))
        degree = entry.get('Degree', '')
        llm_program = entry.get('llm-generated-program', '')
        llm_uni = entry.get('llm-generated-university', '')
        
        cur.execute(insert_query, (
            program, comments, date_added, url, status, term,
            us_or_international, gpa, gre, gre_v, gre_aw, degree,
            llm_program, llm_uni
        ))
        count += 1
        
        if count % 1000 == 0:
            print(f"Loaded {count} entries...")
    
    return count


def main():
    """Main function to load data into PostgreSQL."""
    data_file = sys.argv[1] if len(sys.argv) >= 2 else DATA_FILE
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(data_file):
        data_file = os.path.join(base_dir, data_file)
    # Load JSON data
    print(f"Loading data from {data_file}...")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} entries from JSON")
    
    print("Connecting to PostgreSQL...")
    conn = None
    try:
        conn = get_connection()
        
        with conn.cursor() as cur:
            # Create table
            print("Creating table...")
            create_table(cur)
            
            # Load data
            print("Loading data into database...")
            count = load_data(cur, data)
        
        # Commit
        conn.commit()
        print(f"\nSuccessfully loaded {count} entries into PostgreSQL!")
        
    except psycopg.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()



if __name__ == "__main__":
    main()
