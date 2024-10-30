import sys
import os

# Path to your Flask app's directory
sys.path.insert(0, "/var/www/cameraCountingWeb")

# Import your app object as 'application' for WSGI
from app import app as application  # Make sure 'app' matches the Flask app name in app.py