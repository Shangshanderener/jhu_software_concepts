Setup and Run Instructions
========================================================

PREREQUISITES
-------------
- Python 3.10 or higher
- pip (Python package installer)

INSTALLATION
------------
1. Navigate to the module_1 directory:
   cd module_1

2. Create a virtual environment (required on macOS with Homebrew Python):
   python3 -m venv venv

3. Activate the virtual environment:
   source venv/bin/activate
   
4. Install required dependencies:
   pip install -r requirements.txt


RUNNING THE APPLICATION
-----------------------
1. Make sure you are in the module_1 directory:
   cd module_1

2. Activate the virtual environment (if not already activated):
   source venv/bin/activate
   
3. Start the Flask application using:
   python run.py

ACCESSING THE WEBSITE
---------------------
After starting the application, the website will be available at:
   http://localhost:8080
   or
   http://0.0.0.0:8080

Open your web browser and navigate to one of the URLs above.

To stop the server, press Ctrl+C in the terminal.


PROJECT STRUCTURE
-----------------
module_1/
├── app.py              # Main Flask application file
├── run.py              # Script to run the application
├── requirements.txt    # Python dependencies
├── README.txt         # This file
├── routes/            # Blueprint routes
│   ├── __init__.py
│   ├── homepage.py   # Homepage route
│   ├── contact.py    # Contact page route
│   └── projects.py   # Projects page route
├── templates/         # HTML templates
│   ├── base.html     # Base template with navigation
│   ├── homepage.html # Homepage template
│   ├── contact.html  # Contact page template
│   └── projects.html # Projects page template
└── static/           # Static files
    ├── css/
    │   └── style.css # CSS stylesheet
    └── images/       # Images (add your profile.jpg here)
