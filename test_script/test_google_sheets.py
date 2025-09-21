#!/usr/bin/env python3
"""
Google Sheets Connection Test Script
Tests the connection to Google Sheets and validates the setup.
"""

import os
import sys
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def test_google_sheets_connection():
    """Test Google Sheets API connection and configuration."""
    
    print("🔍 Testing Google Sheets Connection...")
    print("=" * 50)
    
    # Check if credentials file exists
    creds_file = 'service-account.json'
    if not os.path.exists(creds_file):
        print(f"❌ Credentials file not found: {creds_file}")
        return False
    print(f"✅ Credentials file exists: {creds_file}")
    
    try:
        # Load credentials
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, SCOPES)
        print("✅ Credentials loaded successfully")
        
        # Authorize client
        client = gspread.authorize(creds)
        print("✅ Google Sheets client authorized")
        
        # Test sheet access
        sheet_id = os.getenv('GOOGLE_SHEET_ID', '1s6OxhfqfQfxHH4M4ln1C1hrN3DWM8HI_-QJlY_p-KRU')
        print(f"📊 Testing sheet access: {sheet_id}")
        
        spreadsheet = client.open_by_key(sheet_id)
        print(f"✅ Spreadsheet opened: '{spreadsheet.title}'")
        
        # List all worksheets
        worksheets = spreadsheet.worksheets()
        print(f"📄 Found {len(worksheets)} worksheets:")
        for i, ws in enumerate(worksheets, 1):
            print(f"   {i}. '{ws.title}' ({ws.row_count} rows, {ws.col_count} cols)")
        
        # Test VideoAsk worksheet
        videoask_sheet_name = os.getenv('VIDEOASK_GSHEET_WORKSHEET_NAME', 'VideoAsk Responses')
        print(f"\n🎥 Testing VideoAsk worksheet: '{videoask_sheet_name}'")
        
        try:
            videoask_ws = spreadsheet.worksheet(videoask_sheet_name)
            print(f"✅ VideoAsk worksheet found: '{videoask_ws.title}'")
            
            # Check headers
            try:
                headers = videoask_ws.row_values(1)
                if headers:
                    print(f"📋 Headers ({len(headers)} columns): {headers[:5]}...")
                else:
                    print("⚠️  No headers found in row 1")
            except Exception as e:
                print(f"⚠️  Could not read headers: {e}")
                
        except gspread.WorksheetNotFound:
            print(f"❌ VideoAsk worksheet '{videoask_sheet_name}' not found")
            print("📝 Available worksheets:")
            for ws in worksheets:
                print(f"   - '{ws.title}'")
            print(f"\n🔧 To fix: Create a worksheet named '{videoask_sheet_name}' in your spreadsheet")
            return False
        
        print("\n🎉 Google Sheets connection test PASSED!")
        return True
        
    except gspread.exceptions.APIError as e:
        print(f"❌ Google Sheets API Error: {e}")
        
        if 'PERMISSION_DENIED' in str(e):
            print("\n🔧 PERMISSION ISSUE:")
            print("   The service account doesn't have access to the spreadsheet.")
            print("   Solution:")
            print("   1. Open your Google Sheet")
            print("   2. Click 'Share'")
            print("   3. Add this email with 'Editor' access:")
            print("      transcript@transcript-460922.iam.gserviceaccount.com")
            
        elif 'API_NOT_ENABLED' in str(e):
            print("\n🔧 API NOT ENABLED:")
            print("   Google Sheets API is not enabled in Google Cloud Console.")
            print("   Solution:")
            print("   1. Go to Google Cloud Console")
            print("   2. Navigate to APIs & Services > Library")
            print("   3. Enable 'Google Sheets API'")
            
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        return False

def test_environment_variables():
    """Test environment variables."""
    print("\n🔍 Testing Environment Variables...")
    print("=" * 50)
    
    required_vars = [
        'GOOGLE_SHEET_ID',
        'GSHEET_WORKSHEET_NAME',
        'VIDEOASK_GOOGLE_SHEET_ID',
        'VIDEOASK_GSHEET_WORKSHEET_NAME',
        'GOOGLE_SERVICE_ACCOUNT_EMAIL'
    ]
    
    all_good = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            all_good = False
    
    return all_good

if __name__ == "__main__":
    print("🚀 Google Sheets Setup Validator")
    print("=" * 50)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded from .env")
    except ImportError:
        print("⚠️  python-dotenv not available, using system env vars")
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    # Test Google Sheets connection
    sheets_ok = test_google_sheets_connection()
    
    print("\n" + "=" * 50)
    if env_ok and sheets_ok:
        print("🎉 ALL TESTS PASSED! Google Sheets is ready to use.")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED! Please fix the issues above.")
        sys.exit(1)
