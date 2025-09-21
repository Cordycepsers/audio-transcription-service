#!/bin/bash

echo "🚀 Starting Audio Transcription Service..."

# Download NLTK data if not already present
echo "📦 Checking NLTK data..."
python download_nltk_data.py

# Start the application
echo "🌐 Starting web server..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 --worker-class sync --max-requests 1000 --preload app:app