"""
Homepage route blueprint.
Displays personal information, bio, and image.
"""

from flask import Blueprint, render_template

# Create blueprint for homepage
homepage_bp = Blueprint('homepage', __name__)


@homepage_bp.route('/')
@homepage_bp.route('/home')
def index():
    """
    Render the homepage.
    Returns the homepage template with personal information.
    """
    # Personal information (you can customize these)
    personal_info = {
        'name': 'Zicheng Han',
        'position': 'Software Developer',
        'bio': 
            'Hi, I\'m Zicheng Han and I am currently based in San Francisco. ' + 
            'I studied Computer Science at UC Berkeley and now I am a master student at Johns Hopkins University. ' + 
            'Outside of academics, I\'m a big tennis fan and spend a lot of time at the gym. ' +
            'I also have a strong passion for blockchain technology. ' +
            'I enjoy keeping up with new developments in the field and thinking about how it might reshape industries in the future. ' +
            'One trait I value about myself is persistence. ' +
            'Everytime when I encounter a tough problem, I\'m willing to dig in and keep working at it until I truly understand the solution.',
        'image': 'static/images/profile.jpg'  # Path to your profile image
    }
    return render_template('homepage.html', info=personal_info, current_page='home')
