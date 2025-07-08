#!/bin/bash

# Azure App Service startup script for Python Flask app
echo "Starting RFP BOM Generator..."

# Install any additional dependencies if needed
pip install --upgrade pip

# Start the Flask application with Gunicorn
echo "Starting Gunicorn server..."
gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 1 app:app
