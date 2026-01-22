"""
Contact route blueprint.
Displays contact information including email and LinkedIn.
"""

from flask import Blueprint, render_template

# Create blueprint for contact page
contact_bp = Blueprint('contact', __name__)


@contact_bp.route('/contact')
def contact():
    """
    Render the contact page.
    Returns the contact template with contact information.
    """
    # Contact information (customize these with your details)
    contact_info = {
        'email': 'zhan49@jhu.edu',
        'linkedin': 'https://www.linkedin.com/in/zicheng-han-684b073a7/'
    }
    return render_template('contact.html', info=contact_info, current_page='contact')
