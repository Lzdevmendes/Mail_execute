"""
Vercel entry point for the Mail Classification API
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.main import app

# Vercel expects this variable name
app = app