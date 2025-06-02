#!/usr/bin/env python3
"""
Quick Google Sheets Connection Test
Run this after completing the setup steps.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def test_google_sheets():
    print("🧪 Quick Google Sheets Test")
    print("=" * 40)
    
    try:
        # Create client
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = ServiceAccountCredentials.from_json_keyfile_name('service-account.json', scope)
        client = gspread.authorize(creds)
        print("✅ Google Sheets client created")
        
        # Open spreadsheet
        sheet_id = '1s6OxhfqfQfxHH4M4ln1C1hrN3DWM8HI_-QJlY_p-KRU'
        spreadsheet = client.open_by_key(sheet_id)
        print(f"✅ Opened spreadsheet: {spreadsheet.title}")
        
        # List worksheets
        worksheets = [ws.title for ws in spreadsheet.worksheets()]
        print(f"📊 Available worksheets: {worksheets}")
        
        # Test TRANSCRIPT FINAL worksheet
        if 'TRANSCRIPT FINAL' in worksheets:
            worksheet = spreadsheet.worksheet('TRANSCRIPT FINAL')
            print("✅ TRANSCRIPT FINAL worksheet accessible")
            
            # Test write permission
            test_cell = 'AA1'  # Use a cell that won't interfere
            original_value = worksheet.acell(test_cell).value
            worksheet.update(test_cell, 'TEST')
            if worksheet.acell(test_cell).value == 'TEST':
                print("✅ Write permissions working")
                # Restore original value
                worksheet.update(test_cell, original_value or '')
            else:
                print("❌ Write permissions failed")
        else:
            print("❌ TRANSCRIPT FINAL worksheet not found")
        
        print("\n🎉 Google Sheets integration is working!")
        return True
        
    except gspread.SpreadsheetNotFound:
        print("❌ Spreadsheet not found")
        print("   → Share the spreadsheet with: 1053893186121-compute@developer.gserviceaccount.com")
        return False
        
    except gspread.APIError as e:
        print(f"❌ Google Sheets API Error: {e}")
        print("   → Enable Google Sheets API in Google Cloud Console")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_google_sheets()
