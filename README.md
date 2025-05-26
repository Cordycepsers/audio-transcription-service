# Flask Audio Transcription Service

This Flask application provides an audio transcription service with Google Sheets integration. It can process both MP3 and MP4 files, transcribing their audio content using the Whisper model and storing the results in both local JSON files and a Google Sheet.

## Features

- Audio/Video transcription using Whisper model
- Google Sheets integration for transcript storage
- Bulk file processing support
- Web interface for single file uploads
- Support for MP3 and MP4 files
- Local JSON storage of transcripts

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
GOOGLE_SHEET_ID="your-sheet-id"
GSHEET_WORKSHEET_NAME="TRANSCRIPT FINAL"
GOOGLE_SHEETS_CREDS_FILE="service-account.json"
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

## File Structure
- `app.py`: Main Flask application
- `process_uploads.py`: Bulk file processing script
- `uploads/`: Directory for files to be processed
- `transcripts/`: Directory for local JSON transcripts
- `templates/`: HTML templates
- `static/`: Static assets

## Testing
Run the test suite:
```bash
python -m pytest test_app.py
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
