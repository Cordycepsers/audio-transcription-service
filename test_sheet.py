import gspread
from datetime import datetime

def test_sheet_access():
    print("Testing Google Sheet access...")
    try:
        # Connect using service account
        gc = gspread.service_account(filename='service-account.json')
        print("✓ Connected to Google Sheets API")
        
        # Open spreadsheet
        sheet_id = "1s6OxhfqfQfxHH4M4ln1C1hrN3DWM8HI_-QJlY_p-KRU"
        sheet = gc.open_by_key(sheet_id)
        print(f"✓ Opened sheet: {sheet.title}")
        
        # Try to access/create worksheet
        try:
            worksheet = sheet.worksheet("TRANSCRIPT FINAL")
            print("✓ Found existing worksheet 'TRANSCRIPT FINAL'")
        except gspread.exceptions.WorksheetNotFound:
            print("! Worksheet not found, creating new one...")
            worksheet = sheet.add_worksheet("TRANSCRIPT FINAL", rows=100, cols=3)
            worksheet.append_row(["Timestamp", "Audio Filename", "Transcribed Text"])
            print("✓ Created new worksheet with headers")
            
        # Try writing a test row
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_row = [timestamp, "test_file.mp4", "This is a test transcript"]
        worksheet.append_row(test_row)
        print("✓ Successfully wrote test row to sheet")
        
        # Read back the last row to verify
        all_values = worksheet.get_all_values()
        if len(all_values) > 0:
            print("\nLast row in sheet:")
            print(all_values[-1])
        else:
            print("! Sheet is empty after writing")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    test_sheet_access()
