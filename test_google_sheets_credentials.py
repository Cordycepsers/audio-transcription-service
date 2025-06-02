#!/usr/bin/env python3
"""
Comprehensive Google Sheets Credentials Test
This script tests all aspects of Google Sheets integration and provides detailed diagnostics.
"""

import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def test_service_account_file():
    """Test if service account JSON file exists and is valid."""
    print("🔍 Testing Service Account File...")
    
    creds_file = "service-account.json"
    if not os.path.exists(creds_file):
        print(f"❌ Service account file not found: {creds_file}")
        return False
    
    try:
        with open(creds_file, 'r') as f:
            creds_data = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds_data]
        
        if missing_fields:
            print(f"❌ Missing required fields in service account: {missing_fields}")
            return False
        
        print(f"✅ Service account file is valid")
        print(f"   Project ID: {creds_data.get('project_id')}")
        print(f"   Client Email: {creds_data.get('client_email')}")
        return True, creds_data
        
    except json.JSONDecodeError:
        print("❌ Service account file contains invalid JSON")
        return False
    except Exception as e:
        print(f"❌ Error reading service account file: {e}")
        return False

def test_google_sheets_client():
    """Test Google Sheets client creation."""
    print("\n🔍 Testing Google Sheets Client...")
    
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds = ServiceAccountCredentials.from_json_keyfile_name('service-account.json', scope)
        client = gspread.authorize(creds)
        
        print("✅ Google Sheets client created successfully")
        return True, client
        
    except FileNotFoundError:
        print("❌ Service account file not found")
        return False, None
    except Exception as e:
        print(f"❌ Error creating Google Sheets client: {e}")
        return False, None

def test_spreadsheet_access(client, sheet_id, sheet_name="Test Access"):
    """Test access to a specific spreadsheet."""
    print(f"\n🔍 Testing Spreadsheet Access...")
    print(f"   Sheet ID: {sheet_id}")
    
    try:
        spreadsheet = client.open_by_key(sheet_id)
        print(f"✅ Successfully opened spreadsheet: {spreadsheet.title}")
        
        # List all worksheets
        worksheets = spreadsheet.worksheets()
        print(f"   Available worksheets: {[ws.title for ws in worksheets]}")
        
        return True, spreadsheet
        
    except gspread.SpreadsheetNotFound:
        print(f"❌ Spreadsheet not found. Check if:")
        print(f"   1. Sheet ID is correct: {sheet_id}")
        print(f"   2. Service account has access to the sheet")
        return False, None
    except gspread.APIError as e:
        print(f"❌ Google Sheets API error: {e}")
        print("   This usually means:")
        print("   1. Google Sheets API is not enabled")
        print("   2. Service account doesn't have proper permissions")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error accessing spreadsheet: {e}")
        return False, None

def test_worksheet_access(spreadsheet, worksheet_name):
    """Test access to a specific worksheet."""
    print(f"\n🔍 Testing Worksheet Access...")
    print(f"   Worksheet: {worksheet_name}")
    
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
        print(f"✅ Successfully accessed worksheet: {worksheet.title}")
        
        # Try to read first row (headers)
        headers = worksheet.row_values(1)
        print(f"   Headers: {headers[:5]}{'...' if len(headers) > 5 else ''}")
        
        return True, worksheet
        
    except gspread.WorksheetNotFound:
        print(f"❌ Worksheet '{worksheet_name}' not found")
        print(f"   Available worksheets: {[ws.title for ws in spreadsheet.worksheets()]}")
        return False, None
    except Exception as e:
        print(f"❌ Error accessing worksheet: {e}")
        return False, None

def test_write_permission(worksheet):
    """Test write permissions to the worksheet."""
    print(f"\n🔍 Testing Write Permissions...")
    
    try:
        # Find an empty cell to test write
        test_cell = "Z1"  # Use a cell that's unlikely to be used
        test_value = f"Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Try to write
        worksheet.update(test_cell, test_value)
        print(f"✅ Successfully wrote test value to {test_cell}")
        
        # Try to read it back
        read_value = worksheet.acell(test_cell).value
        if read_value == test_value:
            print(f"✅ Successfully read back test value")
        else:
            print(f"⚠️  Read value doesn't match written value")
        
        # Clean up
        worksheet.update(test_cell, "")
        print(f"✅ Cleaned up test value")
        
        return True
        
    except gspread.APIError as e:
        print(f"❌ API error during write test: {e}")
        print("   This usually means the service account needs 'Editor' permissions")
        return False
    except Exception as e:
        print(f"❌ Error during write test: {e}")
        return False

