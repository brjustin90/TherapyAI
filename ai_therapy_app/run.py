#!/usr/bin/env python
"""
Run script for Mental Health AI Therapy Web Application
This script helps users start either the web app (Flask) or the API (FastAPI)
"""
import argparse
import os
import subprocess
import sys
import webbrowser
from time import sleep
from web_app import app

def main():
    """Run the AI Therapy App"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the AI Therapy App')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    # Use 0.0.0.0 to make the server externally visible
    port = int(os.getenv('PORT', 8000))
    
    # Set the static folder path explicitly
    app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    
    print(f"✨ AI video avatar and personalization features are ready to use!")
    print(f"Starting application on http://localhost:{port}")
    app.run(debug=args.debug, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main() 