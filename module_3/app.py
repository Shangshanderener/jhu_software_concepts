#!/usr/bin/env python3
"""
app.py - Flask application for Grad Cafe analysis webpage.

This application displays the results of PostgreSQL queries and provides
functionality to pull new data from Grad Cafe and update the analysis.
"""

import os
import subprocess
import threading
from flask import Flask, render_template, jsonify, request

from query_data import get_all_results

app = Flask(__name__)

# Global state for tracking scraping process
scraping_state = {
    'is_running': False,
    'process': None,
    'message': '',
    'lock': threading.Lock()
}


@app.route('/')
def analysis():
    """Main analysis page showing all query results."""
    try:
        results = get_all_results()
        return render_template('analysis.html', 
                             results=results, 
                             is_scraping=scraping_state['is_running'])
    except Exception as e:
        return render_template('analysis.html', 
                             results=None, 
                             error=str(e),
                             is_scraping=scraping_state['is_running'])


@app.route('/api/pull-data', methods=['POST'])
def pull_data():
    """
    API endpoint to trigger data scraping from Grad Cafe.
    Uses subprocess to run the scrape.py script from module_2.
    """
    with scraping_state['lock']:
        if scraping_state['is_running']:
            return jsonify({
                'success': False,
                'message': 'Data scraping is already in progress. Please wait.'
            })
        
        scraping_state['is_running'] = True
        scraping_state['message'] = 'Starting data scrape...'
    
    # Run scraping in background thread
    def run_scrape():
        try:
            # Path to the scrape script (module_2 inside module_3)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            module_2_dir = os.path.join(base_dir, 'module_2')
            scrape_script = os.path.join(module_2_dir, 'scrape.py')
            output_file = os.path.join(module_2_dir, 'applicant_data.json')
            
            # Run scrape with limited pages for demo (adjust as needed)
            result = subprocess.run(
                ['python3', scrape_script, '--pages', '10', '--output', output_file],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                # Now run clean.py
                clean_script = os.path.join(module_2_dir, 'clean.py')
                cleaned_file = os.path.join(module_2_dir, 'cleaned_applicant_data.json')
                
                clean_result = subprocess.run(
                    ['python3', clean_script, '--input', output_file, '--output', cleaned_file],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if clean_result.returncode != 0:
                    scraping_state['message'] = f'Cleaning failed: {clean_result.stderr}'
                else:
                    # LLM standardization (program/university names)
                    llm_hosting_dir = os.path.join(module_2_dir, 'llm_hosting')
                    llm_script = os.path.join(llm_hosting_dir, 'app.py')
                    llm_output_file = os.path.join(module_2_dir, 'llm_extend_applicant_data.json')
                    llm_result = subprocess.run(
                        ['python3', llm_script, '--file', cleaned_file, '--out', llm_output_file],
                        cwd=llm_hosting_dir,
                        capture_output=True,
                        text=True,
                        timeout=600  # LLM can take a while
                    )
                    if llm_result.returncode != 0:
                        scraping_state['message'] = f'LLM standardization failed: {llm_result.stderr}'
                    else:
                        # Load new data into database
                        load_script = os.path.join(base_dir, 'load_data.py')
                        subprocess.run(
                            ['python3', load_script, llm_output_file],
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        scraping_state['message'] = 'Data scraping completed successfully!'
            else:
                scraping_state['message'] = f'Scraping failed: {result.stderr}'
                
        except subprocess.TimeoutExpired:
            scraping_state['message'] = 'Scraping timed out after 10 minutes.'
        except Exception as e:
            scraping_state['message'] = f'Error during scraping: {str(e)}'
        finally:
            with scraping_state['lock']:
                scraping_state['is_running'] = False
    
    thread = threading.Thread(target=run_scrape)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Data scraping started. This may take several minutes. '
                   'The page will update when complete.'
    })


@app.route('/api/scrape-status')
def scrape_status():
    """API endpoint to check the current scraping status."""
    return jsonify({
        'is_running': scraping_state['is_running'],
        'message': scraping_state['message']
    })


@app.route('/api/update-analysis', methods=['POST'])
def update_analysis():
    """
    API endpoint to update/refresh the analysis.
    Does nothing if scraping is currently in progress.
    """
    if scraping_state['is_running']:
        return jsonify({
            'success': False,
            'message': 'Cannot update analysis while data scraping is in progress. '
                       'Please wait for the scraping to complete.',
            'is_scraping': True
        })
    
    # Return success - the frontend will reload to get fresh data
    return jsonify({
        'success': True,
        'message': 'Analysis updated with the latest data.',
        'is_scraping': False
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
