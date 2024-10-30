import sys
import os
from app import app as application  # Adjust if the app is located in another module

# Add project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))