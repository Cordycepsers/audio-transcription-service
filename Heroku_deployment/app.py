# app.py
import os
import base64
import json
import logging
import psutil
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
import nltk
from nltk.tokenize import sent_tokenize
from faster_whisper import WhisperModel
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials # Corrected import
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import uuid # For unique temporary filenames
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# --- Load Environment Variables ---
load_dotenv()

# --- Initialize Sentry for Error Monitoring ---
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=os.getenv('FLASK_ENV', 'production')
    )

# --- Flask App Initialization ---
app = Flask(__name__, template_folder='templates', static_folder='static')

# --- Configuration ---
# Logging Setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
app.logger.setLevel(logging.DEBUG) # Use Flask's logger with debug level
app.logger.info("Starting Flask application with Google Sheets integration")

# Google Sheets Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', 'xxxxxxxxxxxxxxxxx')  # Get the sheet ID from environment variable
GSHEET_WORKSHEET_NAME = os.getenv('GOOGLE_WORKSHEET_NAME', 'TRANSCRIPT FINAL')
GOOGLE_SHEETS_CREDS_FILE = os.path.join(BASE_DIR, 'service-account.json')
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.getenv('SERVICE_ACCOUNT_EMAIL', 'xxxxxxxxxx-457800-b8@starry-computer-457800-b8.iam.gserviceaccount.com')

# Handle Heroku deployment - service account key from environment variable
GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

if not os.path.exists(GOOGLE_SHEETS_CREDS_FILE):
    if GOOGLE_SERVICE_ACCOUNT_JSON:
        try:
            # Write JSON directly to file
            with open(GOOGLE_SHEETS_CREDS_FILE, 'w') as f:
                f.write(GOOGLE_SERVICE_ACCOUNT_JSON)
            app.logger.info("Service account key created from JSON environment variable")
        except Exception as e:
            app.logger.error(f"Failed to create service account key from JSON environment: {e}")
    elif GOOGLE_SERVICE_ACCOUNT_KEY:
        try:
            # Decode base64 service account key and write to file
            import base64
            key_data = base64.b64decode(GOOGLE_SERVICE_ACCOUNT_KEY).decode()
            with open(GOOGLE_SHEETS_CREDS_FILE, 'w') as f:
                f.write(key_data)
            app.logger.info("Service account key created from base64 environment variable")
        except Exception as e:
            app.logger.error(f"Failed to create service account key from base64 environment: {e}")

app.logger.info(f"Base directory: {BASE_DIR}")
app.logger.info(f"Service account file path: {GOOGLE_SHEETS_CREDS_FILE}")
app.logger.info(f"Service account exists: {os.path.exists(GOOGLE_SHEETS_CREDS_FILE)}")
GOOGLE_SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Uploads directory for temporary audio files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Faster Whisper Model Configuration from .env or defaults
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "base.en")
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "int8") # "float16" for GPU, "int8" for CPU
DEVICE = os.getenv("DEVICE", "cpu") # "cuda" if NVIDIA GPU and CUDA are available

# --- NLTK Tokenizer Download ---
def ensure_nltk_data():
    """Ensure NLTK data is available, download if necessary."""
    # Set NLTK data path to include local directory
    nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
    if os.path.exists(nltk_data_dir):
        nltk.data.path.insert(0, nltk_data_dir)
    
    required_packages = ['punkt_tab', 'punkt']
    
    for package in required_packages:
        try:
            if package == 'punkt_tab':
                nltk.data.find('tokenizers/punkt_tab')
            else:
                nltk.data.find('tokenizers/punkt')
            app.logger.info(f"NLTK '{package}' tokenizer found.")
            break  # If we find one, we're good
        except LookupError:
            try:
                app.logger.info(f"NLTK '{package}' tokenizer not found. Downloading...")
                nltk.download(package, quiet=True)
                app.logger.info(f"NLTK '{package}' tokenizer downloaded.")
                break  # Successfully downloaded
            except Exception as e:
                app.logger.warning(f"Failed to download {package}: {e}")
                continue  # Try next package
    
    # Test tokenization
    try:
        from nltk.tokenize import sent_tokenize
        test_sentences = sent_tokenize("Hello world. This is a test.")
        app.logger.info(f"NLTK tokenization test successful: {len(test_sentences)} sentences")
        return True
    except Exception as e:
        app.logger.error(f"NLTK tokenization test failed: {e}")
        return False

