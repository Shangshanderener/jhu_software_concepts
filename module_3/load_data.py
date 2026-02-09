#!/usr/bin/env python3
"""
load_to_postgres.py - Load Grad Cafe data into PostgreSQL database.

This script loads the LLM-extended applicant data into a PostgreSQL database
for analysis.
"""

import json
import re
import sys
import psycopg
from datetime import datetime



# Database configuration - update these for your environment
DB_CONFIG = {
    'dbname': 'gradcafe',
    'user': 'kamisama',
    'password': '',
    'host': 'localhost',
    'port': '5432'
}

# Path to the LLM-extended data file
DATA_FILE = 'llm_extend_applicant_data_liv.json'


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
                year = int(year_match.group(1))
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
    if parts:
        return parts[0]
    return None


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
    """Create the applicants table if it doesn't exist."""
    cur.execute("""
        DROP TABLE IF EXISTS applicants;
        CREATE TABLE applicants (
            p_id SERIAL PRIMARY KEY,
            program TEXT,
            comments TEXT,
            date_added DATE,
            url TEXT,
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
    """Load data into the applicants table."""
    insert_query = """
        INSERT INTO applicants (
            program, comments, date_added, url, status, term,
            us_or_international, gpa, gre, gre_v, gre_aw, degree,
            llm_generated_program, llm_generated_university
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    
    count = 0
    for entry in data:
        # Parse fields - using correct JSON field names
        program = entry.get('program', '')
        comments = entry.get('comments', '')
        date_added = parse_date(entry.get('date_added', ''))
        url = entry.get('overview_url', '')  # JSON uses 'overview_url'
        status = entry.get('applicant_status', '')  # JSON uses 'applicant_status'
        term = entry.get('start_term', '')  # JSON uses 'start_term'
        us_or_international = get_is_american(entry.get('citizenship', ''))  # JSON uses 'citizenship'
        gpa = parse_float(entry.get('gpa', ''))  # JSON uses lowercase 'gpa'
        gre = parse_float(entry.get('gre_general', ''))  # JSON uses 'gre_general'
        gre_v = parse_float(entry.get('gre_verbal', ''))  # JSON uses 'gre_verbal'
        gre_aw = parse_float(entry.get('gre_aw', ''))  # JSON uses 'gre_aw'
        degree = entry.get('degree_level', '')  # JSON uses 'degree_level'
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
    # Load JSON data
    print(f"Loading data from {data_file}...")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} entries from JSON")
    
    # Connect to PostgreSQL using psycopg3
    print("Connecting to PostgreSQL...")
    conn = None
    try:
        conn = psycopg.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        
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
