"""
Run script for Flask application.
Start the web application using: python run.py
"""

from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