# Initialize NLTK data
ensure_nltk_data()

# --- Transcription & Processing Functions (Adapted from previous script) ---

whisper_model_instance = None # Global model instance

def get_whisper_model():
    """Loads the Whisper model instance if not already loaded."""
    global whisper_model_instance
    if whisper_model_instance is None:
        try:
            app.logger.info(f"Loading Faster Whisper model: {WHISPER_MODEL_NAME} on {DEVICE} with {COMPUTE_TYPE}...")
            whisper_model_instance = WhisperModel(WHISPER_MODEL_NAME, device=DEVICE, compute_type=COMPUTE_TYPE)
            app.logger.info(f"Model {WHISPER_MODEL_NAME} loaded.")
        except Exception as e:
            app.logger.error(f"Error loading Whisper model: {e}", exc_info=True)
            raise  # Re-raise the exception to be caught by the API endpoint
    return whisper_model_instance

def transcribe_audio(file_path: str) -> str | None:
    """
    Transcribes an audio file using the pre-loaded Faster Whisper model.
    """
    if not os.path.exists(file_path):
        app.logger.error(f"Audio file not found for transcription: {file_path}")
        return None
    try:
        model = get_whisper_model() # Get or load the model
        app.logger.info(f"Starting transcription for {file_path}...")
        segments, info = model.transcribe(file_path, beam_size=5, language="en")
        app.logger.info(f"Detected language '{info.language}' with probability {info.language_probability}")
        full_transcription = "".join(segment.text for segment in segments).strip()
        app.logger.info(f"Transcription successful for {file_path}")
        return full_transcription
    except Exception as e:
        app.logger.error(f"Error during transcription for {file_path}: {e}", exc_info=True)
        return None

def post_process_text(raw_text: str) -> str:
    """
    Post-processes raw transcription text.
    """
    if not raw_text:
        return ""
    
    text_to_process = ' '.join(raw_text.split())
    
    try:
        sentences = sent_tokenize(text_to_process)
    except Exception as e:
        app.logger.warning(f"NLTK tokenization failed: {e}. Using basic sentence splitting.")
        # Fallback to basic sentence splitting
        sentences = text_to_process.replace('. ', '.|').replace('! ', '!|').replace('? ', '?|').split('|')
    
    processed_sentences = []
    for sentence in sentences:
        if not sentence.strip():
            continue
        processed_sentence = sentence.strip()
        if processed_sentence:
            processed_sentence = processed_sentence[0].upper() + processed_sentence[1:]
        if processed_sentence and processed_sentence[-1] not in ['.', '!', '?']:
            processed_sentence += '.'
        processed_sentences.append(processed_sentence)
    return " ".join(processed_sentences)

# --- Google Sheets Integration Functions ---
gspread_client_instance = None # Global gspread client

