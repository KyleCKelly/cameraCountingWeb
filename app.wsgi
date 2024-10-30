import sys
import os
import logging
from app import app as application  # Adjust if the app is located in another module

# Configure basic logging to capture errors in the Apache logs
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# Add the project directory to the Python path
project_dir = os.path.dirname(__file__)
sys.path.insert(0, project_dir)