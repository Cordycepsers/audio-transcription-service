# Flask Audio Transcription Service with VideoAsk Integration

This Flask application provides an audio transcription service with Google Sheets integration and VideoAsk webhook support. It can process both MP3 and MP4 files, transcribing their audio content using the Whisper model and storing the results in both local JSON files and a Google Sheet. Additionally, it processes VideoAsk webhook payloads for comprehensive form response management.

## Features

### Audio Transcription
- Audio/Video transcription using Whisper model
- Google Sheets integration for transcript storage
- Bulk file processing support
- Web interface for single file uploads
- Support for MP3 and MP4 files
- Local JSON storage of transcripts

### VideoAsk Integration
- Webhook endpoint for VideoAsk form responses
- Automatic data mapping to Google Sheets format
- Local backup of all webhook payloads
- Test endpoints for validation and debugging
- Comprehensive error handling and logging

## Prerequisites

- Python 3.8+
- Google Cloud project with Sheets API enabled
- Service account credentials
- FFmpeg (for audio processing)

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd [your-repo-name]
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```
# Google Sheets Configuration
GOOGLE_SHEET_ID="your-sheet-id"
GSHEET_WORKSHEET_NAME="TRANSCRIPT FINAL"
GOOGLE_SHEETS_CREDS_FILE="service-account.json"

# VideoAsk Webhook Configuration
VIDEOASK_GOOGLE_SHEET_ID="your-videoask-sheet-id"
VIDEOASK_GSHEET_WORKSHEET_NAME="VideoAsk Responses"

# Whisper Model Settings
WHISPER_MODEL="base.en"
COMPUTE_TYPE="int8"
DEVICE="cpu"
```

4. Set up Google Sheets credentials:
- Place your `service-account.json` in the root directory

## Usage

### Web Interface
Run the Flask application:
```bash
flask run
```
Access the web interface at `http://localhost:5000`

### Bulk Processing
To process multiple files:
```bash
python process_uploads.py
```

Place files to be processed in the `uploads/` directory.

### VideoAsk Webhook Integration

#### Setting Up VideoAsk Webhooks
1. In your VideoAsk account, go to your form settings
2. Navigate to the "Integrations" or "Webhooks" section
3. Add a new webhook with the URL: `https://your-domain.com/webhook/videoask`
4. Select "Form Response" as the trigger event

#### Available Webhook Endpoints

**Main Webhook Endpoint**
```
POST /webhook/videoask
```
- Receives VideoAsk form response payloads
- Processes and maps data to Google Sheets format
- Creates local backup files
- Returns JSON status response

**Test Endpoint**
```
POST /webhook/test
```
- Processes sample VideoAsk data for testing
- Returns mapped data for inspection
- Useful for debugging data mapping

**Validation Endpoint**
```
GET /webhook/validate
```
- Checks webhook configuration
- Validates Google Sheets access
- Reports environment variable status
- Returns comprehensive validation results

#### Testing VideoAsk Integration
Run the comprehensive test suite:
```bash
python test_videoask_webhook.py
```

#### Data Mapping
VideoAsk responses are automatically mapped to the following Google Sheets columns:
- **Name**: Contact name
- **DATE**: Response timestamp
- **EMAIL**: Contact email
- **LOCATION**: Product/form name
- **📝 [Question Label]**: Response text/transcription
- **🔗 [Question Label]**: Share URL for the response

#### Local Backup
All webhook payloads are automatically backed up to `webhook_data/` with the format:
```
YYYYMMDD_HHMMSS_contact_name.json
```

## File Structure
- `app.py`: Main Flask application with VideoAsk webhook integration
- `process_uploads.py`: Bulk file processing script
- `test_videoask_webhook.py`: VideoAsk webhook testing suite
- `uploads/`: Directory for files to be processed
- `transcripts/`: Directory for local JSON transcripts
- `webhook_data/`: Directory for VideoAsk webhook backups
- `templates/`: HTML templates
- `static/`: Static assets

## Testing
Run the audio transcription test suite:
```bash
python -m pytest test_app.py
```

Run the VideoAsk webhook test suite:
```bash
python test_videoask_webhook.py
```

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.spaces ♥️ Flask

Welcome to your shiny new Codespace running Flask! We've got everything fired up and running for you to explore Flask.

You've got a blank canvas to work on from a git perspective as well. There's a single initial commit with the what you're seeing right now - where you go from here is up to you!

Everything you do here is contained within this one codespace. There is no repository on GitHub yet. If and when you’re ready you can click "Publish Branch" and we’ll create your repository and push up your project. If you were just exploring then and have no further need for this code then you can simply delete your codespace and it's gone forever.

To run this application:

```
flask --debug run
```