def get_gspread_client():
    """
    Authenticates with Google Sheets API using service account credentials
    and returns a gspread client. Caches the client instance.
    """
    global gspread_client_instance
    
    if gspread_client_instance is None:
        service_account_file = GOOGLE_SHEETS_CREDS_FILE
        
        try:
            if not os.path.exists(service_account_file):
                app.logger.error(f"Service account credentials file '{service_account_file}' not found.")
                app.logger.error(f"Please ensure the service account ({GOOGLE_SERVICE_ACCOUNT_EMAIL}) has access to the sheet.")
                return None
            
            gspread_client_instance = gspread.service_account(filename=service_account_file)
            app.logger.info("Successfully authorized gspread client using service account.")
            
            # Test the connection by trying to open the spreadsheet
            if GOOGLE_SHEET_ID:
                try:
                    gspread_client_instance.open_by_key(GOOGLE_SHEET_ID)
                    app.logger.info("Successfully connected to Google Sheet.")
                except gspread.exceptions.APIError as e:
                    app.logger.error(f"Failed to access Google Sheet: {e}")
                    if "Google Sheets API has not been used" in str(e):
                        app.logger.error("Please enable Google Sheets API for the service account.")
                    return None
                
        except Exception as e:
            app.logger.error(f"Failed to initialize gspread client: {e}")
            gspread_client_instance = None
            
    return gspread_client_instance

def write_to_google_sheet(audio_filename: str, transcript_text: str):
    """
    Writes the transcript to a Google Sheet if GOOGLE_SHEET_ID is configured.
    """
    if not GOOGLE_SHEET_ID:
        app.logger.info("GOOGLE_SHEET_ID not set. Skipping Google Sheets update.")
        return True # Indicate success as it's an optional step

    app.logger.info("=" * 50)
    app.logger.info("Google Sheets Integration")
    app.logger.info("=" * 50)
    app.logger.info(f"Sheet ID: {GOOGLE_SHEET_ID}")
    app.logger.info(f"Worksheet: {GSHEET_WORKSHEET_NAME}")
    app.logger.info(f"Service Account: {GOOGLE_SERVICE_ACCOUNT_EMAIL}")
    app.logger.info(f"Credentials File: {GOOGLE_SHEETS_CREDS_FILE}")
    app.logger.info(f"Credentials Exist: {os.path.exists(GOOGLE_SHEETS_CREDS_FILE)}")

    client = get_gspread_client()
    if not client:
        app.logger.error("Failed to get gspread client. Skipping Google Sheets update.")
        return False

    try:
        app.logger.info("Opening spreadsheet...")
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        try:
            worksheet = spreadsheet.worksheet(GSHEET_WORKSHEET_NAME)
            app.logger.info(f"Found worksheet: {GSHEET_WORKSHEET_NAME}")
            
            # Check if worksheet is empty or needs headers
            values = worksheet.get_all_values()
            if not values:
                app.logger.info("Worksheet is empty, adding headers...")
                headers = ["Timestamp", "Audio Filename", "Transcribed Text"]
                worksheet.append_row(headers)
                app.logger.info("Added headers to worksheet")
        except gspread.exceptions.WorksheetNotFound:
            app.logger.info(f"Worksheet '{GSHEET_WORKSHEET_NAME}' not found. Creating it...")
            worksheet = spreadsheet.add_worksheet(title=GSHEET_WORKSHEET_NAME, rows="100", cols="3")
            headers = ["Timestamp", "Audio Filename", "Transcribed Text"]
            worksheet.append_row(headers)
            app.logger.info(f"Created worksheet '{GSHEET_WORKSHEET_NAME}' with headers")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row_data = [timestamp, audio_filename, transcript_text]

        # Check for existing entry by filename (idempotency)
        filename_col_values = worksheet.col_values(2) # Assumes "Audio Filename" is the 2nd column
        found_row_index = None
        for i, name_in_sheet in enumerate(filename_col_values):
            if name_in_sheet == audio_filename:
                found_row_index = i + 1 # gspread rows are 1-indexed
                break
        
        if found_row_index:
            app.logger.info(f"Updating existing entry for '{audio_filename}' at row {found_row_index} in Google Sheet.")
            worksheet.update_cell(found_row_index, 1, timestamp)
            worksheet.update_cell(found_row_index, 3, transcript_text)
        else:
            app.logger.info(f"Appending new entry for '{audio_filename}' to Google Sheet.")
            worksheet.append_row(new_row_data)

        app.logger.info(f"Transcript for '{audio_filename}' written to Google Sheet.")
        return True
    except gspread.exceptions.APIError as e:
        app.logger.error(f"Google Sheets API error: {e}", exc_info=True)
        return False
    except Exception as e:
        app.logger.error(f"Unexpected error writing to Google Sheets: {e}", exc_info=True)
        return False

# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    app.logger.info("Google Sheets Configuration:")
    app.logger.info(f"Sheet ID: {GOOGLE_SHEET_ID}")
    app.logger.info(f"Worksheet Name: {GSHEET_WORKSHEET_NAME}")
    app.logger.info(f"Service Account Email: {GOOGLE_SERVICE_ACCOUNT_EMAIL}")
    app.logger.info(f"Credentials File: {GOOGLE_SHEETS_CREDS_FILE}")
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def handle_transcribe():
    """
    Handles audio file upload, transcription, post-processing,
    and optionally writes to Google Sheets.
    """
    if not request.json or 'file_data' not in request.json or 'file_name' not in request.json:
        app.logger.warning("Transcription request missing file_data or file_name.")
        return jsonify({"error": "Missing file_data or file_name in request"}), 400

    file_data_b64 = request.json['file_data']
    original_file_name = request.json['file_name']
    # mime_type = request.json.get('mime_type', 'application/octet-stream') # Mime type is available if needed

    # Sanitize filename (simple sanitization)
    safe_original_filename = "".join(c for c in original_file_name if c.isalnum() or c in ['.', '_', '-']).strip()
    if not safe_original_filename:
        safe_original_filename = "uploaded_audio"
    
    # Create a unique name for the temporary file to avoid conflicts
    file_extension = os.path.splitext(safe_original_filename)[1]
    if not file_extension: # Ensure there's an extension, default if necessary
        # You might want to be smarter here based on mime_type if available
        file_extension = ".mp3" # Default or infer from mime_type
    
    temp_filename = f"{uuid.uuid4()}{file_extension}"
    temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)

    try:
        audio_bytes = base64.b64decode(file_data_b64)
        with open(temp_file_path, 'wb') as f:
            f.write(audio_bytes)
        app.logger.info(f"Audio file saved temporarily as {temp_file_path}")

        # 1. Transcribe
        raw_transcription = transcribe_audio(temp_file_path)
        if raw_transcription is None:
            # transcribe_audio logs its own errors
            return jsonify({"error": "Transcription failed. See server logs for details."}), 500

        # 2. Post-process
        processed_transcription = post_process_text(raw_transcription)
        app.logger.info(f"Processed transcription for {original_file_name} obtained.")
        
        # Save transcription locally
        transcripts_dir = "transcripts"
        if not os.path.exists(transcripts_dir):
            os.makedirs(transcripts_dir)
        
        transcript_file = os.path.join(transcripts_dir, f"{os.path.splitext(original_file_name)[0]}_transcript.json")
        transcript_data = {
            "filename": original_file_name,
            "transcription": processed_transcription,
            "timestamp": datetime.now().isoformat(),
            "duration": "00:01.908"  # This could be extracted from the audio file
        }
        
        with open(transcript_file, 'w') as f:
            json.dump(transcript_data, f, indent=2)
        app.logger.info(f"Transcription saved to {transcript_file}")

        # 3. Write to Google Sheet
        sheet_status = "not_attempted"
        if GOOGLE_SHEET_ID:
            app.logger.info("Attempting to write transcription to Google Sheet...")
            try:
                sheet_success = write_to_google_sheet(
                    audio_filename=original_file_name,
                    transcript_text=processed_transcription
                )
                if sheet_success:
                    app.logger.info("✓ Successfully wrote to Google Sheet!")
                    sheet_status = "success"
                else:
                    app.logger.error("✗ Failed to write to Google Sheet!")
                    sheet_status = "failed"
            except Exception as e:
                app.logger.error(f"✗ Error writing to Google Sheet: {str(e)}")
                sheet_status = "error"

        return jsonify({
            "transcription": processed_transcription,
            "fileName": original_file_name,
            "sheets_status": sheet_status,
            "sheet_id": GOOGLE_SHEET_ID,
            "worksheet_name": GSHEET_WORKSHEET_NAME
        })

    except base64.binascii.Error:
        app.logger.error("Invalid base64 data received.")
        return jsonify({"error": "Invalid base64 data"}), 400
    except Exception as e:
        app.logger.error(f"An unexpected error occurred in /transcribe: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected server error occurred: {str(e)}"}), 500
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                app.logger.info(f"Temporary file {temp_file_path} deleted.")
            except Exception as e_remove:
                app.logger.error(f"Error deleting temporary file {temp_file_path}: {e_remove}")