def provide_setup_instructions(service_account_email, sheet_id):
    """Provide setup instructions based on test results."""
    print(f"\n📋 SETUP INSTRUCTIONS")
    print(f"=" * 50)
    
    print(f"\n1. 🔧 GOOGLE CLOUD CONSOLE SETUP:")
    print(f"   - Go to: https://console.cloud.google.com/")
    print(f"   - Enable these APIs:")
    print(f"     • Google Sheets API")
    print(f"     • Google Drive API (recommended)")
    
    print(f"\n2. 📊 GOOGLE SHEETS PERMISSIONS:")
    print(f"   - Open your Google Sheet: https://docs.google.com/spreadsheets/d/{sheet_id}")
    print(f"   - Click 'Share' button")
    print(f"   - Add this email with 'Editor' permissions:")
    print(f"     {service_account_email}")
    
    print(f"\n3. 📝 WORKSHEET SETUP:")
    print(f"   - Create a worksheet named: 'VideoAsk Responses'")
    print(f"   - Add these headers in row 1:")
    headers = ["Name", "DATE", "EMAIL", "LOCATION", 
               "🔗 Introduce Yourself", "📝 Introduce Yourself",
               "🔗 Foundation's Influence", "📝 Foundation's Influence",
               "🔗 Sharing Advice", "📝 Sharing Advice",
               "🔗 Purpose & Joy", "📝 Purpose & Joy",
               "🔗 Staying Connected", "📝 Staying Connected"]
    for i, header in enumerate(headers, 1):
        print(f"     Column {chr(64+i)}: {header}")

def main():
    """Run comprehensive Google Sheets credentials test."""
    print("🧪 GOOGLE SHEETS CREDENTIALS TEST")
    print("=" * 50)
    
    # Load environment variables
    sheet_id = os.getenv('GOOGLE_SHEET_ID', '1s6OxhfqfQfxHH4M4ln1C1hrN3DWM8HI_-QJlY_p-KRU')
    worksheet_name = os.getenv('GSHEET_WORKSHEET_NAME', 'TRANSCRIPT FINAL')
    videoask_sheet_id = os.getenv('VIDEOASK_GOOGLE_SHEET_ID', sheet_id)
    videoask_worksheet_name = os.getenv('VIDEOASK_GSHEET_WORKSHEET_NAME', 'VideoAsk Responses')
    service_account_email = os.getenv('GOOGLE_SERVICE_ACCOUNT_EMAIL', 'unknown')
    
    print(f"Configuration:")
    print(f"  Main Sheet ID: {sheet_id}")
    print(f"  Main Worksheet: {worksheet_name}")
    print(f"  VideoAsk Sheet ID: {videoask_sheet_id}")
    print(f"  VideoAsk Worksheet: {videoask_worksheet_name}")
    print(f"  Service Account: {service_account_email}")
    
    # Test 1: Service Account File
    service_account_result = test_service_account_file()
    if not service_account_result:
        return
    
    success, creds_data = service_account_result
    actual_service_account = creds_data.get('client_email', 'unknown')
    
    # Test 2: Google Sheets Client
    client_result = test_google_sheets_client()
    if not client_result[0]:
        provide_setup_instructions(actual_service_account, sheet_id)
        return
    
    success, client = client_result
    
    # Test 3: Main Spreadsheet Access
    main_sheet_result = test_spreadsheet_access(client, sheet_id)
    if main_sheet_result[0]:
        spreadsheet = main_sheet_result[1]
        
        # Test 4: Main Worksheet Access
        main_worksheet_result = test_worksheet_access(spreadsheet, worksheet_name)
        if main_worksheet_result[0]:
            worksheet = main_worksheet_result[1]
            
            # Test 5: Write Permissions
            test_write_permission(worksheet)
    
    # Test VideoAsk spreadsheet if different
    if videoask_sheet_id != sheet_id:
        print(f"\n" + "="*50)
        print("TESTING VIDEOASK SPREADSHEET")
        videoask_sheet_result = test_spreadsheet_access(client, videoask_sheet_id)
        if videoask_sheet_result[0]:
            videoask_spreadsheet = videoask_sheet_result[1]
            test_worksheet_access(videoask_spreadsheet, videoask_worksheet_name)
    else:
        # Test VideoAsk worksheet in same spreadsheet
        if main_sheet_result[0]:
            test_worksheet_access(main_sheet_result[1], videoask_worksheet_name)
    
    # Always provide instructions
    print(f"\n" + "="*50)
    provide_setup_instructions(actual_service_account, sheet_id)
    
    print(f"\n✅ Test completed! Check the results above.")

if __name__ == "__main__":
    main()
