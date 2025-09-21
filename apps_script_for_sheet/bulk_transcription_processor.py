#!/usr/bin/env python3
"""
Bulk transcription processor for uploaded files
"""
import os
import gspread
from datetime import datetime
import time
from app import transcribe_audio, post_process_text

def process_uploads_folder():
    """Process all files in the uploads folder and write to Google Sheet"""
    print("\n🔍 Processing uploads folder...")
    
    # Connect to Google Sheets
    print("\n🔑 Connecting to Google Sheets...")
    gc = gspread.service_account(filename='service-account.json')
    sheet = gc.open_by_key("1s6OxhfqfQfxHH4M4ln1C1hrN3DWM8HI_-QJlY_p-KRU")
    worksheet = sheet.worksheet("TRANSCRIPT FINAL")
    
    # Get list of files in uploads folder
    upload_dir = "uploads"
    files = [f for f in os.listdir(upload_dir) 
             if f.endswith(('.mp3', '.mp4')) and not f.startswith('.')]
    files.sort()  # Process files in alphabetical order
    
    print(f"\n📂 Found {len(files)} files to process")
    
    # Process each file
    for i, filename in enumerate(files, 1):
        file_path = os.path.join(upload_dir, filename)
        print(f"\n[{i}/{len(files)}] Processing: {filename}")
        
        try:
            # 1. Transcribe
            print("  🎯 Transcribing...")
            transcription = transcribe_audio(file_path)
            if not transcription:
                print("  ❌ Transcription failed")
                continue
                
            # 2. Post-process
            processed_text = post_process_text(transcription)
            
            # 3. Write to sheet
            print("  📝 Writing to Google Sheet...")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_row = [timestamp, filename, processed_text]
            worksheet.append_row(new_row)
            
            print("  ✅ Success!")
            # Small delay to avoid rate limits
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Error processing {filename}: {str(e)}")
            continue
    
    print("\n✨ Processing complete!")
    print("Check the Google Sheet for results.")

if __name__ == "__main__":
    process_uploads_folder()
