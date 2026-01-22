"""
Projects route blueprint.
Displays information about Python projects, particularly Module 1 project.
"""

from flask import Blueprint, render_template

# Create blueprint for projects page
projects_bp = Blueprint('projects', __name__)


@projects_bp.route('/projects')
def projects():
    """
    Render the projects page.
    Returns the projects template with project information.
    """
    # Project information (customize with your Module 1 project details)
    projects_info = {
        'module1': {
            'title': 'Module 1 - Personal Website ',
            'description': 'A personal developer website built with Flask, featuring a responsive design with three main pages: homepage with biography and profile image, contact information page, and a projects showcase page. The application uses Flask Blueprints for modular route organization, Jinja2 templates for dynamic HTML rendering, and custom CSS for styling. Key features include a fixed navigation bar with active page highlighting, responsive layout with bio text on the left and profile image on the right, and clean separation of concerns using the routes, templates, and static folders structure.',
            'github_link': 'git@github.com:Shangshanderener/jhu_software_concepts.git'
        }
    }
    return render_template('projects.html', projects=projects_info, current_page='projects')