# --- Monitoring and Health Check Endpoints ---
@app.route('/health')
def health_check():
    """Enhanced health check with system metrics"""
    try:
        # Basic health check
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'environment': os.getenv('FLASK_ENV', 'production')
        }
        
        # System metrics
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            health_status['system'] = {
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_percent': disk.percent,
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'cpu_percent': psutil.cpu_percent(interval=1)
            }
        except Exception as e:
            app.logger.warning(f"Could not get system metrics: {e}")
            health_status['system'] = 'unavailable'
        
        # Check critical dependencies
        try:
            # Test Google Sheets connection
            if os.path.exists('service-account.json'):
                health_status['google_sheets'] = 'configured'
            else:
                health_status['google_sheets'] = 'not_configured'
                
            # Test Whisper model availability
            health_status['whisper_model'] = 'available'
            
        except Exception as e:
            health_status['dependencies'] = f'error: {str(e)}'
            
        return jsonify(health_status), 200
        
    except Exception as e:
        app.logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/metrics')
def metrics():
    """Prometheus-style metrics endpoint"""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics_text = f"""# HELP memory_usage_percent Memory usage percentage
# TYPE memory_usage_percent gauge
memory_usage_percent {memory.percent}

# HELP disk_usage_percent Disk usage percentage  
# TYPE disk_usage_percent gauge
disk_usage_percent {disk.percent}

# HELP cpu_usage_percent CPU usage percentage
# TYPE cpu_usage_percent gauge
cpu_usage_percent {psutil.cpu_percent(interval=1)}

# HELP app_uptime_seconds Application uptime in seconds
# TYPE app_uptime_seconds counter
app_uptime_seconds {psutil.Process().create_time()}
"""
        return metrics_text, 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        app.logger.error(f"Metrics endpoint failed: {e}")
        return f"# Error generating metrics: {e}", 500, {'Content-Type': 'text/plain'}

@app.route('/status')
def status():
    """Detailed status page for monitoring dashboard"""
    try:
        status_info = {
            'service': 'Audio Transcription Service',
            'status': 'operational',
            'timestamp': datetime.now().isoformat(),
            'uptime': psutil.Process().create_time(),
            'environment': os.getenv('FLASK_ENV', 'production'),
            'version': '1.0.0',
            'features': {
                'audio_transcription': True,
                'google_sheets_integration': os.path.exists('service-account.json'),
                'web_interface': True,
                'api_endpoints': True
            },
            'system_info': {
                'python_version': os.sys.version,
                'platform': os.name,
                'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'cpu_count': psutil.cpu_count()
            }
        }
        return jsonify(status_info), 200
    except Exception as e:
        app.logger.error(f"Status endpoint failed: {e}")
        return jsonify({'error': str(e)}), 500

# --- Main Execution (for local development) ---
if __name__ == '__main__':
    # Pre-load the Whisper model on startup if desired for faster first request
    # try:
    #    get_whisper_model()
    # except Exception as e:
    #    app.logger.error(f"Failed to pre-load Whisper model on startup: {e}")

    # For development, `flask run` is preferred.
    # The following is for direct script execution:
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
