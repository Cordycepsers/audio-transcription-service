#!/bin/bash

# Audio Transcription Service - Production Startup Script

echo "🚀 Starting Audio Transcription Service in Production Mode..."

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "📦 Installing gunicorn..."
    pip install gunicorn
fi

# Set production environment
export FLASK_ENV=production

# Create necessary directories
mkdir -p uploads transcripts

# Download NLTK data if not present
python3 -c "
import nltk
import os
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
    print('✅ NLTK data already present')
except LookupError:
    print('📦 Downloading NLTK data...')
    nltk.download('punkt')
    nltk.download('punkt_tab')
    print('✅ NLTK data downloaded')
"

# Check if FFmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  Warning: FFmpeg not found. Audio processing may fail."
    echo "   Install with: apt-get install ffmpeg (Ubuntu/Debian)"
    echo "   or: brew install ffmpeg (macOS)"
fi

# Start the application
echo "🌟 Starting server on port 8080..."
echo "📊 Access the app at: http://localhost:8080"
echo "🔍 Health check at: http://localhost:8080/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================"

gunicorn \
    --bind 0.0.0.0:8080 \
    --workers 4 \
    --timeout 300 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    app:app