#!/usr/bin/env python3
"""
flask_app.py - Flask application for Grad Cafe analysis webpage.

This application displays the results of PostgreSQL queries and provides
functionality to pull new data from Grad Cafe and update the analysis.

Supports create_app() factory for testing, DATABASE_URL, and dependency injection.
"""

import os
import sys
import subprocess
import threading
from flask import Flask, render_template, jsonify

# Import will be resolved at runtime - query module uses get_connection from env
from . import query_data


def create_app(
    scraper_loader_fn=None,
    query_fn=None,
):
    """
    Application factory for Flask app.
    
    Args:
        scraper_loader_fn: Optional callable that performs scrape+clean+load.
            Called with no args. Used for testing with fake data.
            If None, uses default subprocess-based implementation.
        query_fn: Optional callable that returns analysis results dict.
            If None, uses query_data.get_all_results.
    
    Returns:
        Configured Flask application.
    """
    app = Flask(__name__)
    
    # Use injected or default implementations
    _scraper_loader = scraper_loader_fn
    _query_fn = query_fn or query_data.get_all_results

    # Global state for tracking scraping process
    scraping_state = {
        'is_running': False,
        'process': None,
        'message': '',
        'lock': threading.Lock()
    }

    def _default_scraper_loader():
        """Default implementation: run scrape -> clean -> llm -> load via subprocess."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        module_2_dir = os.path.join(base_dir, 'module_2')
        llm_dir = os.path.join(module_2_dir, 'llm_hosting')
        scrape_script = os.path.join(module_2_dir, 'scrape.py')
        output_file = os.path.join(module_2_dir, 'applicant_data.json')
        clean_script = os.path.join(module_2_dir, 'clean.py')
        cleaned_file = os.path.join(module_2_dir, 'cleaned_applicant_data.json')
        llm_script = os.path.join(llm_dir, 'app.py')
        llm_output = os.path.join(module_2_dir, 'llm_extend_applicant_data.json')
        load_script = os.path.join(base_dir, 'load_data.py')
        
        result = subprocess.run(
            [sys.executable, scrape_script, '--pages', '10', '--output', output_file],
            capture_output=True, text=True, timeout=600
        )
        if result.returncode != 0:
            scraping_state['message'] = f'Scraping failed: {result.stderr}'
            return
        
        clean_result = subprocess.run(
            [sys.executable, clean_script, '--input', output_file, '--output', cleaned_file],
            capture_output=True, text=True, timeout=300
        )
        if clean_result.returncode != 0:
            scraping_state['message'] = f'Cleaning failed: {clean_result.stderr}'
            return
            
        llm_result = subprocess.run(
            [sys.executable, llm_script, '--file', cleaned_file, '--out', llm_output],
            cwd=llm_dir, capture_output=True, text=True, timeout=600
        )
        if llm_result.returncode != 0:
            scraping_state['message'] = f'LLM failed: {llm_result.stderr}'
            return
            
        subprocess.run(
            [sys.executable, load_script, llm_output],
            capture_output=True, text=True, timeout=300
        )
        scraping_state['message'] = 'Data scraping completed successfully!'

    @app.route('/')
    @app.route('/analysis')
    def analysis():
        """Main analysis page showing all query results."""
        try:
            results = _query_fn()
            return render_template(
                'analysis.html',
                results=results,
                is_scraping=scraping_state['is_running']
            )
        except Exception as e:
            return render_template(
                'analysis.html',
                results=None,
                error=str(e),
                is_scraping=scraping_state['is_running']
            )

    @app.route('/api/pull-data', methods=['POST'])
    def pull_data():
        """API endpoint to trigger data scraping. Returns 200 with ok:true or 409 when busy."""
        with scraping_state['lock']:
            if scraping_state['is_running']:
                return jsonify({'ok': False, 'busy': True}), 409
            scraping_state['is_running'] = True
            scraping_state['message'] = 'Starting data scrape...'

        run_fn = _scraper_loader if _scraper_loader else _default_scraper_loader

        def run_scrape():
            try:
                run_fn()
            except subprocess.TimeoutExpired:
                scraping_state['message'] = 'Scraping timed out.'
            except Exception as e:
                scraping_state['message'] = f'Error: {str(e)}'
            finally:
                with scraping_state['lock']:
                    scraping_state['is_running'] = False

        thread = threading.Thread(target=run_scrape)
        thread.daemon = True
        thread.start()

        return jsonify({'ok': True, 'success': True, 'message': 'Data scraping started.'})

    @app.route('/api/scrape-status')
    def scrape_status():
        """Check current scraping status."""
        return jsonify({
            'is_running': scraping_state['is_running'],
            'message': scraping_state['message']
        })

    @app.route('/api/update-analysis', methods=['POST'])
    def update_analysis():
        """Update/refresh analysis. Returns 409 when pull is in progress."""
        if scraping_state['is_running']:
            return jsonify({'ok': False, 'busy': True}), 409
        return jsonify({
            'ok': True,
            'success': True,
            'message': 'Analysis updated.',
            'is_scraping': False
        })

    return app


# Default app instance for `flask run` or `python -m src.flask_app`
app = create_app()

if __name__ == '__main__':
    def main():
        """Run the app."""
        app.run(host='0.0.0.0', port=8080, debug=True)
    main()
