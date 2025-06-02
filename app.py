# app.py
import os
import base64
import json
import logging
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

# --- Load Environment Variables ---
load_dotenv()

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
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')  # Get the sheet ID from environment variable
GSHEET_WORKSHEET_NAME = os.getenv('GSHEET_WORKSHEET_NAME', 'TRANSCRIPT FINAL')
GOOGLE_SHEETS_CREDS_FILE = os.path.join(BASE_DIR, 'service-account.json')
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.getenv('GOOGLE_SERVICE_ACCOUNT_EMAIL', 'transcript@transcript-460922.iam.gserviceaccount.com')

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

# --- NLTK 'punkt' Tokenizer Download ---
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    app.logger.info("NLTK 'punkt' tokenizer not found. Downloading...")
    nltk.download('punkt', quiet=True)
    app.logger.info("NLTK 'punkt' tokenizer downloaded.")

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
    sentences = sent_tokenize(text_to_process)
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

# --- VideoAsk Webhook Functions ---
def map_videoask_to_sheet(contact, form):
    """
    Map VideoAsk data to Google Sheet columns.
    
    Args:
        contact (dict): Contact information from webhook
        form (dict): Form information from webhook
        
    Returns:
        dict: Mapped data ready for Google Sheet
    """
    # Initialize mapped data with empty values
    mapped_data = {
        'Name': '',
        'DATE': '',
        'EMAIL': '',
        'LOCATION': '',
        '🔗 Introduce Yourself': '',
        '📝 Introduce Yourself': '',
        '🔗 Foundation\'s Influence': '',
        '📝 Foundation\'s Influence': '',
        '🔗 Sharing Advice': '',
        '📝 Sharing Advice': '',
        '🔗 Purpose & Joy': '',
        '📝 Purpose & Joy': '',
        '🔗 Staying Connected': '',
        '📝 Staying Connected': ''
    }
    
    # Map basic contact information
    mapped_data['Name'] = contact.get('name', '')
    
    # Format date from ISO to readable format
    created_at = contact.get('created_at', '')
    if created_at:
        # Convert ISO timestamp to datetime object
        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        # Format as YYYY-MM-DD HH:MM:SS
        mapped_data['DATE'] = dt.strftime('%Y-%m-%d %H:%M:%S')
    
    mapped_data['EMAIL'] = contact.get('email', '')
    mapped_data['LOCATION'] = contact.get('product_name', '')
    
    # Get questions from form
    questions = form.get('questions', [])
    question_map = {}
    
    # Create a mapping of question IDs to their titles/labels
    for question in questions:
        question_id = question.get('question_id')
        label = question.get('label', '')
        title = question.get('title', '')
        share_url = question.get('share_url', '')
        
        # Determine question type from label or title
        question_type = None
        if 'Introduce Yourself' in label or 'Introduce Yourself' in title:
            question_type = 'intro'
        elif 'Foundation\'s Influence' in label or 'Foundation\'s Influence' in title:
            question_type = 'influence'
        elif 'Sharing Advice' in label or 'Sharing Advice' in title:
            question_type = 'advice'
        elif 'Purpose & Joy' in label or 'Purpose & Joy' in title:
            question_type = 'purpose'
        elif 'Staying Connected' in label or 'Staying Connected' in title:
            question_type = 'connected'
        
        if question_type and question_id:
            question_map[question_id] = {
                'type': question_type,
                'share_url': share_url
            }
    
    # Process answers
    answers = contact.get('answers', [])
    for answer in answers:
        question_id = answer.get('question_id')
        if question_id not in question_map:
            continue
            
        question_type = question_map[question_id]['type']
        share_url = answer.get('share_url', question_map[question_id]['share_url'])
        
        # Get answer content based on type
        answer_content = ''
        if answer.get('type') == 'video' or answer.get('type') == 'audio':
            answer_content = answer.get('transcription', '')
        elif answer.get('type') == 'text':
            answer_content = answer.get('text', '')
        elif answer.get('type') == 'poll':
            answer_content = answer.get('poll_option_content', '')
        
        # Map to appropriate columns
        if question_type == 'intro':
            mapped_data['🔗 Introduce Yourself'] = share_url
            mapped_data['📝 Introduce Yourself'] = answer_content
        elif question_type == 'influence':
            mapped_data['🔗 Foundation\'s Influence'] = share_url
            mapped_data['📝 Foundation\'s Influence'] = answer_content
        elif question_type == 'advice':
            mapped_data['🔗 Sharing Advice'] = share_url
            mapped_data['📝 Sharing Advice'] = answer_content
        elif question_type == 'purpose':
            mapped_data['🔗 Purpose & Joy'] = share_url
            mapped_data['📝 Purpose & Joy'] = answer_content
        elif question_type == 'connected':
            mapped_data['🔗 Staying Connected'] = share_url
            mapped_data['📝 Staying Connected'] = answer_content
    
    return mapped_data

