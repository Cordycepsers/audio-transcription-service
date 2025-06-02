#!/usr/bin/env python3

import sys
print(f"Python version: {sys.version}")

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import json
    import os
    
    print("Libraries imported successfully")
    
    # Get credentials
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name('service-account.json', scope)
        print("Credentials loaded successfully")
        
        # Create client
        client = gspread.authorize(creds)
        print("Client authorized")
        
        # Try to open spreadsheet
        spreadsheet = client.open_by_key('1s6OxhfqfQfxHH4M4ln1C1hrN3DWM8HI_-QJlY_p-KRU')
        print(f"Spreadsheet opened: {spreadsheet.title}")
    
    except Exception as e:
        print(f"Error accessing spreadsheet: {e}")
    
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")
