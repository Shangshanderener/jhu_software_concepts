# Module 2: Grad Cafe Web Scraper

**Name:** Zicheng Han  
**JHED ID:** 58C849  
**Module:** Module 2 - Web Scraping and Data Cleaning  
**Due Date:** 2-1-2026

---

## Approach

### Overview
This project implements a web scraper for The Grad Cafe (thegradcafe.com) to collect graduate school admission results. The solution uses Python with `urllib` for HTTP requests and `BeautifulSoup` for HTML parsing, following all assignment requirements.

### robots.txt Compliance
Before scraping, I verified the site's `robots.txt` file (see `robots_screenshot.png`). The file contains:
```
User-agent: *
Allow: /
```
This confirms that web scraping is permitted for the survey results pages.

### Data Collection (`scrape.py`)

#### Architecture
The solution uses a **List of Dictionaries** as the primary data structure to store applicant entries. Each dictionary acts as a record representing a single admission result, containing key-value pairs for all extracted fields (e.g., `program`, `status`, `GPA`).

The scraper is organized into several functions:

- **`scrape_data(num_pages, delay, start_page)`**: Main function that orchestrates the scraping process
  - Uses pagination via URL parameter `?page=N`
  - Implements optional rate limiting (passed via `--delay`) to be respectful to the server
  - Handles retries on network failures

- **`_fetch_page(page_num)`**: Uses `urllib.request` to fetch individual pages
  - Sets appropriate User-Agent header
  - Implements 3 retries with exponential backoff

- **`_parse_page(html)`**: Parses full HTML page using BeautifulSoup
  - Identifies the results table structure
  - Groups table rows by entry (each entry spans 2-3 rows)

- **`_parse_entry(rows)`**: Extracts data from individual entries
  - Cell 0: University name
  - Cell 1: Program name and Degree type (from `<span>` elements)
  - Cell 2: Date added to Grad Cafe
  - Cell 3: Admission status (Accepted/Rejected/Wait listed) with date
  - Cell 4: URL link to the individual result
  - Badge rows: Term, US/International status, GPA, GRE scores
  - Comment rows: Applicant comments

- **`_extract_badges(row)`**: Parses badge information using regex patterns
  - Identifies term (Fall/Spring/Summer YYYY)
  - Extracts GPA, GRE, GRE V, GRE AW scores
  - Determines US/International status

- **`save_data(data, filename)`** and **`load_data(filename)`**: JSON file I/O

#### Data Fields Extracted
| Field | Description |
|-------|-------------|
| `program` | Combined "Program Name, University" format |
| `date_added` | Date the entry was added to Grad Cafe |
| `url` | Direct link to the result page |
| `status` | Raw admission status string (e.g., "Accepted on 15 Jan") |
| `term` | Semester and year (e.g., "Fall 2026") |
| `US/International` | Applicant status |
| `Degree` | Masters or PhD |
| `GPA` | Reported GPA if available |
| `GRE`, `GRE_V`, `GRE_AW` | GRE scores if available |
| `comments` | Applicant comments if provided |

### Data Cleaning (`clean.py`)

The cleaning module standardizes the scraped data:

- **`clean_data(raw_data)`**: Main cleaning function
  - Removes HTML remnants using regex
  - Normalizes whitespace
  - Ensures consistent format for missing values (empty string "")
  - Strips leading/trailing whitespace from all text fields

- **`_clean_text(text)`**: Helper to sanitize individual text fields

- **`save_data()` / `load_data()`**: JSON file operations

### LLM Data Standardization

The `llm_hosting/app.py` standardizes program and university names using an optimized pipeline:

1. **Rule-First Parsing** — Splits "Program, University" strings using regex and normalizes with fuzzy matching to canonical lists. Handles ~99.9% of entries instantly.

2. **LLM Fallback** — For ambiguous entries, uses TinyLlama (local LLM) with few-shot prompting to parse the fields.

3. **Caching** — LRU cache (10k entries) avoids redundant LLM calls for duplicate inputs.

**Output Fields:**
- `llm-generated-program`: Cleaned program name
- `llm-generated-university`: Cleaned university name

**Performance:** Processing 30,000 entries completes in seconds (29,978 rule-parsed, only 22 need LLM).

### Data Structures

**Entry Dictionary Structure:**
```python
{
    "program": "Computer Science, Stanford University",
    "comments": "Received offer via email",
    "date_added": "January 28, 2026",
    "url": "https://www.thegradcafe.com/result/992614",
    "status": "Accepted on 15 Jan",
    "term": "Fall 2026",
    "US/International": "American",
    "Degree": "PhD",
    "GPA": "GPA 3.92",
    "GRE": "GRE 328"
}
```

### Files Included

| File | Description |
|------|-------------|
| `scrape.py` | Main web scraping module |
| `clean.py` | Data cleaning and standardization |
| `applicant_data.json` | Raw scraped data (30,000+ entries) |
| `llm_extend_applicant_data.json` | Cleaned data with LLM-standardized fields |
| `requirements.txt` | Python dependencies |
| `robots_screenshot.png` | Evidence of robots.txt compliance check |
| `llm_hosting/` | Provided LLM standardization tool |


## Usage

### Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Scraper
```bash
# Scrape 1500 pages (~30,000 entries)
python scrape.py --pages 1500 --output applicant_data.json

# Or scrape specific range
python scrape.py --pages 100 --start 1 --delay 1.0
```

### Running the Cleaner
```bash
python clean.py --input applicant_data.json --output cleaned_applicant_data.json
```

### Running LLM Standardization
```bash
cd llm_hosting
source venv/bin/activate  # or create venv and pip install -r requirements.txt
python app.py --file ../cleaned_applicant_data.json --stdout > ../llm_extend_applicant_data.json
