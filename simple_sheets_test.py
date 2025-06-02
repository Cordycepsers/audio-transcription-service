"""
Simple Google Sheets Access Test
This script attempts to access Google Sheets with minimal dependencies.
"""

import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def test_google_sheets_access():
    print("\n🧪 GOOGLE SHEETS ACCESS TEST")
    print("=" * 50)
    
    # Step 1: Load service account
    print("\n📂 Loading service account...")
    try:
        # Define scope
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        
        # Get credentials
        creds = ServiceAccountCredentials.from_json_keyfile_name('service-account.json', scope)
        print("✅ Service account credentials loaded")
        
        # Authorize client
        client = gspread.authorize(creds)
        print("✅ Client authorized")
        
        # Attempt to open spreadsheet
        sheet_id = '1s6OxhfqfQfxHH4M4ln1C1hrN3DWM8HI_-QJlY_p-KRU'
        try:
            spreadsheet = client.open_by_key(sheet_id)
            print(f"✅ Successfully opened spreadsheet: {spreadsheet.title}")
            
            # List worksheets
            worksheets = spreadsheet.worksheets()
            print(f"📊 Available worksheets: {[ws.title for ws in worksheets]}")
            
            # Try to access TRANSCRIPT FINAL worksheet
            try:
                worksheet = spreadsheet.worksheet("TRANSCRIPT FINAL")
                print(f"✅ Successfully accessed TRANSCRIPT FINAL worksheet")
                
                # Try to read data
                try:
                    headers = worksheet.row_values(1)
                    print(f"✅ Successfully read data from worksheet")
                    print(f"📝 First few headers: {headers[:3]}")
                    
                    # Try to write data
                    try:
                        test_cell = "Z1"
                        test_value = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        worksheet.update(test_cell, test_value)
                        print(f"✅ Successfully wrote test value to cell {test_cell}")
                        
                        # Clean up
                        worksheet.update(test_cell, "")
                        print(f"✅ Cleaned up test cell")
                        
                        print("\n🎉 ALL TESTS PASSED! Google Sheets integration is working!")
                        
                    except Exception as e:
                        print(f"❌ Failed to write to worksheet: {str(e)}")
                        print("   This usually means the service account needs Editor permissions")
                        
                except Exception as e:
                    print(f"❌ Failed to read data from worksheet: {str(e)}")
                
            except gspread.exceptions.WorksheetNotFound:
                print(f"❌ Worksheet 'TRANSCRIPT FINAL' not found")
                print(f"   Available worksheets: {[ws.title for ws in worksheets]}")
            
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"❌ Spreadsheet not found with ID: {sheet_id}")
            print("   This usually means:")
            print("   1. The spreadsheet ID is incorrect")
            print("   2. The service account doesn't have access to the spreadsheet")
            print("\n⚠️ IMPORTANT: You need to share the spreadsheet with:")
            print("   1053893186121-compute@developer.gserviceaccount.com")
            
        except gspread.exceptions.APIError as e:
            print(f"❌ Google Sheets API error: {str(e)}")
            print("   This usually means:")
            print("   1. Google Sheets API is not enabled in the Google Cloud project")
            print("   2. The service account doesn't have the necessary permissions")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_google_sheets_access()
