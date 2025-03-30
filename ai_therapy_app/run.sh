#!/bin/bash
# Script to run Mental Health AI Therapy Web Application

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "../.venv" ]; then
    echo "Activating virtual environment..."
    source ../.venv/bin/activate
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 could not be found. Please install Python 3 and try again."
    exit 1
fi

# Run the application
echo "Starting Mental Health AI Therapy Web Application..."
python3 run.py "$@" 