def update_videoask_google_sheet(sheet_data):
    """
    Update Google Sheet with the mapped VideoAsk data.
    
    Args:
        sheet_data (dict): Mapped data ready for Google Sheet
    """
    try:
        client = get_gspread_client()
        if not client:
            app.logger.error("Failed to get gspread client for VideoAsk webhook")
            return False

        # Get the VideoAsk sheet configuration
        videoask_sheet_id = os.getenv('VIDEOASK_GOOGLE_SHEET_ID', GOOGLE_SHEET_ID)
        videoask_worksheet_name = os.getenv('VIDEOASK_GSHEET_WORKSHEET_NAME', 'VideoAsk Responses')
        
        app.logger.info(f"Updating VideoAsk sheet: {videoask_sheet_id}, worksheet: {videoask_worksheet_name}")
        
        spreadsheet = client.open_by_key(videoask_sheet_id)
        
        try:
            worksheet = spreadsheet.worksheet(videoask_worksheet_name)
            app.logger.info(f"Found worksheet: {videoask_worksheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            app.logger.info(f"Worksheet '{videoask_worksheet_name}' not found. Creating it...")
            worksheet = spreadsheet.add_worksheet(title=videoask_worksheet_name, rows="1000", cols="27")
            # Add headers for VideoAsk data
            headers = [
                "Name", "HANNAH REV.", "DRE REV.", "DATE", "EMAIL", "LOCATION",
                "🔗 Introduce Yourself", "📝 Introduce Yourself",
                "🔗 Foundation's Influence", "📝 Foundation's Influence",
                "🔗 Sharing Advice", "📝 Sharing Advice",
                "🔗 Purpose & Joy", "📝 Purpose & Joy",
                "🔗 Staying Connected", "📝 Staying Connected",
                "YEARS AT FOUNDATION", "FOUNDATION TEAMS (AI)", "FOUNDATION TEAMS (MANUAL)",
                "VIDEO QUALITY?", "AUDIO QUALITY?", "POTENTIAL PATHWAYS USAGE",
                "CONFIRMED PATHWAYS USAGE", "WTYSL NOTES", "UNCOMMON NOTES",
                "25th Anniversary Storylines", "PROGRAMMATIC TAGS"
            ]
            worksheet.append_row(headers)
            app.logger.info(f"Created worksheet '{videoask_worksheet_name}' with headers")

        # Prepare row data in the correct column order
        row_data = [
            sheet_data['Name'],                     # Column A
            '',                                     # Column B (HANNAH REV.)
            '',                                     # Column C (DRE REV.)
            sheet_data['DATE'],                     # Column D
            sheet_data['EMAIL'],                    # Column E
            sheet_data['LOCATION'],                 # Column F
            sheet_data['🔗 Introduce Yourself'],    # Column G
            sheet_data['📝 Introduce Yourself'],    # Column H
            sheet_data['🔗 Foundation\'s Influence'], # Column I
            sheet_data['📝 Foundation\'s Influence'], # Column J
            sheet_data['🔗 Sharing Advice'],        # Column K
            sheet_data['📝 Sharing Advice'],        # Column L
            sheet_data['🔗 Purpose & Joy'],         # Column M
            sheet_data['📝 Purpose & Joy'],         # Column N
            sheet_data['🔗 Staying Connected'],     # Column O
            sheet_data['📝 Staying Connected'],     # Column P
            '',                                     # Column Q (YEARS AT FOUNDATION)
            '',                                     # Column R (FOUNDATION TEAMS (AI))
            '',                                     # Column S (FOUNDATION TEAMS (MANUAL))
            '',                                     # Column T (VIDEO QUALITY?)
            '',                                     # Column U (AUDIO QUALITY?)
            '',                                     # Column V (POTENTIAL PATHWAYS USAGE)
            '',                                     # Column W (CONFIRMED PATHWAYS USAGE)
            '',                                     # Column X (WTYSL NOTES)
            '',                                     # Column Y (UNCOMMON NOTES)
            '',                                     # Column Z (25th Anniversary Storylines)
            ''                                      # Column AA (PROGRAMMATIC TAGS)
        ]
        
        # Append the new row
        worksheet.append_row(row_data)
        
        app.logger.info(f"Successfully updated VideoAsk Google Sheet with data for {sheet_data['Name']}")
        return True
        
    except Exception as e:
        app.logger.error(f"Error updating VideoAsk Google Sheet: {str(e)}")
        return False

def save_local_copy(payload, sheet_data):
    """
    Save a local copy of the processed webhook data.
    
    Args:
        payload (dict): Original webhook payload
        sheet_data (dict): Mapped data for Google Sheet
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs('webhook_data', exist_ok=True)
        
        # Generate filename with timestamp and contact name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        contact_name = sheet_data['Name'].replace(' ', '_').lower()
        filename = f"webhook_data/{timestamp}_{contact_name}.json"
        
        # Save data
        with open(filename, 'w') as f:
            json.dump({
                'original_payload': payload,
                'mapped_data': sheet_data,
                'processed_at': datetime.now().isoformat()
            }, f, indent=2)
            
        app.logger.info(f"Saved local copy to {filename}")
        
    except Exception as e:
        app.logger.error(f"Error saving local copy: {str(e)}")

def process_videoask_payload(payload):
    """
    Process the VideoAsk webhook payload and update Google Sheet.
    
    Args:
        payload (dict): The webhook payload from VideoAsk
        
    Returns:
        dict: Processing results with statistics
    """
    # Initialize processing statistics
    processing_stats = {
        'processed': 0,
        'skipped': 0,
        'errors': 0,
        'email': '',
        'details': []
    }
    
    # Extract event type
    event_type = payload.get('event_type')
    
    # Only process form_response events
    if event_type != 'form_response':
        app.logger.info(f"Ignoring non-form_response event: {event_type}")
        processing_stats['skipped'] = 1
        processing_stats['details'].append(f"Skipped non-form_response event: {event_type}")
        return processing_stats
    
    # Extract contact information
    contact = payload.get('contact', {})
    form = payload.get('form', {})
    
    # Get email for tracking
    processing_stats['email'] = contact.get('email', 'unknown@email.com')
    
    try:
        # Map data according to our mapping logic
        sheet_data = map_videoask_to_sheet(contact, form)
        
        # Update Google Sheet with the mapped data
        sheet_success = update_videoask_google_sheet(sheet_data)
        
        if sheet_success:
            processing_stats['processed'] += 1
            processing_stats['details'].append("Successfully updated Google Sheet")
        else:
            processing_stats['errors'] += 1
            processing_stats['details'].append("Failed to update Google Sheet")
        
        # Save a local copy of the processed data
        try:
            save_local_copy(payload, sheet_data)
            processing_stats['details'].append("Local backup saved successfully")
        except Exception as backup_error:
            processing_stats['errors'] += 1
            processing_stats['details'].append(f"Local backup failed: {str(backup_error)}")
            
    except Exception as e:
        processing_stats['errors'] += 1
        processing_stats['details'].append(f"Processing error: {str(e)}")
        app.logger.error(f"Error in process_videoask_payload: {str(e)}")
    
    return processing_stats

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

@app.route('/webhook/videoask', methods=['POST'])
def videoask_webhook():
    """
    Endpoint to receive VideoAsk webhook payloads and process them.
    Returns delivery details with processing statistics.
    """
    # Get JSON payload
    payload = request.json
    
    if not payload:
        app.logger.warning("VideoAsk webhook: No payload received")
        error_response = "Webhook received and processed: No payload received - Processed=0, Skipped=0, Errors=1"
        return error_response, 400, {'Content-Type': 'text/html; charset=utf-8'}
    
    try:
        app.logger.info(f"Received VideoAsk webhook: {payload.get('event_type', 'unknown')}")
        
        # Process the webhook payload and get processing statistics
        processing_stats = process_videoask_payload(payload)
        
        # Create delivery details response
        email = processing_stats.get('email', 'unknown@email.com')
        processed = processing_stats.get('processed', 0)
        skipped = processing_stats.get('skipped', 0)
        errors = processing_stats.get('errors', 0)
        
        delivery_response = f"Webhook received and processed: Webhook processing summary for email {email}: Processed={processed}, Skipped={skipped}, Errors={errors}"
        
        app.logger.info(f"VideoAsk webhook processed - {delivery_response}")
        
        # Return response with proper headers matching the example
        return delivery_response, 200, {
            'Content-Type': 'text/html; charset=utf-8',
            'Server': 'Digital Ocean',
            'Content-Length': str(len(delivery_response))
        }
        
    except Exception as e:
        # Log the error
        app.logger.error(f"Error processing VideoAsk webhook: {str(e)}")
        error_response = f"Webhook received and processed: Processing error - Processed=0, Skipped=0, Errors=1"
        return error_response, 500, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/webhook/test', methods=['POST'])
def test_webhook():
    """
    Test endpoint for webhook functionality with sample data.
    """
    sample_payload = {
        "event_type": "form_response",
        "contact": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "created_at": "2025-06-02T10:30:00Z",
            "product_name": "Test Location",
            "answers": [
                {
                    "question_id": "intro_q1",
                    "type": "video",
                    "transcription": "Hello, my name is John and I'm excited to share my story.",
                    "share_url": "https://example.com/share/intro"
                },
                {
                    "question_id": "influence_q1",
                    "type": "text",
                    "text": "The foundation has greatly influenced my career path.",
                    "share_url": "https://example.com/share/influence"
                }
            ]
        },
        "form": {
            "questions": [
                {
                    "question_id": "intro_q1",
                    "label": "Introduce Yourself",
                    "title": "Tell us about yourself",
                    "share_url": "https://example.com/share/intro"
                },
                {
                    "question_id": "influence_q1",
                    "label": "Foundation's Influence",
                    "title": "How has the foundation influenced you?",
                    "share_url": "https://example.com/share/influence"
                }
            ]
        }
    }
    
    try:
        app.logger.info("Processing test webhook payload")
        
        # Process the test payload
        process_videoask_payload(sample_payload)
        
        # Also return the mapped data for inspection
        contact = sample_payload.get('contact', {})
        form = sample_payload.get('form', {})
        mapped_data = map_videoask_to_sheet(contact, form)
        
        return jsonify({
            'status': 'success',
            'message': 'Test payload processed successfully',
            'mapped_data': mapped_data
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error processing test webhook: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/webhook/validate', methods=['GET'])
def validate_webhook_config():
    """
    Validate webhook configuration and Google Sheets access.
    """
    validation_results = {
        'google_sheets_client': False,
        'videoask_sheet_access': False,
        'webhook_data_directory': False,
        'environment_variables': {}
    }
    
    # Test Google Sheets client
    try:
        client = get_gspread_client()
        if client:
            validation_results['google_sheets_client'] = True
            
            # Test VideoAsk sheet access
            videoask_sheet_id = os.getenv('VIDEOASK_GOOGLE_SHEET_ID', GOOGLE_SHEET_ID)
            if videoask_sheet_id:
                try:
                    spreadsheet = client.open_by_key(videoask_sheet_id)
                    validation_results['videoask_sheet_access'] = True
                except Exception as e:
                    validation_results['videoask_sheet_error'] = str(e)
    except Exception as e:
        validation_results['google_sheets_error'] = str(e)
    
    # Check webhook data directory
    try:
        os.makedirs('webhook_data', exist_ok=True)
        validation_results['webhook_data_directory'] = os.path.exists('webhook_data')
    except Exception as e:
        validation_results['webhook_data_error'] = str(e)
    
    # Check environment variables
    env_vars = [
        'GOOGLE_SHEET_ID',
        'VIDEOASK_GOOGLE_SHEET_ID',
        'GSHEET_WORKSHEET_NAME', 
        'VIDEOASK_GSHEET_WORKSHEET_NAME'
    ]
    
    for var in env_vars:
        validation_results['environment_variables'][var] = os.getenv(var) is not None
    
    return jsonify(validation_results), 200

# --- Main Execution (for local development) ---
if __name__ == '__main__':
    # Pre-load the Whisper model on startup if desired for faster first request
    # try:
    #    get_whisper_model()
    # except Exception as e:
    #    app.logger.error(f"Failed to pre-load Whisper model on startup: {e}")

    # For development, `flask run` is preferred.
    # The following is for direct script execution:
    app.run(debug=True, host='0.0.0.0', port=8000)
