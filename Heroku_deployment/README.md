# Audio Transcription Service

A Flask-based audio transcription service with Google Sheets integration, ready for Heroku deployment.

## Features

- 🎵 Audio/Video transcription using Faster-Whisper
- 📊 Google Sheets integration for transcript storage
- 🌐 Web interface with drag-and-drop file upload
- 📱 RESTful API endpoints
- 🔍 Health monitoring and metrics
- 🚀 Production-ready Heroku configuration

## Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_SHEET_ID="your-sheet-id"
export SERVICE_ACCOUNT_EMAIL="your-service-account@project.iam.gserviceaccount.com"
export GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'

# Run the application
flask run
```

### Heroku Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

## API Endpoints

- `POST /transcribe` - Upload and transcribe audio files
- `GET /health` - Health check and system status
- `GET /status` - Service information
- `GET /metrics` - System metrics (Prometheus format)

## File Support

- Audio: MP3, WAV, M4A, FLAC
- Video: MP4 (audio extraction)
- Maximum file size: 100MB

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_SHEET_ID` | Google Sheets document ID | Yes |
| `SERVICE_ACCOUNT_EMAIL` | Google service account email | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Service account credentials JSON | Yes |
| `GOOGLE_WORKSHEET_NAME` | Worksheet name (default: "TRANSCRIPT FINAL") | No |
| `SENTRY_DSN` | Sentry error monitoring DSN | No |

## Production Features

- Gunicorn WSGI server with optimized configuration
- Comprehensive error handling and logging
- Automatic file cleanup and resource management
- Health monitoring with detailed system metrics
- Sentry integration for error tracking

## License

MIT License - see LICENSE file for details.