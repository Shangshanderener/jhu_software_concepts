"""
Flask application for personal developer website.
This application uses blueprints to organize routes.
"""

from flask import Flask
from routes.homepage import homepage_bp
from routes.contact import contact_bp
from routes.projects import projects_bp

# Initialize Flask application
app = Flask(__name__)

# Register blueprints
app.register_blueprint(homepage_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(projects_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
