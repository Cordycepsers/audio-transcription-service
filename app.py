# app.py
import os
import base64
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app.logger.setLevel(logging.INFO) # Use Flask's logger

# Uploads directory for temporary audio files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Faster Whisper Model Configuration from .env or defaults
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "base.en")
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "int8") # "float16" for GPU, "int8" for CPU
DEVICE = os.getenv("DEVICE", "cpu") # "cuda" if NVIDIA GPU and CUDA are available

# Google Sheets Configuration from .env
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
GSHEET_WORKSHEET_NAME = os.getenv('GSHEET_WORKSHEET_NAME', 'Transcripts')
GSHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GSHEET_CREDENTIALS_FILE = 'credentials.json'
GSHEET_TOKEN_PICKLE = 'token.pickle'

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
    Authenticates with Google Sheets API and returns a gspread client.
    Caches the client instance.
    """
    global gspread_client_instance
    if gspread_client_instance:
        # Check if token needs refresh (simplified check, gspread might handle this internally too)
        if hasattr(gspread_client_instance, 'auth') and gspread_client_instance.auth.expired and gspread_client_instance.auth.refresh_token:
            try:
                gspread_client_instance.auth.refresh(Request())
                app.logger.info("Google Sheets token refreshed.")
            except Exception as e:
                app.logger.warning(f"Failed to refresh Google Sheets token: {e}. Will try re-authentication.")
                gspread_client_instance = None # Force re-auth

    if gspread_client_instance is None:
        creds = None
        if os.path.exists(GSHEET_TOKEN_PICKLE):
            with open(GSHEET_TOKEN_PICKLE, 'rb') as token_file:
                creds = pickle.load(token_file)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    app.logger.info("Google Sheets token refreshed during client acquisition.")
                except Exception as e:
                    app.logger.warning(f"Failed to refresh token: {e}. Re-authenticating.")
                    creds = None
            if not creds:
                if not os.path.exists(GSHEET_CREDENTIALS_FILE):
                    app.logger.error(f"Google Sheets credentials file ('{GSHEET_CREDENTIALS_FILE}') not found.")
                    # Not raising FileNotFoundError here as it's a server, 
                    # it should log and potentially skip GSheet operations.
                    return None 
                
                # For server environments, run_local_server might not be ideal.
                # Consider service account or pre-authorized token.pickle for production.
                flow = InstalledAppFlow.from_client_secrets_file(GSHEET_CREDENTIALS_FILE, GSHEET_SCOPES)
                app.logger.info("Attempting to run local server for Google OAuth. This may require browser interaction.")
                try:
                    # This part might hang if no browser interaction is possible
                    creds = flow.run_local_server(port=0) 
                except Exception as e:
                    app.logger.error(f"Could not complete OAuth flow: {e}. "
                                     "Ensure you can complete browser authentication or use a pre-authorized token.pickle / service account.")
                    return None

            if creds:
                with open(GSHEET_TOKEN_PICKLE, 'wb') as token_file:
                    pickle.dump(creds, token_file)
                app.logger.info(f"OAuth token saved to {GSHEET_TOKEN_PICKLE}")
        
        if creds:
            gspread_client_instance = gspread.authorize(creds)
            app.logger.info("Successfully authorized gspread client.")
        else:
            app.logger.error("Failed to obtain Google API credentials.")
            return None
            
    return gspread_client_instance

def write_to_google_sheet(audio_filename: str, transcript_text: str):
    """
    Writes the transcript to a Google Sheet if GOOGLE_SHEET_ID is configured.
    """
    if not GOOGLE_SHEET_ID:
        app.logger.info("GOOGLE_SHEET_ID not set. Skipping Google Sheets update.")
        return True # Indicate success as it's an optional step

    client = get_gspread_client()
    if not client:
        app.logger.error("Failed to get gspread client. Skipping Google Sheets update.")
        return False

    try:
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        try:
            worksheet = spreadsheet.worksheet(GSHEET_WORKSHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            app.logger.info(f"Worksheet '{GSHEET_WORKSHEET_NAME}' not found. Creating it.")
            worksheet = spreadsheet.add_worksheet(title=GSHEET_WORKSHEET_NAME, rows="100", cols="3")
            headers = ["Timestamp", "Audio Filename", "Transcribed Text"]
            worksheet.append_row(headers)
            app.logger.info(f"Worksheet '{GSHEET_WORKSHEET_NAME}' created with headers.")

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

        # 3. Write to Google Sheet (optional)
        if GOOGLE_SHEET_ID: # Only attempt if configured
            sheet_success = write_to_google_sheet(
                audio_filename=original_file_name, # Use original filename for Sheets
                transcript_text=processed_transcription
            )
            if not sheet_success:
                app.logger.warning(f"Failed to write to Google Sheet for {original_file_name}, but transcription was successful.")
                # Decide if this should be an error to the client or just a server-side warning
                # For now, we'll still return the transcription.

        return jsonify({"transcription": processed_transcription, "fileName": original_file_name})

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

# --- Main Execution (for local development) ---
if __name__ == '__main__':
    # Pre-load the Whisper model on startup if desired for faster first request
    # try:
    #    get_whisper_model()
    # except Exception as e:
    #    app.logger.error(f"Failed to pre-load Whisper model on startup: {e}")

    # For development, `flask run` is preferred.
    # The following is for direct script execution:
    app.run(debug=True, host='0.0.0.0', port=5000)
