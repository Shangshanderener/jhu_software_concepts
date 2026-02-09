# Module 3 - Database Queries Assignment

Grad Cafe Analysis Flask web application with PostgreSQL integration.

## Prerequisites

1. **PostgreSQL** - Install and start PostgreSQL:
   ```bash
   # macOS with Homebrew
   brew install postgresql@14
   brew services start postgresql@14
   
   # Create the database
   createdb gradcafe
   ```

2. **Python 3.x** with virtual environment

## Setup Instructions

### 1. Activate Virtual Environment
```bash
cd module_3
source venv/bin/activate
```

### 2. Configure Database Connection
Edit `load_data.py` and `query_data.py` to update DB_CONFIG if needed:
```python
DB_CONFIG = {
    'dbname': 'gradcafe',
    'user': 'kamisama',      # your postgres username
    'password': '',          # your postgres password (if any)
    'host': 'localhost',
    'port': '5432'
}
```

### 3. Load Data into PostgreSQL
```bash
python load_data.py
```

This loads data from `llm_extend_applicant_data_liv.json` into the PostgreSQL database.

### 4. Run the Flask Application
```bash
python app.py
```

Open http://localhost:8080 in your browser.

## Data File Format

The `load_data.py` script expects JSON data with these fields:
| JSON Field | Database Column |
|------------|-----------------|
| `program` | `program` |
| `start_term` | `term` |
| `applicant_status` | `status` |
| `citizenship` | `us_or_international` |
| `gpa` | `gpa` |
| `gre_general` | `gre` |
| `gre_verbal` | `gre_v` |
| `gre_aw` | `gre_aw` |
| `degree_level` | `degree` |
| `overview_url` | `url` |
| `llm-generated-program` | `llm_generated_program` |
| `llm-generated-university` | `llm_generated_university` |

## Files

| File | Description |
|------|-------------|
| `app.py` | Main Flask application with routes and API endpoints |
| `query_data.py` | SQL queries for all 11 analysis questions |
| `load_data.py` | Script to load JSON data into PostgreSQL |
| `templates/analysis.html` | Analysis page template with styled results |
| `static/css/style.css` | Premium dark-mode CSS styling |
| `limitations.md` | Discussion of self-submit data source limitations |

## Features

- **Analysis Dashboard**: Displays answers to all 11 assignment questions
- **Pull Data Button**: Triggers web scraping from Grad Cafe (uses subprocess)
- **Update Analysis Button**: Refreshes page with latest data (blocks during scraping)